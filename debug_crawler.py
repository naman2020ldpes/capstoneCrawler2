#!/usr/bin/env python3
"""Debug script to identify where the crawler gets stuck."""

import asyncio
import time
import os
from pathlib import Path
from tracker import JSONTracker
from crawler import AsyncWebCrawler
from downloader import FileDownloader
from utils import setup_logging, extract_domain, find_file_links

async def debug_crawler():
    print("=== DEBUGGING CRAWLER ===")
    
    # Test URL
    test_url = "http://127.0.0.1:5500/demo.html"
    
    # Initialize components
    json_file = Path("debug_downloads.json")
    tracker = JSONTracker(json_file)
    await tracker.load_data()
    
    print(f"1. Tracker initialized, data: {tracker.data}")
    
    crawler = AsyncWebCrawler(use_tor=False)
    
    print("2. Testing fetch_page...")
    try:
        content = await crawler.fetch_page(test_url)
        if content:
            print("   ✅ fetch_page works")
            print(f"   Content length: {len(content)} characters")
        else:
            print("   ❌ fetch_page failed - no content")
            return
    except Exception as e:
        print(f"   ❌ fetch_page failed with error: {e}")
        return
    
    print("3. Testing file link extraction...")
    try:
        file_links = find_file_links(content, test_url)
        print(f"   Found {len(file_links)} file links: {list(file_links)}")
    except Exception as e:
        print(f"   ❌ File link extraction failed: {e}")
        return
    
    if not file_links:
        print("   ⚠️ No file links found, testing with manual URL")
        # Add a manual test URL
        file_links = {"http://127.0.0.1:5500/user_json.json"}
    
    print("4. Testing downloader...")
    try:
        downloader = FileDownloader(tracker, False)
        downloaded, skipped = await downloader.download_files(file_links, "127.0.0.1_5500")
        print(f"   Downloaded: {downloaded}, Skipped: {skipped}")
    except Exception as e:
        print(f"   ❌ Downloader failed: {e}")
        # Try to continue with other tests
    
    print("5. Testing tracker save...")
    try:
        # Call the synchronous save_data method directly (no await)
        tracker.save_data()
        if json_file.exists():
            print("   ✅ debug_downloads.json created successfully")
            try:
                with open(json_file, "r") as f:
                    content = f.read()
                    print(f"   Content: {content}")
            except Exception as e:
                print(f"   ⚠️ Could not read file: {e}")
        else:
            print("   ❌ debug_downloads.json not created")
            # Check directory permissions
            print(f"   Current working directory: {os.getcwd()}")
            print(f"   Write access: {os.access('.', os.W_OK)}")
    except Exception as e:
        print(f"   ❌ Tracker save failed: {e}")
    
    print("6. Testing directory structure...")
    try:
        downloads_dir = Path("downloads")
        if downloads_dir.exists():
            print(f"   ✅ Downloads directory exists: {downloads_dir.absolute()}")
            # List files in downloads directory
            for item in downloads_dir.rglob("*"):
                if item.is_file():
                    print(f"      Found file: {item.relative_to(downloads_dir)}")
        else:
            print("   ❌ Downloads directory does not exist")
    except Exception as e:
        print(f"   ❌ Directory check failed: {e}")
    
    print("7. Testing crawl_site with timeout...")
    try:
        # Use asyncio.wait_for to prevent hanging
        site_stats = await asyncio.wait_for(
            crawler.crawl_site(test_url, tracker, downloader),
            timeout=30  # 30 second timeout
        )
        print(f"   ✅ crawl_site completed: {site_stats}")
    except asyncio.TimeoutError:
        print("   ❌ crawl_site timed out after 30 seconds")
    except Exception as e:
        print(f"   ❌ crawl_site failed: {e}")
    
    # Cleanup
    try:
        await crawler.close()
        await downloader.close()
        print("   ✅ Cleanup completed")
    except Exception as e:
        print(f"   ⚠️ Cleanup failed: {e}")
    
    print("=== DEBUG COMPLETED ===")

if __name__ == "__main__":
    # Set up proper working directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    print(f"Working directory: {script_dir}")
    
    asyncio.run(debug_crawler())