#!/usr/bin/env python3
"""
Granby Police Daily Journal PDF Scraper
Automatically downloads new PDF files from the Granby CT Police archive.
"""

import os
import re
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

class GranbyPDFScraper:
    def __init__(self, base_url="https://www.granby-ct.gov/Archive.aspx?AMID=40", 
                 download_dir="granby_police_journals"):
        self.base_url = base_url
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        
        # Setup logging
        log_file = self.download_dir / "scraper.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # File to track downloaded files
        self.downloaded_files_db = self.download_dir / "downloaded_files.json"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def load_downloaded_files(self):
        """Load the list of previously downloaded files."""
        if self.downloaded_files_db.exists():
            try:
                with open(self.downloaded_files_db, 'r') as f:
                    return set(json.load(f))
            except (json.JSONDecodeError, IOError) as e:
                self.logger.warning(f"Could not load downloaded files database: {e}")
                return set()
        return set()
    
    def save_downloaded_files(self, downloaded_files):
        """Save the list of downloaded files."""
        try:
            with open(self.downloaded_files_db, 'w') as f:
                json.dump(list(downloaded_files), f, indent=2)
        except IOError as e:
            self.logger.error(f"Could not save downloaded files database: {e}")
    
    def get_pdf_links(self):
        """Extract PDF links from the archive page."""
        try:
            response = self.session.get(self.base_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all links that contain "PDF" and match the daily journal pattern
            pdf_links = []
            links = soup.find_all('a', href=True)
            
            for link in links:
                href = link.get('href')
                text = link.get_text(strip=True)
                
                # Look for Daily Journal PDF links
                if 'PDF' in text and 'Daily Journal' in text:
                    # Extract date from the text (format: Daily Journal MM-DD-YYYY (PDF))
                    date_match = re.search(r'Daily Journal (\d{2}-\d{2}-\d{4})', text)
                    if date_match:
                        date_str = date_match.group(1)
                        full_url = urljoin(self.base_url, href)
                        
                        pdf_info = {
                            'url': full_url,
                            'filename': f"Daily_Journal_{date_str}.pdf",
                            'date': date_str,
                            'original_text': text
                        }
                        pdf_links.append(pdf_info)
            
            self.logger.info(f"Found {len(pdf_links)} PDF links on the page")
            return pdf_links
            
        except requests.RequestException as e:
            self.logger.error(f"Error fetching the archive page: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error parsing PDF links: {e}")
            return []
    
    def download_pdf(self, pdf_info):
        """Download a single PDF file."""
        filename = pdf_info['filename']
        url = pdf_info['url']
        file_path = self.download_dir / filename
        
        try:
            response = self.session.get(url, timeout=60, stream=True)
            response.raise_for_status()
            
            # Check if it's actually a PDF
            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' not in content_type:
                self.logger.warning(f"Warning: {filename} may not be a PDF (content-type: {content_type})")
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            file_size = file_path.stat().st_size
            self.logger.info(f"Downloaded {filename} ({file_size:,} bytes)")
            return True
            
        except requests.RequestException as e:
            self.logger.error(f"Error downloading {filename}: {e}")
            return False
        except IOError as e:
            self.logger.error(f"Error saving {filename}: {e}")
            return False
    
    def run(self):
        """Main scraping function."""
        self.logger.info("Starting PDF scraping process")
        
        # Load previously downloaded files
        downloaded_files = self.load_downloaded_files()
        self.logger.info(f"Found {len(downloaded_files)} previously downloaded files")
        
        # Get current PDF links
        pdf_links = self.get_pdf_links()
        if not pdf_links:
            self.logger.warning("No PDF links found. Exiting.")
            return
        
        # Filter out already downloaded files
        new_files = []
        for pdf_info in pdf_links:
            if pdf_info['filename'] not in downloaded_files:
                new_files.append(pdf_info)
        
        self.logger.info(f"Found {len(new_files)} new files to download")
        
        if not new_files:
            self.logger.info("No new files to download")
            return
        
        # Download new files
        successful_downloads = []
        for pdf_info in new_files:
            if self.download_pdf(pdf_info):
                successful_downloads.append(pdf_info['filename'])
                downloaded_files.add(pdf_info['filename'])
        
        # Update downloaded files database
        if successful_downloads:
            self.save_downloaded_files(downloaded_files)
            self.logger.info(f"Successfully downloaded {len(successful_downloads)} new files")
        
        self.logger.info("Scraping process completed")

def main():
    """Main entry point."""
    # You can customize the download directory here
    download_dir = os.path.expanduser("~/Documents/Granby_Police_Journals")
    
    scraper = GranbyPDFScraper(download_dir=download_dir)
    scraper.run()

if __name__ == "__main__":
    main()
