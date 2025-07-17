import pandas as pd
import requests
import time
import logging
from typing import Dict
import os
from dotenv import load_dotenv


# === Logging Setup ===
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("whatcms_scraper.log"),
        logging.StreamHandler()
    ]
)

class WhatCMSScraper:
    """
    Class to fetch CMS technology data from WhatCMS API for a list of URLs.
    """

    def __init__(self, api_key: str, input_file: str, input_sheet: str, output_file: str):
        self.api_key = api_key
        self.input_file = input_file
        self.input_sheet = input_sheet
        self.output_file = output_file
        self.urls = []

    def read_input_urls(self):
        """
        Reads input Excel file and extracts unique URLs.
        """
        logging.info(f"Reading input file: {self.input_file} [Sheet: {self.input_sheet}]")
        df = pd.read_excel(self.input_file, sheet_name=self.input_sheet)

        if 'url' not in df.columns:
            raise ValueError("Input Excel must contain a column named 'url'")

        self.urls = df['url'].dropna().unique()
        logging.info(f"Found {len(self.urls)} unique URLs.")

    def get_whatcms_data(self, url: str) -> Dict[str, str]:
        """
        Queries the WhatCMS API for technology data about the given URL.
        Returns structured result data.
        """
        endpoint = "https://whatcms.org/API/Tech"
        cleaned_url = url.replace("http://", "").replace("https://", "").split("/")[0]
        params = {"key": self.api_key, "url": cleaned_url}

        logging.debug(f"Calling WhatCMS API for: {cleaned_url}")

        try:
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            result = response.json()

            data = {
                "whatcms_link": response.url,
                "Blog_CMS": None,
                "E-commerce_CMS": None,
                "Programming_Language": None,
                "Database": None,
                "CDN": None,
                "Web_Server": None,
                "Landing_Page_Builder_CMS": None,
                "Operating_System": None,
                "Web_Framework": None,
                "whatcms_response": response.status_code
            }

            for tech in result.get("results", []):
                name = tech.get("name")
                categories = tech.get("categories", [])

                for category in categories:
                    if category == "Blog":
                        data["Blog_CMS"] = name
                    elif category == "E-commerce":
                        data["E-commerce_CMS"] = name
                    elif category == "Programming Language":
                        data["Programming_Language"] = name
                    elif category == "Database":
                        data["Database"] = name
                    elif category == "CDN":
                        data["CDN"] = name
                    elif category == "Web Server":
                        data["Web_Server"] = name
                    elif category == "Landing Page Builder":
                        data["Landing_Page_Builder_CMS"] = name
                    elif category == "Operating System":
                        data["Operating_System"] = name
                    elif category == "Web Framework":
                        data["Web_Framework"] = name

            return data

        except requests.RequestException as e:
            logging.error(f"Error calling WhatCMS for {url}: {e}")
            return {
                "whatcms_link": f"{endpoint}?key={self.api_key}&url={cleaned_url}",
                "Blog_CMS": None,
                "E-commerce_CMS": None,
                "Programming_Language": None,
                "Database": None,
                "CDN": None,
                "Web_Server": None,
                "Landing_Page_Builder_CMS": None,
                "Operating_System": None,
                "Web_Framework": None,
                "whatcms_response": getattr(e.response, "status_code", 500)
            }

    def scrape_all(self):
        """
        Loops through URLs, fetches CMS data, and stores it.
        """
        logging.info("Starting scraping process...")
        results = []

        for count, url in enumerate(self.urls, 1):
            logging.info(f"Processing {i}/{len(self.urls)}: {url}")
            result = self.get_whatcms_data(url)
            results.append({"URL": url, **result})
            time.sleep(1)  # Respect API rate limits

        return results

    def save_results(self, results: list):
        """
        Saves results to output Excel file.
        """
        logging.info(f"Saving results to {self.output_file}...")
        df = pd.DataFrame(results)
        df.to_excel(self.output_file, index=False)
        logging.info("Results saved successfully.")

    def run(self):
        """
        Runs the entire process from reading input to saving output.
        """
        try:
            self.read_input_urls()
            results = self.scrape_all()
            self.save_results(results)
        except Exception as e:
            logging.error(f"An error occurred: {e}")

if __name__ == "__main__":
    load_dotenv()

    scraper = WhatCMSScraper(
        api_key=os.getenv("API_KEY"),
        input_file=os.getenv("INPUT_FILE"),
        input_sheet=os.getenv("INPUT_SHEET"),
        output_file=os.getenv("OUTPUT_FILE")
    )
    scraper.run()
