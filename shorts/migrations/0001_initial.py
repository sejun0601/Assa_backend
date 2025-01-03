# Generated by Django 5.1.4 on 2025-01-03 13:43

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Video',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('video_id', models.CharField(max_length=50, unique=True)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('published_at', models.DateTimeField()),
                ('view_count', models.BigIntegerField(default=0)),
                ('like_count', models.BigIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='VideoStatsHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('collected_at', models.DateTimeField(auto_now_add=True)),
                ('view_count', models.BigIntegerField(default=0)),
                ('like_count', models.BigIntegerField(default=0)),
                ('video', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stats_history', to='shorts.video')),
            ],
        ),
    ]
