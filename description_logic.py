# description_logic.py
"""mdues to handle file decryption after download using keys found during crawling.
also puts the loging info in the downloads.json (to records) and .."""

"""Methods:

decrypt_all_files: Loads downloads.json, iterates over each domain, extracts keys, and processes files for decryption.
_extract_domain_keys: Extracts all unique keys found for a domain, ensuring they are in the correct format (8 bytes for DES).
_process_domain_files: For each file in a domain, attempts decryption if keys are available, skips if already decrypted or file is missing.
_decrypt_with_domain_keys: Tries each key for a file until decryption succeeds or all keys fail. Only supports CSV files.
_save_updated_json: Saves the updated decryption status back to downloads.json.
decrypt_all_files (async function)"""

import asyncio # async file processings
import json
import logging #logg the historys
# import shutil
from pathlib import Path
from typing import Dict, List, Set
import sys

# Add the decryption module path to sys.path
from decription.decript import CSVEncryptor

# Set up logging
logger = logging.getLogger(__name__)

# Configuration
DOWNLOADS_DIR = Path("downloads")
JSON_FILE = Path("downloads.json")
DECRYPTED_SUBDIR = "decrypted"


class FileDecryptor:
    """Handles decryption of downloaded files using keys found during crawling."""

    def __init__(self):
        self.stats = {
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'no_keys_available': 0
        }
    
    async def decrypt_all_files(self) -> Dict[str, int]:
        """
        Decrypt all files recorded in downloads.json using domain-specific keys.
        
        Returns:
            Dict with decryption statistics
        """
        logger.info("Starting file decryption process using domain-specific keys")
        
        # Load tracking data
        try:
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Loaded tracking data with {len(data)} domains")
        except Exception as e:
            logger.error(f"Failed to load downloads.json: {e}")
            return self.stats
        
        # Process each domain separately
        for domain, entries in data.items():
            if isinstance(entries, list):
                # Extract keys found for this specific domain
                domain_keys = self._extract_domain_keys(entries)
                await self._process_domain_files(domain, entries, domain_keys)
        
        logger.info(
            f"Decryption process complete. "
            f"Success: {self.stats['success']}, "
            f"Failed: {self.stats['failed']}, "
            f"Skipped: {self.stats['skipped']}, "
            f"No keys available: {self.stats['no_keys_available']}"
        )
        
        return self.stats
    
    def _extract_domain_keys(self, entries: List[Dict]) -> Set[str]:
        """Extract all keys found for a specific domain."""
        domain_keys = set()
        
        for entry in entries:
            if isinstance(entry, dict) and 'keys_found' in entry:
                for key_info in entry['keys_found']:
                    if 'value' in key_info:
                        # Convert key to bytes (DES requires 8-byte key)
                        key_value = key_info['value']
                        try:
                            # Try to convert string key to bytes
                            if isinstance(key_value, str):
                                # Pad or truncate to 8 bytes for DES
                                key_bytes = key_value.encode('utf-8')[:8]
                                # Ensure exactly 8 bytes
                                key_bytes = key_bytes.ljust(8, b'\0')[:8]
                                domain_keys.add(key_bytes)
                        except Exception as e:
                            logger.warning(f"Could not convert key '{key_value}' to bytes: {e}")
        
        logger.info(f"Extracted {len(domain_keys)} unique keys for domain")
        return domain_keys
    
    async def _process_domain_files(self, domain: str, entries: List[Dict], domain_keys: Set[bytes]) -> None:
        """Process all files for a specific domain using its keys."""
        if not domain_keys:
            logger.warning(f"No keys available for domain: {domain}")
            self.stats['no_keys_available'] += len([e for e in entries if 'filename' in e])
            return
        
        for entry in entries:
            # Only process file entries (not key entries)
            if 'filename' in entry and 'local_path' in entry:
                file_path = Path(entry['local_path'])
                
                # Check if file exists
                if not file_path.exists():
                    logger.warning(f"File not found, skipping: {file_path}")
                    self.stats['skipped'] += 1
                    continue
                
                # Check if already decrypted
                if entry.get('decryption_status') == 'success':
                    logger.debug(f"Already decrypted, skipping: {file_path.name}")
                    self.stats['skipped'] += 1
                    continue
                
                # Try to decrypt the file with domain keys
                await self._decrypt_with_domain_keys(domain, entry, file_path, domain_keys)
    
    async def _decrypt_with_domain_keys(self, domain: str, entry: Dict, file_path: Path, domain_keys: Set[bytes]) -> None:
        """Try to decrypt a file using all available keys for its domain."""
        filename = entry['filename']
        logger.info(f"Attempting to decrypt {filename} with {len(domain_keys)} domain keys")
        
        successful_key = None
        decrypted_path = None
        
        # Try each key for this domain
        for key_bytes in domain_keys:
            try:
                encryptor = CSVEncryptor(key=key_bytes)
                
                # Create decrypted output directory
                decrypted_dir = file_path.parent / DECRYPTED_SUBDIR
                decrypted_dir.mkdir(exist_ok=True)
                
                # Set output path
                decrypted_path = decrypted_dir / filename
                
                # Try to decrypt based on file type
                success = False
                if file_path.suffix.lower() == '.csv':
                    success = encryptor.decrypt_csv(str(file_path), str(decrypted_path))
                else:
                    # For non-CSV files, we can't decrypt but we'll note this
                    logger.warning(
                        f"File format {file_path.suffix} not supported for decryption. "
                        f"Skipping file: {filename}"
                    )
                    self.stats['skipped'] += 1
                    return
                
                if success:
                    successful_key = key_bytes
                    break
                    
            except Exception as e:
                # This key didn't work, try the next one
                logger.debug(f"Key {key_bytes} failed for {filename}: {e}")
                continue
        
        # Update entry based on decryption result
        if successful_key:
            entry['decryption_status'] = 'success'
            entry['decrypted_path'] = str(decrypted_path)
            entry['decryption_key'] = successful_key.decode('utf-8', errors='ignore')  # Store which key worked
            self.stats['success'] += 1
            logger.info(f"Successfully decrypted {filename} with domain key")
        else:
            entry['decryption_status'] = 'failed'
            self.stats['failed'] += 1
            logger.warning(f"All domain keys failed for: {filename}")
        
        # Save the updated JSON
        self._save_updated_json()
    
    def _save_updated_json(self) -> None:
        """Save the updated JSON data with decryption status."""
        try:
            # Reload the current data to avoid overwriting
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Save the updated data
            with open(JSON_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Failed to update downloads.json: {e}")


async def decrypt_all_files() -> Dict[str, int]:
    """
    Main function to decrypt all files using domain-specific keys.
    
    Returns:
        Dictionary with decryption statistics
    """
    decryptor = FileDecryptor()
    return await decryptor.decrypt_all_files()


# For testing without the main crawler
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    async def test_decryption():
        stats = await decrypt_all_files()
        print(f"Decryption results: {stats}")
    
    asyncio.run(test_decryption())