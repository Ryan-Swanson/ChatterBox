# Generated by Django 4.1 on 2023-06-09 23:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chatterbox_app', '0003_rename_user_profile_username_profile_first_name_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='profile',
            old_name='username',
            new_name='user',
        ),
    ]
