import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fedhealth.settings')
import django
django.setup()

from api.models import User

# Fix all PHC users to have correct phc_id format
users = User.objects.filter(role='PHC_USER')

for user in users:
    old_phc = user.phc_id
    # Convert PHC1 -> PHC_1, PHC2 -> PHC_2, etc.
    if user.phc_id and '_' not in user.phc_id:
        user.phc_id = user.phc_id.replace('PHC', 'PHC_')
        user.save()
        print(f"Updated {user.username}: {old_phc} -> {user.phc_id}")
    else:
        print(f"Skipped {user.username}: already in correct format ({user.phc_id})")

print("\nVerification:")
for user in User.objects.filter(role='PHC_USER'):
    print(f"  {user.username}: phc_id={user.phc_id}")
