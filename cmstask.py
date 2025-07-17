import pandas as pd
import requests
import json
import time
# === Configuration ===
API_KEY = 'wmbjxyw7tkkzlcwbtceaq8sshgrz84q5snnu612z7wtsv9a5liwitfyb4w5rpivhq0plm9'
INPUT_FILE = 'Senior DA - Assignment.xlsx'    
OUTPUT_FILE = 'whatcms_output.xlsx'
INPUT_SHEET = 'WHATCMS INPUT'


# === STEP 2: Read input file ===
df = pd.read_excel(INPUT_FILE, sheet_name=INPUT_SHEET)

if 'url' not in df.columns:
    raise Exception("Input Excel must contain a column named 'URL'")

urls = df['url'].dropna().unique()

# === STEP 3: Function to call WhatCMS API ===
def get_whatcms_data(url):
    endpoint = "https://whatcms.org/API/Tech"
    params = {'key': API_KEY, 'url': url}

    try:
        response = requests.get(endpoint, params=params, timeout=10)
        result = response.json()
        print(result)
        print(response.status_code)

        data = {
            "whatcms_link": f"https://whatcms.org/API/Tech?key={API_KEY}&url={url}",
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

    except requests.exceptions.RequestException as e:
        status_code = getattr(e.response, "status_code", None) or 500
        return {
            "whatcms_link": f"https://whatcms.org/API/Tech?key={API_KEY}&url={url}",
            "Blog_CMS": None,
            "E-commerce_CMS": None,
            "Programming_Language": None,
            "Database": None,
            "CDN": None,
            "Web_Server": None,
            "Landing_Page_Builder_CMS": None,
            "Operating_System": None,
            "Web_Framework": None,
            "whatcms_response": status_code 
        }

results = []

for i, url in enumerate(urls, 1):
    print(f"🔍 Processing {i}/{len(urls)}: {url}")
    cleaned_url = url.replace("http://", "").replace("https://", "").split("/")[0]
    data = get_whatcms_data(cleaned_url)
    results.append({"URL": url, **data})
    time.sleep(1)  # Avoid hitting rate limits

# === STEP 5: Save to output Excel ===
output_df = pd.DataFrame(results)
output_df.to_excel(OUTPUT_FILE, index=False)
print(f"✅ Done. Results saved to '{OUTPUT_FILE}'")
