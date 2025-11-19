from django.contrib.auth import get_user_model
from django.conf import settings
from django.db.models.signals import post_migrate
from django.dispatch import receiver
import os

@receiver(post_migrate)
def create_superuser(sender, **kwargs):
    if os.environ.get("RENDER") == "true":
        User = get_user_model()
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser(
                username="admin",
                email="admin@example.com",
                password="ApexAdmin123!"
            )
            print("✓ Superuser created on Render")
