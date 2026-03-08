import os
import django
from decouple import config

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'daythree.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

username = config('DJANGO_SUPERUSER_USERNAME')
email = config('DJANGO_SUPERUSER_EMAIL')
password = config('DJANGO_SUPERUSER_PASSWORD')

if not  User.objects.filter(email=email).exists():
    User.objects.create_superuser(email, password)
    print(f"Superuser {email} created successfully.")
else:
    print(f"Superuser {email} already exists.")