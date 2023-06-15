from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.generic.detail import DetailView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.urls import reverse
from django.core.cache import cache
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import smtplib
import imaplib
from email import message_from_bytes
from smtplib import SMTPAuthenticationError
from django.contrib import messages
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
            profile_form.save()

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
            smtp_email = request.user.profile.smtp_email
            smtp_password = request.user.profile.smtp_password

            msg = MIMEMultipart()
            msg['From'] = smtp_email
            msg['To'] = contact.email
            msg['Subject'] = subject
            msg.attach(MIMEText(message, 'plain'))

            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            try:
                server.login(smtp_email, smtp_password)
            except SMTPAuthenticationError:
                messages.error(request, 'SMTP Authentication failed. Please check your SMTP username and password.')
                return redirect('chatterbox_app:my_account')  # Redirect them back to the account page to fix their SMTP settings.

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

@login_required
def email_inbox(request):
    user = request.user
    smtp_email = user.profile.smtp_email
    smtp_password = user.profile.smtp_password

    # Check if the emails are already cached
    cache_key = f'email_inbox:{user.id}'
    emails = cache.get(cache_key)

    if emails is None:
        try:
            # Connect to the SMTP server
            smtp_server = smtplib.SMTP('smtp.gmail.com', 587)
            smtp_server.starttls()
            smtp_server.login(smtp_email, smtp_password)

            # Connect to the IMAP server
            imap_server = imaplib.IMAP4_SSL('imap.gmail.com')
            imap_server.login(smtp_email, smtp_password)
            imap_server.select('INBOX')

            # Retrieve the email UIDs
            _, uids = imap_server.search(None, 'ALL')
            email_ids = uids[0].split()

            # Limit the initial number of emails
            email_ids = email_ids[-20:]

            emails = []
            for email_id in email_ids:
                _, data = imap_server.fetch(email_id, '(RFC822)')
                raw_email = data[0][1]
                email = message_from_bytes(raw_email)
                emails.append(email)

            # Sort emails by timestamp in descending order
            emails.sort(key=lambda e: e['Date'], reverse=True)

            imap_server.close()
            imap_server.logout()

            smtp_server.quit()
        except (smtplib.SMTPAuthenticationError, imaplib.IMAP4.error):
            messages.error(request, 'Failed to retrieve emails. Please check your SMTP username and password.')

        # Cache the emails for 5 minutes
        cache.set(cache_key, emails, 300)

    # Paginate the emails
    paginator = Paginator(emails, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj
    }
    return render(request, 'chatterbox_app/email_inbox.html', context)

@login_required
def load_emails(request):
    user = request.user
    smtp_email = user.profile.smtp_email
    smtp_password = user.profile.smtp_password

    try:
        # Connect to the SMTP server
        smtp_server = smtplib.SMTP('smtp.gmail.com', 587)
        smtp_server.starttls()
        smtp_server.login(smtp_email, smtp_password)

        # Connect to the IMAP server
        imap_server = imaplib.IMAP4_SSL('imap.gmail.com')
        imap_server.login(smtp_email, smtp_password)
        imap_server.select('INBOX')

        # Retrieve the email UIDs
        _, uids = imap_server.search(None, 'ALL')
        email_ids = uids[0].split()
        total_num_emails = len(email_ids)

        # Get the number of emails already loaded
        cache_key = f'email_inbox:{user.id}'
        existing_emails = cache.get(cache_key, [])
        num_existing_emails = len(existing_emails)
        print(f'\n\n\n\n{num_existing_emails=}')

        # Limit the number of emails to load
        num_emails_to_load = 20
        start_index = total_num_emails - num_existing_emails- num_emails_to_load
        end_index = start_index + num_emails_to_load

        # Retrieve the new emails
        email_ids_to_load = email_ids[start_index:end_index]
        emails = []
        for email_id in email_ids_to_load:
            _, data = imap_server.fetch(email_id, '(RFC822)')
            raw_email = data[0][1]
            email = message_from_bytes(raw_email)
            emails.append(email)

        # Sort emails by timestamp in descending order
        emails.sort(key=lambda e: e['Date'], reverse=True)

        imap_server.close()
        imap_server.logout()

        smtp_server.quit()
    except (smtplib.SMTPAuthenticationError, imaplib.IMAP4.error):
        messages.error(request, 'Failed to retrieve emails. Please check your SMTP username and password.')

    # Append the new emails to the existing emails
    all_emails = existing_emails + emails

    # Cache the updated emails for 5 minutes
    cache.set(cache_key, all_emails, 300)
    current_page_number = len(all_emails) // 10 + 1

    return redirect(reverse('chatterbox_app:email_inbox') + f'?page={current_page_number - 2}')
