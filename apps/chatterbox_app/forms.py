# chatterbox_app/forms.py

from allauth.account.forms import SignupForm
from django import forms
from django.contrib.auth.models import User
from .models import Profile, Contact, Note


class CustomSignupForm(SignupForm):
    first_name = forms.CharField(max_length=30, label='First Name')
    last_name = forms.CharField(max_length=30, label='Last Name')
    username = forms.CharField(max_length=30, label='Username')
    phone_number = forms.CharField(max_length=20, label='Phone Number')

    def save(self, request):
        user = super().save(request)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.username = self.cleaned_data['username']
        user.save()

        # Manually create the profile if it doesn't exist.
        Profile.objects.get_or_create(user=user, defaults={'phone_number': self.cleaned_data['phone_number']})

        return user


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username']
        widgets = {
            'username': forms.TextInput(attrs={'maxlength': 100}),
        }

class ProfileUpdateForm(forms.ModelForm):
    smtp_password = forms.CharField(widget=forms.PasswordInput, required=False)

    class Meta:
        model = Profile
        fields = ['phone_number', 'address', 'notes', 'bio', 'location', 'birthdate', 'smtp_email', 'smtp_password']

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'notes']


class EmailForm(forms.Form):
    subject = forms.CharField(max_length=200)
    message = forms.CharField(widget=forms.Textarea)


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['note_content', 'contact']  # 'content' changed to 'note_content'
        widgets = {'contact': forms.HiddenInput()}  # make 'contact' field hidden