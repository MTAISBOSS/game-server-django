from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Player',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False)),
                ('device_id', models.TextField(blank=True, null=True, unique=True)),
                ('phone', models.CharField(blank=True, max_length=20, null=True, unique=True)),
                ('country_code', models.CharField(blank=True, default='', max_length=5)),
                ('platform', models.CharField(blank=True, default='unknown', max_length=20)),
                ('app_version', models.CharField(blank=True, default='1.0.0', max_length=20)),
                ('role', models.CharField(choices=[('player', 'Player'), ('admin', 'Admin'), ('moderator', 'Moderator')], default='player', max_length=20)),
                ('is_banned', models.BooleanField(default=False)),
                ('ban_reason', models.TextField(blank=True, default='')),
                ('is_active', models.BooleanField(default=True)),
                ('is_staff', models.BooleanField(default=False)),
                ('username', models.CharField(blank=True, default='', max_length=150)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('groups', models.ManyToManyField(blank=True, related_name='player_groups', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, related_name='player_permissions', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'db_table': 'players',
            },
        ),
        migrations.AddIndex(
            model_name='player',
            index=models.Index(fields=['device_id'], name='players_device_id_idx'),
        ),
        migrations.AddIndex(
            model_name='player',
            index=models.Index(fields=['phone'], name='players_phone_idx'),
        ),
        migrations.AddIndex(
            model_name='player',
            index=models.Index(fields=['role'], name='players_role_idx'),
        ),
        migrations.AddIndex(
            model_name='player',
            index=models.Index(fields=['is_banned'], name='players_is_banned_idx'),
        ),
        migrations.AddIndex(
            model_name='player',
            index=models.Index(fields=['created_at'], name='players_created_at_idx'),
        ),
        migrations.CreateModel(
            name='OTPCode',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('phone', models.CharField(db_index=True, max_length=20)),
                ('code_hash', models.CharField(max_length=128)),
                ('attempts', models.IntegerField(default=0)),
                ('expires_at', models.DateTimeField()),
                ('verified_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('player', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, to='auth_service.player')),
            ],
            options={
                'db_table': 'otp_codes',
            },
        ),
        migrations.CreateModel(
            name='RefreshTokenRecord',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('token_hash', models.CharField(db_index=True, max_length=64, unique=True)),
                ('device_id', models.TextField(blank=True, default='')),
                ('expires_at', models.DateTimeField()),
                ('revoked_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('player', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='refresh_tokens', to='auth_service.player')),
            ],
            options={
                'db_table': 'refresh_tokens',
            },
        ),
    ]
