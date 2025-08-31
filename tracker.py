# tracker.py
"""JSON file management and key extraction functionality."""

import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Optional

from utils import setup_logging, extract_keys_from_text

logger = setup_logging(__name__)


class JSONTracker:
    """Manages the downloads.json file and key extraction."""
    
    def __init__(self, json_file: Path):
        self.json_file = json_file
        self.data: Dict = {}
    
    async def load_data(self) -> None:
        """Load existing data from JSON file."""
        try:
            if self.json_file.exists():
                with open(self.json_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.data = json.loads(content) if content.strip() else {}
            else:
                self.data = {}
            logger.info(f"Loaded tracking data with {len(self.data)} domains")
        except Exception as e:
            logger.error(f"Error loading JSON data: {e}")
            self.data = {}
    
    def save_data(self) -> None:
        """Save current data to JSON file."""
        try:
            # Ensure parent directory exists
            self.json_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.json_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            logger.debug("Saved tracking data to JSON file")
        except Exception as e:
            logger.error(f"Error saving JSON data: {e}")
    
    def get_downloaded_filenames(self, domain: str) -> Set[str]:
        """Get set of already downloaded filenames for a domain."""
        if domain not in self.data:
            return set()
        
        downloaded_filenames = set()
        
        # Handle both list format and other formats
        domain_data = self.data[domain]
        
        if isinstance(domain_data, list):
            for entry in domain_data:
                if isinstance(entry, dict) and 'filename' in entry:
                    downloaded_filenames.add(entry['filename'])
        
        return downloaded_filenames
    
    async def add_download_entry(self, domain: str, file_url: str, local_path: str, filename: str) -> None:
        """Add a new download entry to the tracking data."""
        try:
            if domain not in self.data:
                self.data[domain] = []
            
            # Ensure we have a list for this domain
            if not isinstance(self.data[domain], list):
                self.data[domain] = []
            
            entry = {
                'file_url': file_url,
                'local_path': local_path,
                'filename': filename,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
            
            self.data[domain].append(entry)
            logger.info(f"Added download entry for {filename} from {domain}")
            
            # Save synchronously to avoid async issues
            self.save_data()
        except Exception as e:
            logger.error(f"Error adding download entry: {e}")
    
    async def add_keys(self, domain: str, keys: List[dict]) -> None:
        """Add extracted keys for a domain."""
        if not keys:
            return
            
        try:
            if domain not in self.data:
                self.data[domain] = []
            
            # Initialize keys_found if it doesn't exist
            keys_found_exists = False
            for item in self.data[domain]:
                if isinstance(item, dict) and 'keys_found' in item:
                    keys_found_exists = True
                    # Add new keys to existing ones, avoiding duplicates
                    existing_keys = item['keys_found']
                    for key in keys:
                        if key not in existing_keys:
                            existing_keys.append(key)
                    break
            
            if not keys_found_exists:
                # Add a keys_found entry
                self.data[domain].append({'keys_found': keys})
            
            # Save synchronously
            self.save_data()
            logger.info(f"Added {len(keys)} keys for {domain}")
        except Exception as e:
            logger.error(f"Error adding keys: {e}")
    
    def get_stats(self) -> Dict[str, int]:
        """Get statistics about tracked data."""
        total_files = 0
        total_keys = 0
        
        for domain_data in self.data.values():
            if isinstance(domain_data, list):
                for entry in domain_data:
                    if isinstance(entry, dict):
                        if 'filename' in entry:
                            total_files += 1
                        elif 'keys_found' in entry:
                            total_keys += len(entry['keys_found'])
        
        return {
            'domains': len(self.data),
            'files': total_files,
            'keys': total_keys
        }


class KeyExtractor:
    """Handles key/password extraction from various content types."""
    
    def __init__(self):
        self.logger = setup_logging(__name__)
    
    def extract_from_html(self, html_content: str) -> List[dict]:
        """Extract keys from HTML content."""
        return extract_keys_from_text(html_content)
    
    def extract_from_file(self, file_path: Path) -> List[dict]:
        """Extract keys from downloaded files."""
        try:
            if file_path.suffix.lower() in ['.txt', '.csv', '.json']:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                return extract_keys_from_text(content)
            
            elif file_path.suffix.lower() in ['.pdf']:
                # For PDF files, we'd need additional libraries like PyPDF2
                # For now, return empty list
                self.logger.info(f"PDF key extraction not implemented for {file_path}")
                return []
            
            elif file_path.suffix.lower() in ['.docx']:
                # For DOCX files, we'd need python-docx library
                # For now, return empty list
                self.logger.info(f"DOCX key extraction not implemented for {file_path}")
                return []
            
            else:
                # For other file types, try to read as text
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read(10000)  # Read first 10KB only
                    return extract_keys_from_text(content)
                except Exception:
                    return []
                    
        except Exception as e:
            self.logger.error(f"Error extracting keys from {file_path}: {e}")
            return []