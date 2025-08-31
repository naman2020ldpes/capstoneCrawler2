# config.py
"""Configuration settings for the advanced web crawler."""

import os
from pathlib import Path

# Directory settings
BASE_DIR = Path(__file__).parent
DOWNLOADS_DIR = BASE_DIR / "downloads"
JSON_FILE = BASE_DIR / "downloads.json"

# Supported file extensions
SUPPORTED_EXTENSIONS = {
    '.csv', '.txt', '.json', '.xlsx', '.xls', 
    '.zip', '.rar', '.pdf', '.docx'
}

# Tor proxy settings
TOR_PROXY = {
    'http': 'socks5://127.0.0.1:9050',
    'https': 'socks5://127.0.0.1:9050'
}

# Request settings
REQUEST_TIMEOUT = 30
RETRY_ATTEMPTS = 3
RETRY_BACKOFF = 2  # seconds

# Crawler limits
MAX_PAGES_PER_DOMAIN = 100
MAX_CONCURRENT_REQUESTS = 10
MAX_DOWNLOAD_THREADS = 5

# Key extraction patterns
KEY_PATTERNS = [
    r'password\s*[:=]\s*([^\s\'"<>]+)',
    r'key\s*[:=]\s*([^\s\'"<>]+)',
    r'passkey\s*[:=]\s*([^\s\'"<>]+)',
    r'passwd\s*[:=]\s*([^\s\'"<>]+)',
    r'pwd\s*[:=]\s*([^\s\'"<>]+)',
    r'secret\s*[:=]\s*([^\s\'"<>]+)',
    r'token\s*[:=]\s*([^\s\'"<>]+)',
]

# Logging configuration
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = 'INFO'

# User agent
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'