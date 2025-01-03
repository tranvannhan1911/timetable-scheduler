# Generated by Django 5.1.4 on 2024-12-14 18:41

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scheduler', '0004_alter_lesson_options_subject_lesson_count'),
    ]

    operations = [
        migrations.CreateModel(
            name='TimetableSchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('semester', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='timetables', to='scheduler.semester')),
            ],
            options={
                'verbose_name': 'Timetable Schedule',
                'verbose_name_plural': 'Timetable Schedules',
            },
        ),
        migrations.CreateModel(
            name='TimetableAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lesson', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignments', to='scheduler.lesson')),
                ('lesson_class', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignments', to='scheduler.class')),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignments', to='scheduler.room')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignments', to='scheduler.subject')),
                ('teacher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignments', to='scheduler.teacher')),
                ('timetable', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignments', to='scheduler.timetableschedule')),
            ],
            options={
                'verbose_name': 'Timetable Assignment',
                'verbose_name_plural': 'Timetable Assignments',
                'unique_together': {('timetable', 'lesson_class', 'lesson')},
            },
        ),
    ]
