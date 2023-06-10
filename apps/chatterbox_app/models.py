# chatterbox_app/models.py

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


# User model
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=20, blank=True, null=True)
    last_name = models.CharField(max_length=20, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=500, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=30, blank=True)
    birthdate = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.user.username if self.user else 'No User'

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


# Contact
class Contact(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.EmailField()
    first_name = models.CharField(max_length=20, blank=True, null=True)
    last_name = models.CharField(max_length=20, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)  # New field

    def __str__(self):
        return f'{self.first_name} {self.last_name}' if self.first_name or self.last_name else self.email

# Note
class Note(models.Model):
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='contact_notes')
    note_content = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)  # Added this line
    updated_at = models.DateTimeField(auto_now=True)  # Added this line

    def __str__(self):
        return f'{self.contact.first_name} {self.contact.last_name}: {self.note_content[:20]}...'

