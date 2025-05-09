# stats/models.py

from django.db import models

class PlayerSeasonStat(models.Model):
    """
    Stores aggregated IPL stats for each player in each season.
    """

    ROLE_CHOICES = [
        ('Batsman', 'Batsman'),
        ('Bowler', 'Bowler'),
        ('All-rounder', 'All-rounder'),
        ('Wicket-keeper', 'Wicket-keeper'),
    ]

    year = models.PositiveSmallIntegerField(db_index=True)
    team = models.CharField(max_length=64, db_index=True)
    player = models.CharField(max_length=128, db_index=True)
    role = models.CharField(max_length=32, choices=ROLE_CHOICES)
    total_runs = models.PositiveIntegerField()
    total_fours = models.PositiveIntegerField()
    total_sixes = models.PositiveIntegerField()
    total_wickets = models.PositiveIntegerField()
    total_dots = models.PositiveIntegerField()
    total_fifties = models.PositiveIntegerField()

    class Meta:
        unique_together = (('year', 'team', 'player'),)
        indexes = [
            models.Index(fields=['year', 'team']),
        ]
        ordering = ['-year', 'team', 'player']

    def __str__(self):
        return f"{self.player} ({self.team}, {self.year})"
