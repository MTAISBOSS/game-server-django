from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth_service', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('player', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='profile', serialize=False, to=settings.AUTH_USER_MODEL)),
                ('username', models.CharField(max_length=30, unique=True)),
                ('display_name', models.CharField(blank=True, default='', max_length=60)),
                ('bio', models.TextField(blank=True, default='')),
                ('avatar_id', models.CharField(default='default', max_length=50)),
                ('frame_id', models.CharField(default='default', max_length=50)),
                ('country', models.CharField(blank=True, default='', max_length=3)),
                ('level', models.IntegerField(default=1)),
                ('xp', models.BigIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'profiles',
            },
        ),
        migrations.AddIndex(
            model_name='profile',
            index=models.Index(fields=['username'], name='profiles_username_idx'),
        ),
        migrations.AddIndex(
            model_name='profile',
            index=models.Index(fields=['country'], name='profiles_country_idx'),
        ),
        migrations.AddIndex(
            model_name='profile',
            index=models.Index(fields=['level'], name='profiles_level_idx'),
        ),
        migrations.CreateModel(
            name='PlayerStats',
            fields=[
                ('player', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='stats', serialize=False, to=settings.AUTH_USER_MODEL)),
                ('games_played', models.IntegerField(default=0)),
                ('wins', models.IntegerField(default=0)),
                ('losses', models.IntegerField(default=0)),
                ('win_streak', models.IntegerField(default=0)),
                ('best_streak', models.IntegerField(default=0)),
                ('total_xp', models.BigIntegerField(default=0)),
                ('total_score', models.BigIntegerField(default=0)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'player_stats',
            },
        ),
    ]
