# IPL Scraper & Stats Pipeline

A headless‐Chrome/Selenium‐based scraper for IPL player‐season statistics, integrated with a Django backend for storage and querying.

---

# Table of Contents

1. [Overview](#overview)  
2. [Model Architecture](#model-architecture)  
3. [Data Processing Pipeline](#data-processing-pipeline)  
4. [Setup & Installation](#setup--installation)  
5. [Usage](#usage)  
6. [Project Structure](#project-structure)  
7. [Troubleshooting](#troubleshooting)  
8. [License](#license)  

---

## Overview

This project scrapes IPL statistics (runs, fours, sixes, wickets, etc.) for each franchise and season (2008–present) from [iplt20stats.com](https://iplt20stats.com). Scraped data are normalized and stored in a PostgreSQL database via Django models, enabling downstream analysis, reporting, or API exposure.

---

## Model Architecture

All scraped stats are stored in a single Django model: `PlayerSeasonStat` in the `stats` app.

```python
class PlayerSeasonStat(models.Model):
    year           = models.PositiveSmallIntegerField(db_index=True)
    team           = models.CharField(max_length=64, db_index=True)
    player         = models.CharField(max_length=128, db_index=True)
    role           = models.CharField(max_length=32, choices=ROLE_CHOICES)
    total_runs     = models.PositiveIntegerField()
    total_fours    = models.PositiveIntegerField()
    total_sixes    = models.PositiveIntegerField()
    total_wickets  = models.PositiveIntegerField()
    total_dots     = models.PositiveIntegerField()
    total_fifties  = models.PositiveIntegerField()

    class Meta:
        unique_together = (('year', 'team', 'player'),)
        indexes = [
            models.Index(fields=['year', 'team']),
        ]
        ordering = ['-year', 'team', 'player']
```
Fields: cover all key batting/bowling aggregates per player per season.
Indexes: accelerate queries by year, team, and the composite (year, team).
Uniqueness: no duplicate (year, team, player) entries.

# Data Processing Pipeline
Scraper Initialization

1.Launch headless Chrome with Selenium & webdriver_manager.
Iterate seasons (2008–current) and all IPL franchises.
Dynamically adjust URL slugs for renamed teams (e.g., Delhi Daredevils → Delhi Capitals).

2.Page Load & Wait
Navigate to each team-season URL.
Wait (up to 10 s) for the statistics table to appear; skip if missing.

3.Raw Text Extraction
Extract table text, split into lines, and trim whitespace.

4.Header Detection & Row Parsing
Locate the “Player Total Runs” header.
For each player block:
Capture name, role, total runs, and next lines of ball-by-ball stats.
Use re to extract numeric fields, fall back to zero for placeholders ("-").

5.Record Assembly
Build a list of dictionaries—one per player—with keys:
'Year', 'Team', 'Player', 'Role', 'Total Runs', 'Total Fours', 'Total Sixes', 'Total Wickets', 'Total Dots', 'Total 50s'.

6.Storage in Django
Call save_stats_batch(records) from stats/utils.py.
Internally, ensure the stats_playerseasonstat table exists (auto-create via raw SQL).
Coerce all numeric strings safely to int.
Bulk-insert with ignore_conflicts=True to skip duplicates.

7.Archival & Retention (Optional)
For large archives, you can partition by year or move old seasons into an archive table via a management command.

# Setup & Installation
Prerequisites:
Python 3.9+

PostgreSQL 12+

Google Chrome (latest)

(Optional) virtualenv or venv

1. Clone & Virtualenv
```
git clone https://github.com/Madhan230205/IPL-AllPlayers-Stats-From-2008to2025
cd IPL-AllPlayers-Stats-From-2008to2025
python -m venv .venv
source .venv/bin/activate      # Linux / macOS
.venv\Scripts\activate         # Windows PowerShell
```

2. Install Dependencies
```
pip install --upgrade pip
pip install -r requirements.txt
```
3. Configure Database
Edit ipl_scraper/settings.py (or your local settings) to set up PostgreSQL:

```python
Copy
Edit
DATABASES = {
    'default': {
        'ENGINE':   'django.db.backends.postgresql',
        'NAME':     'ipl_db',
        'USER':     'your_db_user',
        'PASSWORD': 'your_password',
        'HOST':     'localhost',
        'PORT':     '5432',
    }
}
```
4. Run Migrations
```
python manage.py makemigrations stats
python manage.py migrate
```
5. (Optional) Create a Superuser
```
python manage.py createsuperuser
```
# Usage
1. Run the Scraper

python app.py

This will:
Spin up headless Chrome
Scrape all seasons & teams
Auto-create the DB table if missing
Bulk-insert stats into stats_playerseasonstat

2. Inspect via Django Shell / Admin
```

python manage.py shell
>>> from stats.models import PlayerSeasonStat
>>> PlayerSeasonStat.objects.filter(year=2024, team__icontains='Mumbai')
Or log in to the Django admin at http://127.0.0.1:8000/admin/ and browse “Player Season Stats.”
```
# Project Structure
```
ipl_scraper/
├── ipl.py                  # Main scraper entrypoint
├── stats/
│   ├── models.py           # Django model definitions
│   ├── utils.py            # save_stats_batch & table-ensure logic
│   └── migrations/         # Auto-generated migration files
├── ipl_scraper/            # Django project settings & URLs
│   ├── settings.py
│   └── urls.py
├── requirements.txt
└── README.md               # ← You are here
```
# Output Screenshots
This the visualization of total runs scored by all players played IPL

![Totalruns](https://github.com/user-attachments/assets/bafd083b-6144-450e-b399-658c4b98c8ec)

This is the data collected terminal image from VS Code ,as the AI Web Scraper collected over 2415 data of all IPL players stats

![Screenshot 2025-05-09 180132](https://github.com/user-attachments/assets/6196747c-d30a-49d3-b185-71464260e62e)

Screenshot of Admin dashboard in PostgreSQL Database

![image](https://github.com/user-attachments/assets/890e6e81-aea3-46c7-80f4-49efc93edf79)


# Troubleshooting
1.relation "stats_playerseasonstat" does not exist
Ensure stats is in INSTALLED_APPS.
Re-run makemigrations & migrate.
Confirm via python manage.py dbshell → \dt.

2.ValueError: invalid literal for int(): "-"
Our _to_int() helper in utils.py now coerces non-digit strings to 0.

3.ChromeDriver issues
Update Chrome & webdriver_manager.
Ensure chromedriver binary matches your Chrome version.

# License
MIT © Madhan
