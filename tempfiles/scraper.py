import random, logging
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS

# — Configuration —
USER_AGENTS = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64)…", "Mozilla/5.0 (Macintosh; Intel Mac OS X)…"]
TEAM_SLUGS  = [
    "chennai-super-kings","delhi-capitals","gujarat-titans","kolkata-knight-riders",
    "lucknow-super-giants","mumbai-indians","punjab-kings","rajasthan-royals",
    "royal-challengers-bengaluru","sunrisers-hyderabad"
]
YEARS = [2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016, 2015, 2014, 2013, 2012, 2011, 2010, 2009, 2008]

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

def create_driver():
    ua = random.choice(USER_AGENTS)
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument(f"--user-agent={ua}")
    service = EdgeService(EdgeChromiumDriverManager().install())
    return webdriver.Edge(service=service, options=opts)


def scrape_team_archive(driver, team):
    url = f"https://www.iplt20.com/teams/{team}/archive"
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    table = soup.find("table")
    if not table:
        logging.warning(f"No <table> found on archive page for {team}")
        return []

    body = table.find("tbody")
    if not body:
        logging.warning(f"No <tbody> in archive table for {team}")
        return []

    stats = []
    for row in body.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 4:
            continue
        year        = cells[0].get_text(strip=True)
        position    = cells[1].get_text(strip=True)
        top_scorer  = cells[2].get_text(strip=True)
        top_wickets = cells[3].get_text(strip=True)
        if year.isdigit() and int(year) in YEARS:
            stats.append({
                "team": team,
                "year": int(year),
                "position": position,
                "top_scorer": top_scorer,
                "top_wickets": top_wickets
            })
    return stats


def run_scrape():
    driver = create_driver()
    all_stats = []
    try:
        for team in TEAM_SLUGS:
            recs = scrape_team_archive(driver, team)
            if recs:
                logging.info(f"{team}: collected {len(recs)} rows")
                all_stats.extend(recs)
            else:
                logging.info(f"{team}: no data found")
    finally:
        driver.quit()

    df = pd.DataFrame(all_stats)
    df.to_csv("ipl_team_stats.csv", index=False)
    logging.info(f"Saved {len(df)} records to ipl_team_stats.csv")

    if "position" in df:
        df["position"] = pd.to_numeric(df["position"], errors="coerce")
        avg_pos = df.groupby("team")["position"].mean()
        plt.figure(); plt.bar(avg_pos.index, avg_pos.values)
        plt.xticks(rotation=45, ha="right"); plt.ylabel("Avg Position")
        plt.title("Avg Finish Position (2020–2024)"); plt.tight_layout(); plt.show()

    if "top_scorer" in df:
        counts = df["top_scorer"].value_counts()
        plt.figure(); plt.plot(counts.index, counts.values, marker="o")
        plt.xticks(rotation=90); plt.ylabel("Count"); plt.title("Top Scorer Frequency"); plt.tight_layout(); plt.show()

        text = " ".join(df["top_scorer"])
        wc = WordCloud(width=800, height=400, background_color="white",
                       stopwords=set(STOPWORDS)).generate(text)
        plt.figure(figsize=(10,5)); plt.imshow(wc, interpolation="bilinear")
        plt.axis("off"); plt.title("Word Cloud of Top Scorers"); plt.show()


if __name__ == "__main__":
    logging.info("Starting IPL scraper…")
    run_scrape()
    logging.info("Scrape complete.")