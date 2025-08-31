# Advanced Python Web Crawler (Python 3.11+)

## **Overview**
This is a **production-grade** Python 3.11+ web crawler designed for **high-performance crawling** of both **normal web** and **dark web (.onion)** sites.  
The crawler can:
- Crawl and scrape websites
- Find and **download various file types**
- **Scan content** for keys/passwords
- Store **all metadata in a JSON file** instead of a database

---

## **Project Structure**
```
project/
├── main.py                 # Main entry point
├── config.py              # Configuration settings
├── crawler.py             # Main async crawler class
├── downloader.py          # Multi-threaded file downloader
├── tracker.py             # JSON file management + key extraction
├── utils.py               # Utility functions (logging, cleanup, helpers)
├── debug_crawler.py       # Debug script for troubleshooting
├── test_basic.py          # Basic file system test
├── urls.json              # Input file with URLs to crawl (created if missing)
├── crawler.log            # Log file (auto-generated)
├── downloads.json         # Tracking data (auto-generated)
├── downloads/             # Directory for downloaded files (auto-created)
└── user_json.json         # Example JSON file for testing
```

---

## **File Purposes**

### **1. `main.py`**
**Purpose:** Main entry point that orchestrates the entire crawling process.

**Key Functions:**
- `main()` → Orchestrates the crawling process
- `load_urls_from_file()` → Loads URLs from a JSON file
- `create_example_urls_file()` → Creates an example `urls.json` file if none exists

---

### **2. `config.py`**
**Purpose:** Centralizes all configuration settings for the crawler.

**Key Settings:**
- Directory paths
- Supported file extensions
- Tor proxy settings
- Request timeout & retry settings
- Crawler limits
- Key extraction patterns
- Logging configuration
- User agent string

---

### **3. `crawler.py`**
**Purpose:** Core async web crawler implementation.

**Key Classes/Functions:**
- `AsyncWebCrawler` → Main crawler class
- `create_session()` → Creates aiohttp session with proxy settings
- `fetch_page()` → Fetches a single page with retry logic
- `crawl_site()` → Crawls a single website
- `crawl_multiple_sites()` → Crawls multiple websites concurrently

---

### **4. `downloader.py`**
**Purpose:** Handles multi-threaded file downloads.

**Key Classes/Functions:**
- `FileDownloader` → Main downloader class
- `download_file_async()` → Downloads a single file asynchronously
- `download_file_sync()` → Synchronous download via `ThreadPoolExecutor`
- `download_files()` → Downloads multiple files in parallel

---

### **5. `tracker.py`**
**Purpose:** Manages the JSON tracking file and key extraction.

**Key Classes/Functions:**
- `JSONTracker` → Manages `downloads.json`
- `load_data()` → Loads existing data from JSON
- `save_data()` → Saves updated data
- `add_download_entry()` → Adds a new download record
- `add_keys()` → Adds extracted keys for a domain
- `KeyExtractor` → Handles key/password extraction using regex

---

### **6. `utils.py`**
**Purpose:** Utility functions for various operations.

**Key Functions:**
- `setup_logging()` → Configures logging
- `delete_downloads()` → Deletes the downloads folder
- `extract_domain()` → Extracts domain from a URL
- `find_file_links()` → Extracts file links from HTML content
- `extract_keys_from_text()` → Extracts keys/passwords from text
- `sanitize_filename()` → Ensures safe filenames

---

### **7. `debug_crawler.py`**
**Purpose:** Debug script to troubleshoot crawler issues.

---

### **8. `test_basic.py`**
**Purpose:** Basic test to check file system operations.

---

## **Workflow (main.py)**

1. **Initialization** → Load configuration & set up logging  
2. **URL Loading** → Read URLs from `urls.json`  
3. **Component Setup** → Initialize **tracker, crawler, and downloader**  
4. **Crawling**  
   - Crawl sites asynchronously  
   - Extract page links & file links  
   - Download supported files in parallel  
   - Extract keys from **pages** and **files**  
5. **Tracking** → Save metadata in `downloads.json`  
6. **Reporting** → Display crawl statistics

---

## **How to Run**

### **Step 1 — Install Dependencies**
```bash
pip install aiohttp aiofiles requests aiohttp_socks
```

### **Step 2 — Create/Edit `urls.json`**
```json
{
  "urls": [
    "https://example.com",
    "https://another-site.com"
  ]
}
```

### **Step 3 — Run the Crawler**
```bash
python main.py
```

---

## **Running with Tor**

For **dark web (.onion)** sites:

1. Install and start the **Tor service**
2. Use the `--tor` flag:
```bash
python main.py --tor
```

---

## **Running Periodically**

### **On Linux/macOS — Using `cron`**
Edit crontab:
```bash
crontab -e
```
Add a job to run daily at **2 AM**:
```text
0 2 * * * cd /path/to/crawler && python main.py >> crawler.log 2>&1
```

---

### **On Windows — Using Task Scheduler**
1. Open **Task Scheduler**
2. Create a **new task**
3. Set the trigger to **daily** at your preferred time
4. Set the action:
   ```
   Program: python.exe
   Arguments: C:\path\to\crawler\main.py
   ```
5. Set **working directory** to the crawler folder

---

### **Using a Python Scheduler**
```python
import schedule
import time
import asyncio
from main import main

def run_crawler():
    asyncio.run(main("urls.json", False))

# Schedule daily at 2 AM
schedule.every().day.at("02:00").do(run_crawler)

while True:
    schedule.run_pending()
    time.sleep(60)
```

---

## **Key Libraries & Their Purposes**
| Library          | Purpose                                   |
|------------------|------------------------------------------|
| **aiohttp**      | Async HTTP client/server (web requests) |
| **aiofiles**     | Async file I/O operations               |
| **requests**     | Synchronous fallback for file downloads |
| **aiohttp_socks**| SOCKS proxy connector (Tor support)     |
| **asyncio**      | Core async I/O framework                |
| **concurrent.futures** | Multi-threaded downloads          |

---

## **Important Features**
- ⚡ **Async Crawling** → High-performance concurrent fetching  
- 🧵 **Multi-threaded Downloads** → Parallel file downloads  
- 🕵 **Tor Support** → Crawl dark web `.onion` sites  
- 🔄 **Duplicate Prevention** → Avoids re-downloading existing files  
- 🔑 **Key Extraction** → Finds passwords, API keys, tokens, etc.  
- 🛠 **Robust Error Handling** → Retries + fallback mechanisms  
- 📂 **Structured Storage** → Organizes downloads by domain  
- 📝 **Detailed Logging** → For monitoring & debugging

---

## **Error Handling**
The crawler handles:
- Connection timeouts
- HTTP errors (403, 404, 500, etc.)
- Invalid URLs
- Tor connection failures
- File I/O issues
- JSON parsing errors

---

## **Performance Considerations**
- **Concurrency Limits** → Prevents server overload  
- **Exponential Backoff** → Retries failed requests with delays  
- **Memory Management** → Streams large file downloads  
- **Timeout Handling** → Avoids hanging on slow responses

---









Overview
This is a production-grade Python 3.11+ web crawler designed for high-performance crawling of both normal web and dark web (.onion) sites. The crawler can find and download various file types, scan content for keys/passwords, and store all metadata in a JSON file instead of a database.

Project Structure
text
project/
├── main.py                 # Main entry point
├── config.py              # Configuration settings
├── crawler.py             # Main async crawler class
├── downloader.py          # Multi-threaded file downloader
├── tracker.py             # JSON file management + key extraction
├── utils.py               # Utility functions (logging, cleanup, helpers)
├── debug_crawler.py       # Debug script for troubleshooting
├── test_basic.py          # Basic file system test
├── urls.json              # Input file with URLs to crawl (created if missing)
├── crawler.log            # Log file (auto-generated)
├── downloads.json         # Tracking data (auto-generated)
├── downloads/             # Directory for downloaded files (auto-created)
└── user_json.json         # Example JSON file for testing
File Purposes
1. main.py
Purpose: Main entry point that orchestrates the entire crawling process.

Key Functions:

main(): Orchestrates the crawling process

load_urls_from_file(): Loads URLs from a JSON file

create_example_urls_file(): Creates an example URLs file if none exists

2. config.py
Purpose: Centralizes all configuration settings for the crawler.

Key Settings:

Directory paths

Supported file extensions

Tor proxy settings

Request timeout and retry settings

Crawler limits

Key extraction patterns

Logging configuration

User agent string

3. crawler.py
Purpose: Core async web crawler implementation.

Key Classes/Functions:

AsyncWebCrawler: Main crawler class

create_session(): Creates aiohttp session with proxy settings

fetch_page(): Fetches a single web page with retry logic

crawl_site(): Crawls a single website

crawl_multiple_sites(): Crawls multiple websites concurrently

4. downloader.py
Purpose: Handles multi-threaded file downloads.

Key Classes/Functions:

FileDownloader: Main downloader class

download_file_async(): Downloads a single file asynchronously

download_file_sync(): Synchronous download function for ThreadPoolExecutor

download_files(): Downloads multiple files using ThreadPoolExecutor

5. tracker.py
Purpose: Manages the JSON tracking file and key extraction.

Key Classes/Functions:

JSONTracker: Manages the downloads.json file

load_data(): Loads existing data from JSON file

save_data(): Saves current data to JSON file

add_download_entry(): Adds a new download entry

add_keys(): Adds extracted keys for a domain

KeyExtractor: Handles key/password extraction from various content types

6. utils.py
Purpose: Utility functions for various operations.

Key Functions:

setup_logging(): Sets up logging configuration

delete_downloads(): Deletes the entire downloads folder

extract_domain(): Extracts domain from URL

find_file_links(): Extracts file links from HTML content

extract_keys_from_text(): Extracts keys/passwords from text

sanitize_filename(): Sanitizes filename for cross-platform compatibility

7. debug_crawler.py
Purpose: Debug script to identify where the crawler gets stuck.

8. test_basic.py
Purpose: Basic test to check file system operations.

Workflow (main.py)
Initialization: Load configuration and set up logging

URL Loading: Read URLs from a JSON file (urls.json)

Component Setup: Initialize tracker, crawler, and downloader

Crawling:

For each URL, crawl the site asynchronously

Extract file links and page links

Download supported files using multi-threaded approach

Extract keys from both pages and downloaded files

Tracking: Store all metadata in downloads.json

Reporting: Print statistics about the crawl operation

How to Run
Initial Setup
Install required libraries:

bash
pip install aiohttp aiofiles requests aiohttp_socks
Create/edit urls.json with the sites you want to crawl:

json
{
  "urls": [
    "https://example.com",
    "https://another-site.com"
  ]
}
Run the crawler:

bash
python main.py
Running with Tor
For dark web sites (.onion), you need to:

Install and run Tor service

Use the --tor flag:

bash
python main.py --tor
Running Periodically
On Linux/macOS (using cron)
Edit crontab:

bash
crontab -e
Add a line to run the crawler daily at 2 AM:

text
0 2 * * * cd /path/to/crawler && python main.py >> crawler.log 2>&1
On Windows (using Task Scheduler)
Open Task Scheduler

Create a new task

Set trigger to daily at desired time

Set action to run: python.exe C:\path\to\crawler\main.py

Set working directory to the crawler directory

Using a Python Scheduler
Create a scheduler script:

python
import schedule
import time
import asyncio
from main import main

def run_crawler():
    asyncio.run(main("urls.json", False))

# Schedule daily at 2 AM
schedule.every().day.at("02:00").do(run_crawler)

while True:
    schedule.run_pending()
    time.sleep(60)
Key Libraries and Their Purposes
aiohttp: Async HTTP client/server for asyncio (web requests)

aiofiles: Async file I/O for asyncio applications (file operations)

requests: Synchronous HTTP library (fallback for file downloads)

aiohttp_socks: SOCKS proxy connector for aiohttp (Tor support)

asyncio: Async I/O framework (core async functionality)

concurrent.futures: Thread pool execution (multi-threaded downloads)

Important Features
Async Crawling: Uses asyncio for high-performance concurrent page fetching

Multi-threaded Downloads: Uses ThreadPoolExecutor for parallel file downloads

Tor Support: Can route requests through Tor for dark web access

Duplicate Prevention: Checks JSON tracking file before downloading files

Key Extraction: Scans both pages and files for passwords/keys using regex

Error Handling: Comprehensive error handling with retry logic

Structured Storage: Organizes downloads by domain in a clear folder structure

Logging: Detailed logging for monitoring and debugging

Error Handling
The crawler includes robust error handling for:

Connection timeouts

HTTP errors (403, 404, 500, etc.)

Invalid URLs

Tor connection failures

File I/O errors

JSON parsing errors

Performance Considerations
Concurrency Limits: Configurable limits prevent overloading servers

Exponential Backoff: Retry failed requests with increasing delays

Memory Management: Streams large file downloads to avoid memory issues

Timeout Handling: Prevents hanging on slow responses