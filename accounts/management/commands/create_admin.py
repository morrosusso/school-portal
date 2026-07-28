"""
accounts/management/commands/create_admin.py

Free Render instances don't include Shell access, so there's no
`python manage.py createsuperuser` prompt available. This command
does the same job non-interactively, reading credentials from
environment variables, and is safe to run on every single deploy
(build.sh calls it automatically) because it only creates the
account the FIRST time -- if it already exists, it does nothing.

Set these on Render -> your service -> Environment:
    DJANGO_SUPERUSER_USERNAME
    DJANGO_SUPERUSER_EMAIL
    DJANGO_SUPERUSER_PASSWORD

If any of the three are missing, the command just skips quietly so
local development (where you use the normal interactive
createsuperuser) is unaffected.
"""

import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Role


class Command(BaseCommand):
    help = "Creates a superuser from DJANGO_SUPERUSER_* environment variables, if one doesn't already exist."

    def handle(self, *args, **options):
        User = get_user_model()

        username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

        if not username or not password:
            self.stdout.write("DJANGO_SUPERUSER_USERNAME / PASSWORD not set -- skipping auto-admin creation.")
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write(f"Superuser '{username}' already exists -- skipping.")
            return

        User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            role=Role.IT_SUPPORT,
        )
        self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' created successfully."))
