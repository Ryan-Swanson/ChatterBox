# Generated by Django 4.1 on 2023-06-10 18:33

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('chatterbox_app', '0007_note'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='note',
            name='date',
        ),
        migrations.AddField(
            model_name='note',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='note',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
