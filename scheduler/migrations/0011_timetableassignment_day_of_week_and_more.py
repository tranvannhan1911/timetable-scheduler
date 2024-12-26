# Generated by Django 5.1.4 on 2024-12-26 16:38

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scheduler', '0010_alter_classteacherschedule_unique_together_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='timetableassignment',
            name='day_of_week',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name='TimetableGenerationHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('generation_history', models.IntegerField(default=1)),
                ('fitness', models.FloatField()),
                ('timetable', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='generations', to='scheduler.timetableschedule')),
            ],
            options={
                'verbose_name': 'Timetable Generation History',
                'verbose_name_plural': 'Timetable Generation Histories',
                'unique_together': {('timetable', 'generation_history')},
            },
        ),
        migrations.AlterUniqueTogether(
            name='timetableassignment',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='timetableassignment',
            name='timetable_generation_history',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='assignments', to='scheduler.timetablegenerationhistory'),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='timetableassignment',
            unique_together={('timetable_generation_history', 'lesson_class', 'day_of_week', 'lesson')},
        ),
        migrations.RemoveField(
            model_name='timetableassignment',
            name='timetable',
        ),
    ]
