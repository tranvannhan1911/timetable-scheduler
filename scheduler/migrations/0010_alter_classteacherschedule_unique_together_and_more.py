# Generated by Django 5.1.4 on 2024-12-25 17:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scheduler', '0009_classteacherschedule'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='classteacherschedule',
            unique_together={('subject', 'teacher', 'lesson_class')},
        ),
        migrations.RemoveField(
            model_name='classteacherschedule',
            name='semester',
        ),
    ]