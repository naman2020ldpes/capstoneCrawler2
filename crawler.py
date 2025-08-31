# crawler.py
"""Main async web crawler for normal and dark web sites."""

import asyncio
import aiohttp
from urllib.parse import urljoin, urlparse
from typing import Set, List, Optional
import time
from pathlib import Path

from config import (
    REQUEST_TIMEOUT, RETRY_ATTEMPTS, MAX_PAGES_PER_DOMAIN,
    MAX_CONCURRENT_REQUESTS, USER_AGENT, TOR_PROXY
)
from utils import (
    setup_logging, extract_domain, find_file_links, find_page_links,
    exponential_backoff, extract_keys_from_text
)
from tracker import JSONTracker
from downloader import FileDownloader


class AsyncWebCrawler:
    """High-performance async web crawler with Tor support."""
    
    def __init__(self, use_tor: bool = False):
        self.use_tor = use_tor
        self.logger = setup_logging(__name__)
        self.session: Optional[aiohttp.ClientSession] = None
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        
        # Statistics
        self.stats = {
            'pages_visited': 0,
            'files_downloaded': 0,
            'files_skipped': 0,
            'keys_found': 0
        }
    
    async def create_session(self) -> aiohttp.ClientSession:
        """Create aiohttp session with appropriate proxy settings."""
        connector = None
        
        if self.use_tor:
            try:
                import aiohttp_socks
                connector = aiohttp_socks.ProxyConnector.from_url('socks5://127.0.0.1:9050')
                self.logger.info("Using Tor proxy for requests")
            except ImportError:
                self.logger.error("aiohttp_socks not installed. Install with: pip install aiohttp_socks")
                raise
        
        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
        headers = {'User-Agent': USER_AGENT}
        
        return aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=headers
        )
    
    async def fetch_page(self, url: str) -> Optional[str]:
      """Fetch a single web page with retry logic."""
      if not self.session:
          self.session = await self.create_session()
      
      async with self.semaphore:
          for attempt in range(RETRY_ATTEMPTS):
              try:
                  # Add timeout to prevent hanging
                  async with self.session.get(url, timeout=REQUEST_TIMEOUT) as response:
                      if response.status == 200:
                          content = await response.text()
                          self.logger.debug(f"Fetched: {url}")
                          return content
                      else:
                          self.logger.warning(f"HTTP {response.status} for {url}")
                          
              except asyncio.TimeoutError:
                  self.logger.warning(f"Timeout for {url} (attempt {attempt + 1})")
              except Exception as e:
                  self.logger.error(f"Error fetching {url} (attempt {attempt + 1}): {e}")
              
              if attempt < RETRY_ATTEMPTS - 1:
                  await exponential_backoff(attempt)
          
          return None 
    
    async def crawl_site(self, start_url: str, tracker: JSONTracker, downloader: FileDownloader) -> dict:
      """
      Crawl a single website starting from the given URL.
      
      Returns:
          dict: Statistics for this site
      """
      # Initialize site stats with default values
      site_stats = {
          'pages_visited': 0,
          'files_downloaded': 0,
          'files_skipped': 0,
          'keys_found': 0
      }
      
      try:
          domain = extract_domain(start_url)
          self.logger.info(f"Starting crawl of {domain}")
          
          visited_urls: Set[str] = set()
          urls_to_visit: Set[str] = {start_url}
          all_file_urls: Set[str] = set()
          all_keys: List[dict] = []
          
          while urls_to_visit and site_stats['pages_visited'] < MAX_PAGES_PER_DOMAIN:
              # Process URLs in batches
              current_batch = list(urls_to_visit)[:MAX_CONCURRENT_REQUESTS]
              urls_to_visit -= set(current_batch)
              
              # Fetch pages concurrently
              tasks = [self.fetch_page(url) for url in current_batch]
              results = await asyncio.gather(*tasks, return_exceptions=True)
              
              for url, result in zip(current_batch, results):
                  if url in visited_urls:
                      continue
                  
                  visited_urls.add(url)
                  site_stats['pages_visited'] += 1
                  
                  if isinstance(result, str):  # Successful fetch
                      self.logger.info(f"Crawled page {site_stats['pages_visited']}: {url}")
                      
                      # Extract file links
                      file_links = find_file_links(result, url)
                      all_file_urls.update(file_links)
                      
                      # Extract page links for further crawling
                      if site_stats['pages_visited'] < MAX_PAGES_PER_DOMAIN:
                          page_links = find_page_links(result, url, domain)
                          new_links = page_links - visited_urls - urls_to_visit
                          urls_to_visit.update(new_links)
                      
                      # Extract keys from page content
                      page_keys = extract_keys_from_text(result)
                      all_keys.extend(page_keys)
                      
                  elif isinstance(result, Exception):
                      self.logger.error(f"Failed to fetch {url}: {result}")
          
          # Download all found files
          self.logger.info(f"Found {len(all_file_urls)} files to download from {domain}")
          downloaded, skipped = await downloader.download_files(all_file_urls, domain)
          
          site_stats['files_downloaded'] = downloaded
          site_stats['files_skipped'] = skipped
          
          # Store keys found on pages
          if all_keys:
              await tracker.add_keys(domain, all_keys)
              site_stats['keys_found'] = len(all_keys)
              self.logger.info(f"Found {len(all_keys)} keys on pages from {domain}")
          
      except Exception as e:
          self.logger.error(f"Error in crawl_site for {start_url}: {e}")
      
      # IMPORTANT: This must be at the end
      return site_stats 
    
    
    async def crawl_multiple_sites(self, urls: List[str], tracker: JSONTracker) -> dict:
        """
        Crawl multiple websites concurrently.

        Args:
            urls: List of URLs to crawl
            tracker: JSONTracker instance

        Returns:
            dict: Overall statistics
        """
        self.logger.info(f"Starting crawl of {len(urls)} sites")

        # Initialize session and downloader
        self.session = await self.create_session()
        downloader = FileDownloader(tracker, self.use_tor)

        try:
            # Create tasks for each site
            tasks = []
            for url in urls:
                task = self.crawl_site(url, tracker, downloader)
                tasks.append(task)

            # Execute all crawls concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Aggregate statistics
            total_stats = {
                'pages_visited': 0,
                'files_downloaded': 0,
                'files_skipped': 0,
                'keys_found': 0
            }

            for i, result in enumerate(results):
                if isinstance(result, dict):  # Successful crawl
                    for key in total_stats:
                        total_stats[key] += result[key]
                    self.logger.info(f"Site {urls[i]} completed: {result}")
                elif isinstance(result, Exception):  # Error during crawl
                    self.logger.error(f"Error crawling {urls[i]}: {result}")
                else:  # Unexpected result (like None)
                    self.logger.warning(f"Unexpected result for {urls[i]}: {type(result)}")

            return total_stats

        finally:
            # Cleanup
            if self.session:
                await self.session.close()
            await downloader.close()
    
    async def close(self) -> None:
        """Close the crawler session."""
        if self.session:
            await self.session.close()