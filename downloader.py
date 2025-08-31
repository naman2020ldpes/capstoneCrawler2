# downloader.py
"""Multi-threaded file downloader with retry logic and duplicate checking."""

import asyncio
import aiohttp
import aiofiles
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Set, Optional
import time

from config import (
    DOWNLOADS_DIR, REQUEST_TIMEOUT, RETRY_ATTEMPTS, RETRY_BACKOFF,
    MAX_DOWNLOAD_THREADS, USER_AGENT, TOR_PROXY
)
from utils import setup_logging, extract_domain, extract_filename, sanitize_filename, exponential_backoff
from tracker import JSONTracker, KeyExtractor


class FileDownloader:
    """Handles multi-threaded file downloads with async coordination."""
    
    def __init__(self, tracker: JSONTracker, use_tor: bool = False):
        self.tracker = tracker
        self.use_tor = use_tor
        self.logger = setup_logging(__name__)
        self.key_extractor = KeyExtractor()
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def create_session(self) -> aiohttp.ClientSession:
        """Create aiohttp session with appropriate proxy settings."""
        connector = None
        
        if self.use_tor:
            try:
                import aiohttp_socks
                connector = aiohttp_socks.ProxyConnector.from_url('socks5://127.0.0.1:9050')
            except ImportError:
                self.logger.warning("aiohttp_socks not available, falling back to requests with Tor")
                connector = None
        
        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
        headers = {'User-Agent': USER_AGENT}
        
        return aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=headers
        )
    
    async def download_file_async(self, file_url: str, local_path: Path) -> bool:
        """Download a single file asynchronously."""
        if not self.session:
            self.session = await self.create_session()
        
        for attempt in range(RETRY_ATTEMPTS):
            try:
                async with self.session.get(file_url) as response:
                    if response.status == 200:
                        # Ensure directory exists
                        local_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        async with aiofiles.open(local_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                await f.write(chunk)
                        
                        self.logger.info(f"Downloaded: {local_path.name}")
                        return True
                    else:
                        self.logger.warning(f"HTTP {response.status} for {file_url}")
                        
            except Exception as e:
                self.logger.error(f"Download attempt {attempt + 1} failed for {file_url}: {e}")
                
                # Delete partial file if it exists
                if local_path.exists():
                    try:
                        local_path.unlink()
                    except Exception:
                        pass
                
                if attempt < RETRY_ATTEMPTS - 1:
                    await exponential_backoff(attempt, RETRY_BACKOFF)
        
        return False
    
    def download_file_sync(self, file_url: str, local_path: Path, use_tor: bool) -> bool:
        """Synchronous download function for ThreadPoolExecutor."""
        import requests
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        session = requests.Session()
        
        # Set up retry strategy
        retry_strategy = Retry(
            total=RETRY_ATTEMPTS,
            backoff_factor=RETRY_BACKOFF,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Configure Tor proxy if needed
        if use_tor:
            session.proxies = TOR_PROXY
        
        session.headers.update({'User-Agent': USER_AGENT})
        
        try:
            response = session.get(file_url, timeout=REQUEST_TIMEOUT, stream=True)
            response.raise_for_status()
            
            # Ensure directory exists
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self.logger.info(f"Downloaded: {local_path.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Sync download failed for {file_url}: {e}")
            
            # Delete partial file if it exists
            if local_path.exists():
                try:
                    local_path.unlink()
                except Exception:
                    pass
            
            return False
        finally:
            session.close()
    
    async def download_files(self, file_urls: Set[str], domain: str) -> tuple[int, int]:
      """
      Download multiple files using ThreadPoolExecutor.
      
      Returns:
          tuple: (downloaded_count, skipped_count)
      """
      if not file_urls:
          return 0, 0
      
      downloaded_count = 0
      skipped_count = 0
      
      # Get already downloaded filenames for this domain
      existing_filenames = self.tracker.get_downloaded_filenames(domain)
      
      # Prepare download tasks
      download_tasks = []
      for file_url in file_urls:
          filename = sanitize_filename(extract_filename(file_url))
          
          if filename in existing_filenames:
              self.logger.info(f"Skipping existing file: {filename}")
              skipped_count += 1
              continue
          
          local_path = DOWNLOADS_DIR / domain / filename
          download_tasks.append((file_url, local_path, filename))
      
      if not download_tasks:
          return downloaded_count, skipped_count
      
      # Execute downloads in thread pool
      loop = asyncio.get_event_loop()
      
      with ThreadPoolExecutor(max_workers=MAX_DOWNLOAD_THREADS) as executor:
          # Submit all download tasks
          futures = []
          for file_url, local_path, filename in download_tasks:
              future = loop.run_in_executor(
                  executor, 
                  self.download_file_sync, 
                  file_url, 
                  local_path, 
                  self.use_tor
              )
              futures.append((future, file_url, local_path, filename))
          
          # Wait for all downloads to complete and process results
          for future, file_url, local_path, filename in futures:
              try:
                  success = await future
                  
                  if success:
                      downloaded_count += 1
                      
                      # Add to tracker
                      await self.tracker.add_download_entry(
                          domain, file_url, str(local_path), filename
                      )
                      
                      # Extract keys from downloaded file
                      keys = self.key_extractor.extract_from_file(local_path)
                      if keys:
                          await self.tracker.add_keys(domain, keys)
                          self.logger.info(f"Found {len(keys)} keys in {filename}")
                  
              except Exception as e:
                  self.logger.error(f"Download task failed for {file_url}: {e}")
      
      return downloaded_count, skipped_count  
    
    async def close(self) -> None:
        """Close the aiohttp session."""
        if self.session:
            await self.session.close()