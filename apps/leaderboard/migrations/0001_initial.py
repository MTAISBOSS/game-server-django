from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth_service', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Season',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('starts_at', models.DateTimeField()),
                ('ends_at', models.DateTimeField()),
                ('is_active', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'seasons',
                'ordering': ['-starts_at'],
            },
        ),
        migrations.CreateModel(
            name='LeaderboardEntry',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('score', models.BigIntegerField(default=0)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('player', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='leaderboard_entries', to=settings.AUTH_USER_MODEL)),
                ('season', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entries', to='leaderboard.season')),
            ],
            options={
                'db_table': 'leaderboard_entries',
                'unique_together': {('player', 'season')},
            },
        ),
        migrations.AddIndex(
            model_name='leaderboardentry',
            index=models.Index(fields=['season', '-score'], name='lb_season_score_idx'),
        ),
        migrations.AddIndex(
            model_name='leaderboardentry',
            index=models.Index(fields=['player'], name='lb_player_idx'),
        ),
        migrations.CreateModel(
            name='ScoreHistory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('match_id', models.CharField(blank=True, default='', max_length=100)),
                ('delta', models.BigIntegerField()),
                ('score_after', models.BigIntegerField()),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('player', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='score_history', to=settings.AUTH_USER_MODEL)),
                ('season', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='leaderboard.season')),
            ],
            options={
                'db_table': 'score_history',
            },
        ),
        migrations.AddIndex(
            model_name='scorehistory',
            index=models.Index(fields=['player', 'season', '-created_at'], name='sh_player_season_idx'),
        ),
    ]
