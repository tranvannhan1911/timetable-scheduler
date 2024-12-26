# Generated by Django 5.1.4 on 2024-12-21 16:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scheduler', '0006_lesson_timetable_timetableschedule_classes_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='timetableschedule',
            name='generations_limit',
            field=models.PositiveIntegerField(default=100),
        ),
        migrations.AddField(
            model_name='timetableschedule',
            name='population_size',
            field=models.PositiveIntegerField(default=100),
        ),
    ]