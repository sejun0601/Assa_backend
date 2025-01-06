# Generated by Django 5.1.4 on 2025-01-05 12:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0002_problem_rename_created_at_match_started_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='match',
            name='status',
            field=models.CharField(choices=[('ongoing', 'Ongoing'), ('finished', 'Finished'), ('forfeited', 'Forfeited'), ('draw', 'Draw')], default='ongoing', max_length=10),
        ),
    ]