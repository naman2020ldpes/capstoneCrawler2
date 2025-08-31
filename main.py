# main.py
"""Main entry point for the advanced web crawler."""

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import List, Dict

from config import JSON_FILE
from utils import setup_logging
from tracker import JSONTracker
from crawler import AsyncWebCrawler


async def load_urls_from_file(urls_file: str) -> List[str]:
    """Load URLs from a JSON file."""
    try:
        with open(urls_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different JSON structures
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'urls' in data:
            return data['urls']
        else:
            raise ValueError("JSON file must contain a list of URLs or an object with 'urls' key")
            
    except Exception as e:
        print(f"Error loading URLs from {urls_file}: {e}")
        return []


def create_example_urls_file():
    """Create an example URLs file if none exists."""
    example_data = {
        "urls": [
            "https://httpbin.org/",
            "https://jsonplaceholder.typicode.com/",
            "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/",
            # Add your URLs here:
            # "https://your-site.com",
            # "http://your-onion-site.onion"
        ]
    }
    
    filename = "urls.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(example_data, f, indent=2)
    
    print(f"Created example URLs file: {filename}")
    print("Edit this file to add your own URLs")
    return filename


async def main(urls_file: str, use_tor: bool = False):
    """
    Main crawler execution function for background operation.
    
    Args:
        urls_file: Path to JSON file containing URLs to crawl
        use_tor: Whether to use Tor proxy (always False as specified)
    """
    logger = setup_logging(__name__)
    
    print("Advanced Web Crawler - Starting Operation")
    print("=" * 60)
    
    # Load URLs from file
    urls = await load_urls_from_file(urls_file)
    if not urls:
        print("No valid URLs found. Exiting.")
        sys.exit(1)
    
    print(f"Loaded {len(urls)} URLs to crawl")
    print(f"Tor usage: {'Enabled' if use_tor else 'Disabled'}")
    
    # Initialize components
    tracker = JSONTracker(JSON_FILE)
    await tracker.load_data()
    
    crawler = AsyncWebCrawler(use_tor=use_tor)
    
    # Print initial stats
    initial_stats = tracker.get_stats()
    print(f"\nInitial state:")
    print(f"  Tracked domains: {initial_stats['domains']}")
    print(f"  Tracked files: {initial_stats['files']}")
    print(f"  Tracked keys: {initial_stats['keys']}")
    
    print(f"\nStarting crawl operation...")
    print("-" * 60)
    
    start_time = time.time()
    
    try:
        # Execute the crawl with timeout (5 minutes)
        results = await asyncio.wait_for(
            crawler.crawl_multiple_sites(urls, tracker),
            timeout=300  # 5 minutes timeout
        )
        
        # Calculate final stats
        final_stats = tracker.get_stats()
        elapsed_time = time.time() - start_time
        
        # Print final results
        print("\n" + "=" * 60)
        print("CRAWL OPERATION COMPLETED")
        print("=" * 60)
        print(f"Total execution time: {elapsed_time:.2f} seconds")
        print(f"Total pages visited: {results['pages_visited']}")
        print(f"Total files downloaded: {results['files_downloaded']}")
        print(f"Total files skipped: {results['files_skipped']}")
        print(f"Total keys found: {results['keys_found']}")
        print(f"Total domains tracked: {final_stats['domains']}")
        print(f"Total files tracked: {final_stats['files']}")
        print(f"Total keys tracked: {final_stats['keys']}")
        
        # Show file locations
        if results['files_downloaded'] > 0:
            print(f"\nDownloads saved to: {Path('downloads').absolute()}")
        print(f"Tracking data saved to: {JSON_FILE.absolute()}")
        print(f"Logs saved to: {Path('crawler.log').absolute()}")
        
        # Log final statistics
        logger.info(f"Crawl completed - Pages: {results['pages_visited']}, "
                   f"Files: {results['files_downloaded']}, "
                   f"Keys: {results['keys_found']}")
        
        return results
        
    except asyncio.TimeoutError:
        elapsed_time = time.time() - start_time
        print(f"\nCrawl timed out after {elapsed_time:.2f} seconds (5 minute limit)")
        logger.error(f"Crawl timed out after {elapsed_time:.2f} seconds")
        
        # Try to get partial results if available
        try:
            partial_stats = tracker.get_stats()
            print(f"Partial results before timeout:")
            print(f"  Domains tracked: {partial_stats['domains']}")
            print(f"  Files tracked: {partial_stats['files']}")
            print(f"  Keys tracked: {partial_stats['keys']}")
        except Exception:
            pass
            
        sys.exit(1)
    except KeyboardInterrupt:
        elapsed_time = time.time() - start_time
        print(f"\nCrawl interrupted by user after {elapsed_time:.2f} seconds")
        logger.warning(f"Crawl interrupted by user after {elapsed_time:.2f} seconds")
        sys.exit(130)
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Crawl failed after {elapsed_time:.2f} seconds: {e}")
        print(f"Crawl failed after {elapsed_time:.2f} seconds: {e}")
        sys.exit(1)
    finally:
        await crawler.close()


if __name__ == "__main__":
    # Configuration
    URLS_FILE = "urls.json"  # Change this to your file path
    USE_TOR = False  # Always False as per requirements
    
    try:
        # Option 1: Use hardcoded path from above
        urls_file = URLS_FILE
        use_tor = USE_TOR
        
        # Option 2: Fallback to command line arguments if provided
        if len(sys.argv) >= 2:
            urls_file = sys.argv[1]
            use_tor = "--tor" in sys.argv
            print(f"Using command line argument: {urls_file}")
        else:
            print(f"Using hardcoded path: {urls_file}")
        
        # Validate file exists
        if not Path(urls_file).exists():
            print(f"Error: File '{urls_file}' not found")
            
            # Auto-create example file if using hardcoded path
            if urls_file == URLS_FILE:
                print(f"Creating example file: {urls_file}")
                create_example_urls_file()
                print(f"File created. Edit {urls_file} and run again.")
            else:
                print(f"Create the file or update the path in main.py")
            
            sys.exit(1)
        
        # Run the crawler
        asyncio.run(main(urls_file, use_tor))
        
    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(130)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)