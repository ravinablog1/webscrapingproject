import undetected_chromedriver as uc
import chromedriver_autoinstaller
from bs4 import BeautifulSoup
import pandas as pd
import time
import random

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

#Auto-install ChromeDriver
chromedriver_autoinstaller.install()

# Chrome options
options = uc.ChromeOptions()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--headless=new")  # Run headless
options.add_argument("user-agent=Mozilla/5.0")

def launch_browser():
    driver = uc.Chrome(options=options)
    driver.set_page_load_timeout(120)
    driver.set_script_timeout(90)
    return driver

# Launch browser
driver = launch_browser()
base_url = "https://www.cityu.edu.hk"
all_startup_links = []

# Load startup list page(s)
for page in range(42):
    page_url = f"{base_url}/hktech300/start-ups/all-start-ups?page={page}"
    
    for attempt in range(3):
        try:
            driver.get(page_url)
            time.sleep(2)
            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/hktech300/start-ups/seed-fund-teams/']"))
            )
            break
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt == 2:
                print("Restarting browser...")
                driver.quit()
                driver = launch_browser()
            time.sleep(random.uniform(3, 6))
    else:
        continue

    soup = BeautifulSoup(driver.page_source, "html.parser")
    links =soup.select("a[href*='/hktech300/start-ups/seed-fund-teams/'], \
             a[href*='/hktech300/start-ups/ideation-teams/'], \
             a[href*='/hktech300/start-ups/angel-fund-teams/']")

    for a in links:
        name = a.get_text(strip=True).replace("\n", " ")
        if not name:
            continue
        href = a["href"]
        full_url = f"{base_url}{href}"
        all_startup_links.append((name, full_url))

# Remove duplicates (based on Name + URL)
seen = set()
unique_startup_links = []
for name, url in all_startup_links:
    key = (name.strip().lower(), url.strip().lower())
    if key not in seen:
        seen.add(key)
        unique_startup_links.append((name, url))

# Scrape detail pages
startup_data = []
social_domains = ['facebook.com', 'linkedin.com', 'twitter.com', 'instagram.com', 'youtube.com']

for i, (startup_name, detail_url) in enumerate(unique_startup_links, 1):

    for attempt in range(3):
        try:
            driver.get(detail_url)
            time.sleep(1.5)
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))
            soup = BeautifulSoup(driver.page_source, "html.parser")
            break
        except Exception as e:
            if attempt == 2:
                print("Restarting browser...")
                driver.quit()
                driver = launch_browser()
            time.sleep(random.uniform(3, 6))
    else:
        startup_data.append({
            "Company Name": startup_name,
            "Company Website": "No Info Found",
            "Email": "No Info Found",
            "CityU URL": detail_url
        })
        continue

    #Extract external website and email
    ext_link = soup.select_one("a[href^='http']:not([href*='cityu.edu.hk'])")
    email_tag = soup.select_one("a[href^='mailto:']")

    website = ext_link['href'] if ext_link else "No Info Found"
    if any(domain in website for domain in social_domains):
        website = "No Info Found"

    email = email_tag['href'].replace("mailto:", "") if email_tag else "No Info Found"
    if email.lower() == "hktech300.info@cityu.edu.hk":
        email = "No Info Found"

    startup_data.append({
        "Company Name": startup_name,
        "Company Website": website,
        "Email": email,
        "CityU URL": detail_url
    })

    print(f"Saved: {startup_name}")

# Save to CSV (deduplicated again for safety)
df = pd.DataFrame(startup_data).drop_duplicates(subset=["Company Name", "Company Website", "Email", "CityU URL"])
df.to_csv("all_startup_details2.csv", index=False)
print("\n Done. Data saved to 'all_startup_details.csv'")

driver.quit()
