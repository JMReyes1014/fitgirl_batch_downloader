from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import requests
import json
import os
import time
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from pathlib import Path
import asyncio
import aiohttp
from tqdm.asyncio import tqdm  # For async progress bar with asyncio
from tqdm import tqdm  # For synchronous progress bars
import humanize
import traceback
from aiohttp import ClientSession, ClientTimeout
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


class DownloadLinkExtractor:
    def __init__(self):
        self.output_file = "final_download_links.json"
        self.setup_browser()

    def setup_browser(self):
        options = Options()
        options.add_argument('--headless')  # Run in background
        options.add_argument('--disable-dev-shm-usage')  # Overcome resource constraints
        options.add_argument('--no-sandbox')  # Bypass OS security model
        options.add_argument('--remote-debugging-port=9222')  # Debugging port

        # Increase page load and script execution timeouts
        caps = DesiredCapabilities().EDGE
        caps['pageLoadStrategy'] = 'normal'  # Wait until the page is fully loaded
        caps['timeouts'] = {
            "implicit": 240000,  # 240 seconds
            "pageLoad": 240000,  # 240 seconds
            "script": 240000  # 240 seconds
        }

        service = Service(EdgeChromiumDriverManager().install())
        self.driver = webdriver.Edge(service=service, options=options)

    def get_initial_links(self, url):
        print("Fetching initial links...")
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        return [a['href'] for a in soup.find_all('a', href=True) if "fuckingfast.co" in a['href']]

    def get_final_download_link(self, url):
        try:
            self.driver.get(url)

            # Get page source and extract download link using regex
            import re
            page_source = self.driver.page_source
            download_pattern = r'window\.open\("(https://fuckingfast\.co/dl/[^\"]+)"\)'
            match = re.search(download_pattern, page_source)

            if match:
                final_url = match.group(1)
                return {
                    'initial_url': url,
                    'final_url': final_url,
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                }
            else:
                script = r"""
                let downloadFunc = document.querySelector('.link-button').getAttribute('onclick');
                if (downloadFunc) {
                    return downloadFunc.toString().match(/window\.open\("([^\"]+)"\)/)[1];
                }
                return null;
                """
                final_url = self.driver.execute_script(script)

                if final_url:
                    return {
                        'initial_url': url,
                        'final_url': final_url,
                        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                    }

            print(f"Could not extract download link from {url}")
            return None

        except Exception as e:
            print(f"Error processing {url}: {e}")
            return None
        finally:
            # Clear any extra tabs
            while len(self.driver.window_handles) > 1:
                self.driver.switch_to.window(self.driver.window_handles[-1])
                self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])

    def save_links(self, links):
        with open(self.output_file, 'w') as f:
            json.dump(links, f, indent=2)
        print(f"Links saved to {self.output_file}")

    def extract_all_links(self, fitgirl_url):
        initial_links = self.get_initial_links(fitgirl_url)
        print(f"Found {len(initial_links)} initial links")

        final_links = []
        for i, link in enumerate(initial_links, 1):
            print(f"\nProcessing link {i}/{len(initial_links)}")
            final_link = self.get_final_download_link(link)
            if final_link:
                final_links.append(final_link)

        self.save_links(final_links)
        return final_links

    def cleanup(self):
        self.driver.quit()


class BatchDownloader:
    def __init__(self, json_file, batch_size=1, max_retries=3, retry_delay=5):
        self.json_file = json_file
        self.batch_size = batch_size
        self.download_dir = Path("C:/Users/Downloads") # Change this to your desired download directory
        self.download_dir.mkdir(exist_ok=True)
        self.progress_file = self.download_dir / "download_progress.json"
        self.semaphore = asyncio.Semaphore(batch_size)
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def load_links(self):
        with open(self.json_file) as f:
            return json.load(f)

    def load_progress(self):
        if self.progress_file.exists():
            with open(self.progress_file) as f:
                return set(json.load(f))
        return set()

    def save_progress(self, url):
        progress = self.load_progress()
        progress.add(url)
        with open(self.progress_file, 'w') as f:
            json.dump(list(progress), f)

    async def download_file_with_session(self, link_data, session):
        initial_url = link_data['initial_url']
        download_url = link_data['final_url']

        filename = initial_url.split('#')[1]
        filepath = self.download_dir / filename

        if filepath.exists():
            print(f"\nSkipping {filename} - already exists")
            return

        attempts = 0
        while attempts < self.max_retries:
            try:
                async with self.semaphore:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    }
                    async with session.get(download_url, headers=headers) as response:
                        if response.status != 200:
                            print(f"\nError downloading {filename}: HTTP {response.status}")
                            raise Exception(f"HTTP error {response.status}")

                        total_size = int(response.headers.get('content-length', 0))
                        with tqdm(
                            total=total_size,
                            unit='iB',
                            unit_scale=True,
                            unit_divisor=1024,
                            desc=filename,
                            leave=True
                        ) as progress_bar:
                            with open(filepath, 'wb') as f:
                                async for chunk in response.content.iter_chunked(8196):
                                    f.write(chunk)
                                    progress_bar.update(len(chunk))
                    self.save_progress(initial_url)
                    break
            except Exception as e:
                print(f"\nError downloading {filename} (Attempt {attempts + 1}/{self.max_retries}): {str(e)}")
                attempts += 1
                if attempts < self.max_retries:
                    print(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    print(f"Failed to download {filename} after {self.max_retries} attempts.")
                    if filepath.exists():
                        filepath.unlink()

    async def download_all(self):
        links = self.load_links()
        completed = self.load_progress()
        remaining = [link for link in links if link['initial_url'] not in completed]

        if not remaining:
            print("All downloads completed!")
            return

        print(f"Starting downloads: {len(remaining)} files remaining")

        timeout = ClientTimeout(total=2400)
        connector = aiohttp.TCPConnector(limit_per_host=20)  # Increased limit for parallel connections
        async with ClientSession(connector=connector, timeout=timeout) as session:
            tasks = []
            for link in remaining:
                tasks.append(self.download_file_with_session(link, session))

                if len(tasks) >= self.batch_size:
                    await asyncio.gather(*tasks)
                    tasks.clear()

            if tasks:
                await asyncio.gather(*tasks)


def main():
    url = input("Enter Fitgirl Repack page URL: ").strip()
    if not url:
         print("Please provide a valid URL")
         return

    extractor = DownloadLinkExtractor()
    try:
         extractor.extract_all_links(url)
    finally:
         extractor.cleanup()

    #Actual download loop
    downloader = BatchDownloader('final_download_links.json', batch_size=3)
    asyncio.run(downloader.download_all())

if __name__ == "__main__":
    main()