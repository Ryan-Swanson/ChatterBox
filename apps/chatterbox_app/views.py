from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.generic.detail import DetailView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from .forms import UserUpdateForm, ProfileUpdateForm, ContactForm, EmailForm, NoteForm
from .models import Contact, Note

def home(request):
    return render(request, 'chatterbox_app/home.html')

@login_required
def my_account(request):
    user = request.user
    profile = user.profile

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = ProfileUpdateForm(request.POST, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()

            smtp_password = profile_form.cleaned_data.get('smtp_password')
            if smtp_password:  # Check if the user provided a new password
                profile.smtp_password = smtp_password

            profile.save()
    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = ProfileUpdateForm(instance=profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'chatterbox_app/my_account.html', context)


# Contact Views
@login_required
def contact_list(request):
    contacts = Contact.objects.filter(user=request.user)
    return render(request, 'chatterbox_app/contact_list.html', {'contacts': contacts})

@login_required
def contact_create(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.user = request.user
            contact.save()
            return redirect('chatterbox_app:contact_list')
    else:
        form = ContactForm()

    return render(request, 'chatterbox_app/contact_form.html', {'form': form})

@login_required
def contact_delete(request, pk):
    contact = get_object_or_404(Contact, pk=pk, user=request.user)

    if request.method == 'POST':
        contact.delete()
        return redirect('chatterbox_app:contact_list')

    return render(request, 'chatterbox_app/contact_confirm_delete.html', {'contact': contact})

@login_required
def contact_update(request, pk):
    contact = get_object_or_404(Contact, pk=pk, user=request.user)
    if request.method == 'POST':
        form = ContactForm(request.POST, instance=contact)
        if form.is_valid():
            form.save()
            return redirect('chatterbox_app:contact_list')
    else:
        form = ContactForm(instance=contact)

    return render(request, 'chatterbox_app/contact_form.html', {'form': form})

@login_required
def send_email(request, contact_id):
    contact = get_object_or_404(Contact, id=contact_id, user=request.user)

    if request.method == 'POST':
        form = EmailForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            # Use the SMTP credentials from user's profile instead
            smtp_email = request.user.profile.smtp_email
            smtp_password = request.user.profile.smtp_password  # You will need to decrypt this

            # Create message
            msg = MIMEMultipart()
            msg['From'] = smtp_email
            msg['To'] = contact.email
            msg['Subject'] = subject
            msg.attach(MIMEText(message, 'plain'))

            # Setup server
            server = smtplib.SMTP('smtp.gmail.com', 587)  # assuming gmail
            server.starttls()
            server.login(smtp_email, smtp_password)

            # Send the email
            text = msg.as_string()
            server.sendmail(smtp_email, contact.email, text)
            server.quit()

            return redirect('chatterbox_app:contact_list')
    else:
        form = EmailForm()

    context = {
        'form': form,
        'contact': contact,
    }
    return render(request, 'chatterbox_app/email_form.html', context)



@login_required
def note_create(request, contact_id):
    contact = get_object_or_404(Contact, id=contact_id, user=request.user)
    if request.method == 'POST':
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.contact = contact
            note.save()
            return redirect('chatterbox_app:contact_detail', contact.id)
    else:
        form = NoteForm()
    return render(request, 'chatterbox_app/note_form.html', {'form': form, 'contact': contact})

class ContactDetailView(LoginRequiredMixin, DetailView):
    model = Contact
    template_name = 'chatterbox_app/contact_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['notes'] = self.object.contact_notes.all()
        return context

@login_required
def add_note(request, pk):
    contact = get_object_or_404(Contact, pk=pk)

    if request.method == 'POST':
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.contact = contact
            note.save()
            return redirect('chatterbox_app:contact_detail', pk=contact.pk)
    else:
        form = NoteForm(initial={'contact': contact}) 

    return render(request, 'chatterbox_app/add_note.html', {'form': form})

@login_required
def note_edit(request, contact_pk, pk):
    note = get_object_or_404(Note, pk=pk, contact__user=request.user)

    if request.method == 'POST':
        form = NoteForm(request.POST, instance=note)
        if form.is_valid():
            form.save()
            return redirect('chatterbox_app:contact_detail', pk=contact_pk)
    else:
        form = NoteForm(instance=note)

    return render(request, 'chatterbox_app/note_form.html', {'form': form})

@login_required
def note_delete(request, contact_pk, pk):
    note = get_object_or_404(Note, pk=pk, contact__user=request.user)

    if request.method == 'POST':
        note.delete()
        return redirect('chatterbox_app:contact_detail', pk=contact_pk)

    return render(request, 'chatterbox_app/note_confirm_delete.html', {'note': note})