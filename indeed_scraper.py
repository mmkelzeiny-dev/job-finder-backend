from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import time
import random
from dotenv import load_dotenv
import os

load_dotenv()
SCRAPER_API_KEY = os.getenv("scraper_api_key")
PROXY = "http://scraperapi.render=true.country_code=us:{SCRAPER_API_KEY}@proxy-server.scraperapi.com:8001"

def scrape_jobs(job_query="software developer", location="Abu Dhabi", pages=1):
    all_jobs = []

    for page in range(pages):
        start = page * 10
        target_url = (
            f"https://ae.indeed.com/jobs?q={job_query.replace(' ', '+')}&l={location.replace(' ', '+')}&start={start}"
        )

        print(f"🌍 Loading: {target_url}")

        # --- Create a new driver each time ---
        options = Options()
        options.add_argument("--disable-blink-features=AutomationControlled")
        seleniumwire_options = {
            'proxy': {
                'http': PROXY,
                'https': PROXY,
            },
            'verify_ssl': False
        }
        driver = uc.Chrome(options=options, seleniumwire_options=seleniumwire_options)

        try:
            driver.get(target_url)
            print("⏳ Waiting for page to load...")
            time.sleep(random.uniform(5, 8))  # Wait for dynamic content

            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.ID, "mosaic-jobResults"))
                )
            except:
                print("⚠ Could not locate job results on this page")
                continue

            soup = BeautifulSoup(driver.page_source, "html.parser")
            job_results = soup.find("div", attrs={"id": "mosaic-jobResults"})
            job_elements = job_results.find_all("li", class_="css-1ac2h1w eu4oa1w0") if job_results else []

            print(f"✔ Found {len(job_elements)} job cards on page {page + 1}")

            for job_element in job_elements:
                title_el = job_element.select_one("a.jcs-JobTitle span")
                if not title_el:
                    continue
                title_text = title_el.get_text(strip=True)
                if not title_text or title_text == ".":
                    continue

                if "mosaic" in job_element.get("class", []):
                    continue

                # if not description:
                #     continue

                comp_el = job_element.select_one("span[data-testid='company-name']")
                loc_el = job_element.select_one("div[data-testid='text-location']")
                snip_el = job_element.select_one("div.job-snippet")
                salary_el = job_element.select_one("#salaryInfoAndJobType")
                desc_el = None

                # Try to fetch job description (optional)
                detail_url = ""
                link_el = job_element.select_one("a.jcs-JobTitle")
                description = ""
                if link_el and link_el.get("href"):
                    detail_url = "https://www.indeed.com" + link_el["href"]
                    try:
                        driver.get(detail_url)
                        time.sleep(random.uniform(2, 4))
                        detail_soup = BeautifulSoup(driver.page_source, "html.parser")
                        desc_tag = detail_soup.select_one("#jobDescriptionText")
                        description = desc_tag.get_text(" ", strip=True) if desc_tag else ""
                        if not description: 
                            continue
                    except:
                        description = ""
                
                job_data = {
                    "title": title_el.get_text(strip=True) if title_el else "",
                    "company": comp_el.get_text(strip=True) if comp_el else "",
                    "location": loc_el.get_text(strip=True) if loc_el else "",
                    "summary": snip_el.get_text(" ", strip=True) if snip_el else "",
                    "description": description,
                    "skills": [],          # empty by default
                    "job_type": "",        # empty by default
                    "job_link": detail_url
                }

                all_jobs.append(job_data)

            time.sleep(random.uniform(1.5, 3))  # polite delay

        finally:
            driver.quit()  # ensure Chrome closes every loop

    print(f"\n🎉 DONE — Scraped {len(all_jobs)} jobs")
    return all_jobs
# "salary": salary_el.get_text(strip=True) if salary_el else "",