#!/usr/bin/env python
"""Test database connectivity"""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fedhealth.settings')

import django
django.setup()

from api.models import Patient

print(f"✅ Total patients in database: {Patient.objects.count()}")
print(f"✅ Sample PHC count (PHC1): {Patient.objects.filter(phc_id='PHC1').count()}")
print("✅ Database is ready for API requests!")
