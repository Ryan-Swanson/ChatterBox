# Generated by Django 4.1 on 2023-06-09 23:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chatterbox_app', '0002_profile_address_profile_notes_profile_phone_number'),
    ]

    operations = [
        migrations.RenameField(
            model_name='profile',
            old_name='user',
            new_name='username',
        ),
        migrations.AddField(
            model_name='profile',
            name='first_name',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='last_name',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
