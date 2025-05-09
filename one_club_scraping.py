import re  
import logging
import pandas as pd  
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By  
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager  

# — Logging setup —
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# — Selenium headless setup —
opts = Options()
opts.add_argument("--headless")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)

all_records = []

try:
    for year in range(2008, 2025):
        url = f"https://iplt20stats.com/ipl-{year}/royal-challengers-bangalore"
        logging.info(f"Loading season {year} → {url}")
        driver.get(url)

        # wait for the stats “table-responsive” block under .collapse.show :contentReference[oaicite:6]{index=6}
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".collapse.show .table-responsive"))
        )

        # grab its full visible text (header + all players) :contentReference[oaicite:7]{index=7}
        block = driver.find_element(By.CSS_SELECTOR, ".collapse.show .table-responsive")
        lines = [ln.strip() for ln in block.text.splitlines() if ln.strip()]

        # locate header row dynamically (starts with “Player Total Runs”) :contentReference[oaicite:8]{index=8}
        hdr_idx = next(i for i, ln in enumerate(lines) if ln.startswith("Player Total Runs"))
        data_lines = lines[hdr_idx + 1 :]

        # parse into player chunks
        i = 0
        roles = {"Batsman", "Bowler", "All‑rounder", "Wicket‑keeper"}
        while i < len(data_lines):
            ln = data_lines[i]
            if not ln.startswith("P:") and not any(ln.startswith(r) for r in roles):
                name = ln
                # next line = role + runs
                parts = data_lines[i + 1].split()
                role = parts[0]
                runs = parts[1] if len(parts) > 1 else "0"

                # collect up to five “P:” lines
                stats = []
                j = i + 2
                while j < len(data_lines) and data_lines[j].startswith("P:"):
                    nums = re.findall(r"\d+", data_lines[j])  # :contentReference[oaicite:9]{index=9}
                    stats.append(nums[-1] if nums else "0")
                    j += 1

                # pad/trim to five stats: Fours, Sixes, Wickets, Dots, 50s
                stats = (stats + ["0"] * 5)[:5]
                fours, sixes, wickets, dots, fifties = stats

                all_records.append({
                    "Year":          year,
                    "Player":        name,
                    "Role":          role,
                    "Total Runs":    runs,
                    "Total Fours":   fours,
                    "Total Sixes":   sixes,
                    "Total Wickets": wickets,
                    "Total Dots":    dots,
                    "Total 50s":     fifties
                })
                i = j
            else:
                i += 1

    # build master DataFrame & save
    df = pd.DataFrame(all_records)
    logging.info(f"Total records collected: {len(df)}")
    print(df.head(10))
    df.to_csv("rcb_2008_2024_stats.csv", index=False)
    logging.info("Saved all seasons to rcb_2008_2024_stats.csv")

finally:
    driver.quit()
