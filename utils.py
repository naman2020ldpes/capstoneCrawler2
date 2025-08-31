# utils.py
"""Utility functions for logging, cleanup, and helper operations."""

import logging
import shutil
import asyncio
from pathlib import Path
from urllib.parse import urlparse, urljoin
from typing import Set, List
import re
import os

from config import LOG_FORMAT, LOG_LEVEL, DOWNLOADS_DIR, SUPPORTED_EXTENSIONS, KEY_PATTERNS


def setup_logging(name: str) -> logging.Logger:
    """Set up logging configuration."""
    logging.basicConfig(
        format=LOG_FORMAT,
        level=getattr(logging, LOG_LEVEL),
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('crawler.log')
        ]
    )
    return logging.getLogger(name)


def delete_downloads(confirm: bool = True) -> bool:
    """
    Delete the entire downloads folder.
    
    Args:
        confirm: If True, ask for user confirmation before deleting
        
    Returns:
        bool: True if deleted, False if cancelled
    """
    if not DOWNLOADS_DIR.exists():
        print("Downloads folder doesn't exist.")
        return True
        
    if confirm:
        response = input(f"Are you sure you want to delete '{DOWNLOADS_DIR}' and all its contents? (y/N): ")
        if response.lower() != 'y':
            print("Deletion cancelled.")
            return False
    
    try:
        shutil.rmtree(DOWNLOADS_DIR)
        print(f"Successfully deleted {DOWNLOADS_DIR}")
        return True
    except Exception as e:
        print(f"Error deleting downloads folder: {e}")
        return False


def extract_domain(url: str) -> str:
    """Extract domain from URL and sanitize for folder names."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Handle localhost with ports
        if ':' in domain:
            domain = domain.replace(':', '_')
        
        # Sanitize domain for use as folder name
        domain = sanitize_domain(domain)
        
        return domain if domain else "unknown"
    except Exception:
        return "unknown"


def sanitize_domain(domain: str) -> str:
    """Sanitize domain name for use as folder name."""
    # Replace problematic characters for Windows/cross-platform compatibility
    problematic_chars = '<>:"/\\|?*'
    for char in problematic_chars:
        domain = domain.replace(char, '_')
    
    # Remove leading/trailing dots and spaces
    domain = domain.strip('. ')
    
    return domain if domain else "unknown"


def is_supported_file(url: str) -> bool:
    """Check if URL points to a supported file type."""
    try:
        path = urlparse(url).path.lower()
        return any(path.endswith(ext) for ext in SUPPORTED_EXTENSIONS)
    except Exception:
        return False


def extract_filename(url: str) -> str:
    """Extract filename from URL."""
    try:
        path = urlparse(url).path
        filename = Path(path).name
        if not filename or '.' not in filename:
            # Generate a filename based on URL hash
            import hashlib
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            return f"file_{url_hash}.unknown"
        return filename
    except Exception:
        import hashlib
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        return f"file_{url_hash}.unknown"


def find_file_links(html_content: str, base_url: str) -> Set[str]:
    """Extract file links from HTML content."""
    file_links = set()
    
    # Pattern to find links in href and src attributes
    link_patterns = [
        r'href=["\']([^"\']+)["\']',
        r'src=["\']([^"\']+)["\']',
        r'download=["\']([^"\']+)["\']',
    ]
    
    for pattern in link_patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        for match in matches:
            try:
                # Skip local file paths (Windows/Unix paths)
                if (match.startswith('C:') or match.startswith('/') or 
                    match.startswith('\\') or ':\\' in match):
                    continue
                
                # Skip javascript, mailto, tel links
                if any(match.lower().startswith(proto) for proto in ['javascript:', 'mailto:', 'tel:']):
                    continue
                
                absolute_url = urljoin(base_url, match)
                
                # Validate it's a proper URL
                parsed = urlparse(absolute_url)
                if not parsed.scheme or not parsed.netloc:
                    continue
                
                if is_supported_file(absolute_url):
                    file_links.add(absolute_url)
            except Exception:
                continue
    
    return file_links


def find_page_links(html_content: str, base_url: str, current_domain: str) -> Set[str]:
    """Extract page links from HTML content (same domain only)."""
    page_links = set()
    
    # Pattern to find links in href attributes
    href_pattern = r'href=["\']([^"\']+)["\']'
    matches = re.findall(href_pattern, html_content, re.IGNORECASE)
    
    for match in matches:
        try:
            absolute_url = urljoin(base_url, match)
            url_domain = extract_domain(absolute_url)
            
            # Only include links from the same domain and not file links
            if url_domain == current_domain and not is_supported_file(absolute_url):
                # Clean up the URL (remove fragments)
                clean_url = absolute_url.split('#')[0]
                page_links.add(clean_url)
        except Exception:
            continue
    
    return page_links


def extract_keys_from_text(text: str) -> List[dict]:
    """
    Extract keys/passwords from text using regex patterns.
    
    Args:
        text: Text content to search
        
    Returns:
        List of dictionaries with key type and value
    """
    found_keys = []
    
    for pattern in KEY_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            key_type = match.group(0).split(':')[0].split('=')[0].strip().lower()
            key_value = match.group(1)
            
            # Skip common false positives
            if len(key_value) < 3 or key_value.lower() in ['none', 'null', '""', "''"]:
                continue
                
            found_keys.append({
                'type': key_type,
                'value': key_value
            })
    
    return found_keys


async def exponential_backoff(attempt: int, base_delay: float = 1.0) -> None:
    """Implement exponential backoff for retries."""
    delay = base_delay * (2 ** attempt)
    await asyncio.sleep(delay)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for cross-platform compatibility."""
    # Remove or replace problematic characters
    problematic_chars = '<>:"/\\|?*'
    for char in problematic_chars:
        filename = filename.replace(char, '_')
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:250] + ext
    
    return filename