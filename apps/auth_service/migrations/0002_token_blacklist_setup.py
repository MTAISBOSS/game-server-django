from django.db import migrations


class Migration(migrations.Migration):
    """
    Empty migration that ensures rest_framework_simplejwt token blacklist
    and django admin both wait for our Player model to exist first.
    """
    dependencies = [
        ('auth_service', '0001_initial'),
        ('token_blacklist', '0001_initial'),
    ]

    operations = []
