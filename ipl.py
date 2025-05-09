import re
import logging
import pandas as pd  # DataFrame ops 
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By  # locators :contentReference[oaicite:10]{index=10}
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ipl_scraper.settings")
django.setup()
from stats.utils import save_stats_batch






logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Headless Chrome setup
opts = Options()
opts.add_argument("--headless")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)

# Current franchises (for naming only)
teams = ["delhi", "punjab", "chennai-super-kings", "kolkata-knight-riders",
         "royal-challengers-bangalore", "rajasthan-royals", "mumbai-indians",
         "hyderabad", "gujarat", "lucknow-supergiants"]

def get_slug(team, year):
    """Return the correct URL slug for a given team in a given year, or None if not active."""
    if team == "delhi":
        return "delhi-daredevils" if year <= 2018 else "delhi-capitals"  # rename in 2019 :contentReference[oaicite:11]{index=11}
    if team == "punjab":
        return "kings-xi-punjab" if year <= 2020 else "punjab-kings"     # rename in 2021 :contentReference[oaicite:12]{index=12}
    if team == "hyderabad":
        return "deccan-chargers" if year <= 2012 else "sunrisers-hyderabad"  # re‑launch 2013 :contentReference[oaicite:13]{index=13}
    if team == "gujarat":
        return "gujarat-titans" if year >= 2022 else None  # Titans start 2022 :contentReference[oaicite:14]{index=14}
    if team == "lucknow-supergiants":
        return "lucknow-supergiants" if year >= 2022 else None  # start 2022 :contentReference[oaicite:15]{index=15}
    # unchanged slugs for others, active all years
    return team

all_records = []
for year in range(2008, 2026):
    for team in teams:
        slug = get_slug(team, year)
        if not slug:
            logging.warning(f"{team.title()} did not exist in {year}, skipping.")  # skip defunct :contentReference[oaicite:16]{index=16}
            continue

        url = f"https://iplt20stats.com/ipl-{year}/{slug}"
        logging.info(f"Loading {year} – {slug}")
        driver.get(url)

        # wait for stats container; skip on timeout
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".collapse.show .table-responsive"))
            )
        except TimeoutException:
            logging.warning(f"No stats for {slug} in {year}, skipping.")
            continue

        # snapshot text, split lines
        block = driver.find_element(By.CSS_SELECTOR, ".collapse.show .table-responsive")
        lines = [ln.strip() for ln in block.text.splitlines() if ln.strip()]

        # find header dynamically
        try:
            hdr = next(i for i, ln in enumerate(lines) if ln.startswith("Player Total Runs"))
        except StopIteration:
            logging.warning(f"Header missing for {slug} in {year}, skipping.")
            continue
        data = lines[hdr + 1:]

        # parse players
        i = 0
        roles = {"Batsman", "Bowler", "All‑rounder", "Wicket‑keeper"}
        while i < len(data):
            ln = data[i]
            if not ln.startswith("P:") and not any(ln.startswith(r) for r in roles):
                name = ln
                parts = data[i+1].split()
                role, runs = parts[0], parts[1] if len(parts)>1 else "0"

                stats = []
                j = i+2
                while j < len(data) and data[j].startswith("P:"):
                    nums = re.findall(r"\d+", data[j])  # extract digits 
                    stats.append(nums[-1] if nums else "0")
                    j += 1
                stats = (stats + ["0"]*5)[:5]
                f, s, w, d, f5 = stats

                all_records.append({
                    "Year": year,
                    "Team": slug.replace("-", " ").title(),
                    "Player": name,
                    "Role": role,
                    "Total Runs": runs,
                    "Total Fours": f,
                    "Total Sixes": s,
                    "Total Wickets": w,
                    "Total Dots": d,
                    "Total 50s": f5
                })
                i = j
            else:
                i += 1

# Build DataFrame & save
df = pd.DataFrame(all_records)
logging.info(f"Collected {len(all_records)} records, saving to database…")
save_stats_batch(all_records)
logging.info("Saved all seasons to database.")

driver.quit()

