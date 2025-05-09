from django.core.management.base import BaseCommand
from django.db import transaction
from stats.models import PlayerStat
from stats.models import PlayerStatArchive  # define this model similarly

class Command(BaseCommand):
    help = 'Archive old player stats'

    def handle(self, *args, **options):
        cutoff = 2018
        qs = PlayerStat.objects.filter(year__lte=cutoff)
        batch = 1000
        while qs.exists():
            with transaction.atomic():
                chunk = list(qs[:batch])
                archives = [PlayerStatArchive(**obj.__dict__) for obj in chunk]
                PlayerStatArchive.objects.bulk_create(archives)
                PlayerStat.objects.filter(pk__in=[o.pk for o in chunk]).delete()
            self.stdout.write(f"Archived {len(chunk)} records")
