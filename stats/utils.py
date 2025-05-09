# stats/utils.py

from django.db import connection, transaction
from .models import PlayerSeasonStat

def ensure_playerseasonstat_table():
    """
    Ensures the stats_playerseasonstat table (and an index) exist.
    Uses raw SQL to create them if missing.
    """
    with connection.cursor() as cursor:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS stats_playerseasonstat (
            id              SERIAL PRIMARY KEY,
            year            SMALLINT        NOT NULL,
            team            VARCHAR(64)     NOT NULL,
            player          VARCHAR(128)    NOT NULL,
            role            VARCHAR(32)     NOT NULL,
            total_runs      INTEGER         NOT NULL,
            total_fours     INTEGER         NOT NULL,
            total_sixes     INTEGER         NOT NULL,
            total_wickets   INTEGER         NOT NULL,
            total_dots      INTEGER         NOT NULL,
            total_fifties   INTEGER         NOT NULL,
            UNIQUE (year, team, player)
        );
        """)
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS stats_year_team_idx
          ON stats_playerseasonstat (year, team);
        """)

def _to_int(value):
    """
    Safely convert a scraped string to int, turning any non-digit or placeholder (e.g. "-") into 0.
    """
    try:
        # Remove commas, whitespace
        s = str(value).replace(',', '').strip()
        return int(s) if s.isdigit() else 0
    except (ValueError, TypeError):
        return 0

def save_stats_batch(records):
    """
    Persist a batch of scraped IPL player-season statistics.

    1. Ensures the target table exists.
    2. Converts each record’s fields into a PlayerSeasonStat instance.
    3. Bulk-inserts with ignore_conflicts to skip duplicates.
    """
    # 1) ensure table & index exist
    ensure_playerseasonstat_table()

    # 2) build model instances
    objs = []
    for rec in records:
        objs.append(PlayerSeasonStat(
            year         = _to_int(rec.get('Year')),
            team         = str(rec.get('Team', '')).strip(),
            player       = str(rec.get('Player', '')).strip(),
            role         = str(rec.get('Role', '')).strip(),
            total_runs   = _to_int(rec.get('Total Runs')),
            total_fours  = _to_int(rec.get('Total Fours')),
            total_sixes  = _to_int(rec.get('Total Sixes')),
            total_wickets= _to_int(rec.get('Total Wickets')),
            total_dots   = _to_int(rec.get('Total Dots')),
            total_fifties= _to_int(rec.get('Total 50s')),
        ))

    # 3) bulk-insert
    with transaction.atomic():
        PlayerSeasonStat.objects.bulk_create(
            objs,
            batch_size=500,
            ignore_conflicts=True  # requires Django ≥2.2
        )
