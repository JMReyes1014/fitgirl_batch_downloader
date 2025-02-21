# Fitgirl Repacks Batch Downloader

## Description
A Simple Python script to automate downloading multiple parts from Fitgirl Repacks using Selenium WebDriver. This is my version, inspired from "amanmprojects" version.

When downloading large games from Fitgirl Repacks, which are often divided into numerous parts (sometimes over 100), the manual process can be tedious and time-consuming. This involves:

1. Clicking each download link
2. Waiting for the download page to load
3. Clicking the download button
4. Repeating the steps for every part
5. 
This script streamlines the process by managing multiple downloads in batches, reducing effort and saving time.

## Requirements

This project requires the following dependencies:

- `selenium`
- `webdriver-manager`
- `beautifulsoup4`
- `requests`
- `json`
- `os`
- `time`
- `pathlib`
- `asyncio`
- `aiohttp`
- `tqdm`
- `humanize`
- `traceback`

## Installation

The script requires:
- Python 3.6+

I used Python 3.11

To install the required dependencies, run:

```sh
pip install selenium webdriver-manager beautifulsoup4 requests aiohttp tqdm humanize
```

## Usage
Basic usage:
```bash
python script.py <url> 
```

Full options:
```bash
python script.py <url> [--browser edge|chrome] [--concurrent N] [--download-dir DIR] [--batch-size N]
```

Arguments:
- 

url

: URL of the Fitgirl Repacks page containing download links
- `--browser`: Browser to use for downloads (default: edge)
- `--concurrent`: Number of concurrent downloads (default: 1) 
- `--download-dir`: Download directory (default: ./downloaded_files)
- `--batch-size`: Number of files to process in each batch (default: 5)

Example:
```bash
python script.py https://fitgirl-repacks.site/game-name --browser chrome --download-dir D:\Downloads --batch-size 10

## Setup for Selenium WebDriver

Ensure you have the Edge WebDriver installed. It can be managed automatically using:

```python
from webdriver_manager.microsoft import EdgeChromiumDriverManager
service = Service(EdgeChromiumDriverManager().install())
driver = webdriver.Edge(service=service)
```

## Important Note

This tool is for educational purposes only. Users should consider bandwidth limitations and website terms of service. Whether to use this tool as well as [Fitgirl Repacks](https://fitgirl-repacks.site) is up to individual discretion and responsibility.

## License

MIT License

