# Generated by Django 5.1.4 on 2024-12-14 17:47

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Grade',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('level', models.IntegerField()),
            ],
            options={
                'verbose_name': 'Grade',
                'verbose_name_plural': 'Grades',
            },
        ),
        migrations.CreateModel(
            name='Lesson',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session', models.CharField(choices=[('morning', 'Morning'), ('afternoon', 'Afternoon'), ('evening', 'Evening')], max_length=10)),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('index', models.IntegerField()),
            ],
            options={
                'verbose_name': 'Session',
                'verbose_name_plural': 'Sessions',
            },
        ),
        migrations.CreateModel(
            name='Room',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('room_id', models.CharField(max_length=10, unique=True)),
                ('name', models.CharField(max_length=100)),
            ],
            options={
                'verbose_name': 'Room',
                'verbose_name_plural': 'Rooms',
            },
        ),
        migrations.CreateModel(
            name='Semester',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('year', models.CharField(max_length=10)),
                ('index', models.IntegerField()),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
            ],
            options={
                'verbose_name': 'Semester',
                'verbose_name_plural': 'Semesters',
            },
        ),
        migrations.CreateModel(
            name='Teacher',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mgv', models.CharField(max_length=10, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('min_lessons', models.IntegerField(default=0)),
                ('max_lessons', models.IntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Teacher',
                'verbose_name_plural': 'Teachers',
            },
        ),
        migrations.CreateModel(
            name='Class',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('class_id', models.CharField(max_length=10, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('grade', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='classes', to='scheduler.grade')),
                ('main_room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='classes', to='scheduler.room')),
            ],
            options={
                'verbose_name': 'Class',
                'verbose_name_plural': 'Classes',
            },
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mmh', models.CharField(max_length=10, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('grade', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subjects', to='scheduler.grade')),
            ],
            options={
                'verbose_name': 'Subject',
                'verbose_name_plural': 'Subjects',
            },
        ),
        migrations.CreateModel(
            name='SubjectSchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lesson_count', models.IntegerField()),
                ('semester', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='schedules', to='scheduler.semester')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='schedules', to='scheduler.subject')),
            ],
            options={
                'verbose_name': 'Subject Schedule',
                'verbose_name_plural': 'Subject Schedules',
                'unique_together': {('subject', 'semester')},
            },
        ),
        migrations.CreateModel(
            name='TeacherSubject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='teachers', to='scheduler.subject')),
                ('teacher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subjects', to='scheduler.teacher')),
            ],
            options={
                'verbose_name': 'Teacher Subject',
                'verbose_name_plural': 'Teacher Subjects',
                'unique_together': {('teacher', 'subject')},
            },
        ),
    ]