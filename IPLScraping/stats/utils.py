from django.db import transaction
from stats.models import PlayerStat

def save_stats_batch(records, batch_size=2000):
    objs = [PlayerStat(**rec) for rec in records]
    with transaction.atomic():
        for i in range(0, len(objs), batch_size):
            PlayerStat.objects.bulk_create(objs[i:i+batch_size], batch_size=batch_size)
