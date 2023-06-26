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
from datetime import timezone
from django.contrib import messages
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from .forms import UserUpdateForm, ProfileUpdateForm, ContactForm, EmailForm, NoteForm
from .models import Contact, Note
from .utils import get_body, parse_email_date, fetch_emails, connect_smtp_server, connect_imap_server


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
    initial_data = {}
    if request.method == 'GET':
        email = request.GET.get('email')
        if email:
            initial_data['email'] = email

    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.user = request.user
            contact.save()
            return redirect('chatterbox_app:contact_list')
    else:
        form = ContactForm(initial=initial_data)

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
def send_email(request, contact_id=None, email_address=None):
    if contact_id:
        contact = get_object_or_404(Contact, id=contact_id, user=request.user)
        recipient_email = contact.email
    elif email_address:
        recipient_email = email_address
        subject = request.GET.get('subject', '')
        message_id = request.GET.get('message_id', '')
    else:
        messages.error(request, 'No recipient specified.')
        return redirect('chatterbox_app:contact_list')

    if request.method == 'POST':
        form = EmailForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            smtp_email = request.user.profile.smtp_email
            smtp_password = request.user.profile.smtp_password

            msg = MIMEMultipart()
            msg['From'] = smtp_email
            msg['To'] = recipient_email
            msg['Subject'] = subject
            msg['In-Reply-To'] = message_id  # Set the 'In-Reply-To' header using the message_id variable
            msg.attach(MIMEText(message, 'plain'))

            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            try:
                server.login(smtp_email, smtp_password)
            except SMTPAuthenticationError:
                messages.error(
                    request, 'SMTP Authentication failed. Please check your SMTP username and password.')
                # Redirect them back to the account page to fix their SMTP settings.
                return redirect('chatterbox_app:my_account')

            text = msg.as_string()
            server.sendmail(smtp_email, recipient_email, text)
            server.quit()
            return redirect('chatterbox_app:contact_list')
    else:
        form = EmailForm(initial={'subject': subject})

    context = {
        'form': form,
        'recipient_email': recipient_email,
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

    cache_key = f'email_inbox:{user.id}'
    emails = cache.get(cache_key)

    if emails is None:
        try:
            smtp_server = connect_smtp_server(smtp_email, smtp_password)
            emails = fetch_emails(user, -30, None)
            smtp_server.quit()
        except (smtplib.SMTPAuthenticationError, imaplib.IMAP4.error):
            messages.error(
                request, 'Failed to retrieve emails. Please check your SMTP username and password.')

        cache.set(cache_key, emails, 300)

    emails.sort(key=lambda e: parse_email_date(e[1]), reverse=True)
    paginator = Paginator(emails, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {'page_obj': page_obj}
    return render(request, 'chatterbox_app/email_inbox.html', context)


@login_required
def load_emails(request):
    user = request.user
    smtp_email = user.profile.smtp_email
    smtp_password = user.profile.smtp_password

    try:
        smtp_server = connect_smtp_server(smtp_email, smtp_password)
        cache_key = f'email_inbox:{user.id}'
        existing_emails = cache.get(cache_key, [])
        num_existing_emails = len(existing_emails)
        total_num_emails = len(fetch_emails(user, None, None))
        start_index = total_num_emails - num_existing_emails - 30
        end_index = start_index + 30
        new_emails = fetch_emails(user, start_index, end_index)
        smtp_server.quit()
    except (smtplib.SMTPAuthenticationError, imaplib.IMAP4.error):
        messages.error(
            request, 'Failed to retrieve emails. Please check your SMTP username and password.')

    all_emails = existing_emails + new_emails
    cache.set(cache_key, all_emails, 300)
    current_page_number = len(all_emails) // 10 + 1

    return redirect(reverse('chatterbox_app:email_inbox') + f'?page={current_page_number - 2}')


@login_required
def email_detail(request, email_uid):
    user = request.user
    smtp_email = user.profile.smtp_email
    smtp_password = user.profile.smtp_password

    try:
        imap_server = connect_imap_server(smtp_email, smtp_password)
        imap_server.select('INBOX')
        _, data = imap_server.fetch(email_uid, '(RFC822)')
        raw_email = data[0][1]
        email = message_from_bytes(raw_email)
        imap_server.close()
        imap_server.logout()
    except smtplib.SMTPAuthenticationError as e:
        messages.error(request, f'SMTP Authentication failed: {str(e)}')
        return redirect('chatterbox_app:email_inbox')
    except imaplib.IMAP4.error as e:
        messages.error(request, f'IMAP error: {str(e)}')
        return redirect('chatterbox_app:email_inbox')
    body = get_body(email)

    context = {
        'email': email,
        'body': body,
    }

    return render(request, 'chatterbox_app/email_detail.html', context)

