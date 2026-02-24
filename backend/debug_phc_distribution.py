import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fedhealth.settings')
import django
django.setup()

from api.models import Patient
from django.db.models import Count

# Get unique phc_ids and their counts
results = Patient.objects.values('phc_id').annotate(count=Count('id')).order_by('-count')
print("phc_id distribution:")
for row in results[:20]:
    print(f"  {row['phc_id']}: {row['count']} patients")
