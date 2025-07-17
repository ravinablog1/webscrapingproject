import time
import random
import logging
import pandas as pd
from bs4 import BeautifulSoup

import undetected_chromedriver as uc
import chromedriver_autoinstaller

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Setup logging
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler()
    ]
)

class HKTech300Scraper:
    """
    Scraper class for extracting HK Tech 300 startup data from CityU website.
    """

    def __init__(self):
        chromedriver_autoinstaller.install()
        self.base_url = "https://www.cityu.edu.hk"
        self.social_domains = ['facebook.com', 'linkedin.com', 'twitter.com', 'instagram.com', 'youtube.com']
        self.driver = self._launch_browser()
        self.startup_links = []
        self.startup_data = []

    def _launch_browser(self):
        """
        Launches and returns an undetected Chrome browser instance with custom options.
        """
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--headless=new")
        options.add_argument("user-agent=Mozilla/5.0")

        logging.info("Launching browser...")
        driver = uc.Chrome(options=options)
        driver.set_page_load_timeout(120)
        driver.set_script_timeout(90)
        return driver

    def _retry_load_page(self, url, wait_selector, retries=3):
        """
        Loads a URL with retry logic and waits for a selector to appear.
        """
        for attempt in range(retries):
            try:
                self.driver.get(url)
                time.sleep(2)
                WebDriverWait(self.driver, 60).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, wait_selector))
                )
                logging.info(f"Page loaded: {url}")
                return BeautifulSoup(self.driver.page_source, "html.parser")
            except Exception as e:
                logging.warning(f"Attempt {attempt + 1} failed for URL {url}: {e}")
                if attempt == retries - 1:
                    logging.error(f"Giving up on {url} after {retries} retries.")
                    return None
                self._restart_browser()
                time.sleep(random.uniform(3, 6))
        return None

    def _restart_browser(self):
        """
        Restarts the browser instance in case of repeated failure.
        """
        logging.info("Restarting browser...")
        try:
            self.driver.quit()
        except Exception:
            pass
        self.driver = self._launch_browser()

    def collect_startup_links(self, max_pages=42):
        """
        Collects startup links from paginated CityU listing.
        """
        logging.info("Collecting startup links...")
        for page in range(max_pages):
            page_url = f"{self.base_url}/hktech300/start-ups/all-start-ups?page={page}"
            soup = self._retry_load_page(page_url, "a[href*='/hktech300/start-ups/seed-fund-teams/']")
            if not soup:
                continue

            links = soup.select(
                "a[href*='/hktech300/start-ups/seed-fund-teams/'], \
                 a[href*='/hktech300/start-ups/ideation-teams/'], \
                 a[href*='/hktech300/start-ups/angel-fund-teams/']"
            )

            for a in links:
                name = a.get_text(strip=True)
                href = a.get("href", "")
                if name and href:
                    full_url = f"{self.base_url}{href}"
                    self.startup_links.append((name, full_url))
            logging.info(f"Collected links from page {page + 1}")

        # Deduplicate
        seen = set()
        self.startup_links = [
            (name, url) for name, url in self.startup_links
            if (key := (name.strip().lower(), url.strip().lower())) not in seen and not seen.add(key)
        ]
        logging.info(f"Total unique startup links: {len(self.startup_links)}")

    def scrape_startup_details(self):
        """
        Scrapes details (website/email) for each startup link.
        """
        logging.info("Scraping startup detail pages...")
        for index, (startup_name, detail_url) in enumerate(self.startup_links, 1):
            soup = self._retry_load_page(detail_url, "body")
            if not soup:
                self.startup_data.append({
                    "Company Name": startup_name,
                    "CityU URL": detail_url,
                    "Company Website": "No Info Found",
                    "Email": "No Info Found",
                })
                continue

            ext_link = soup.select_one("a[href^='http']:not([href*='cityu.edu.hk'])")
            email_tag = soup.select_one("a[href^='mailto:']")

            website = ext_link['href'] if ext_link else "No Info Found"
            if any(domain in website for domain in self.social_domains):
                website = "No Info Found"

            email = email_tag['href'].replace("mailto:", "") if email_tag else "No Info Found"
            if email.lower() == "hktech300.info@cityu.edu.hk":
                email = "No Info Found"

            self.startup_data.append({
                "Company Name": startup_name,
                "CityU URL": detail_url,
                "Company Website": website,
                "Email": email,

            })

            logging.info(f"[{index}/{len(self.startup_links)}] Saved: {startup_name}")

    def save_to_csv(self, filename="all_startup_details33.csv"):
        """
        Saves collected data to a CSV file.
        """
        logging.info(f"Saving data to {filename}...")
        df = pd.DataFrame(self.startup_data).drop_duplicates(
            subset=["Company Name","CityU URL","Company Website","Email"]
        )
        df.to_csv(filename, index=False)
        logging.info("Data saved successfully.")

    def close_browser(self):
        """
        Closes the browser instance.
        """
        logging.info("Closing browser...")
        self.driver.quit()

    def run(self):
        """
        Runs the full scraping workflow.
        """
        try:
            self.collect_startup_links()
            self.scrape_startup_details()
            self.save_to_csv()
        finally:
            self.close_browser()

if __name__ == "__main__":
    scraper = HKTech300Scraper()
    scraper.run()
