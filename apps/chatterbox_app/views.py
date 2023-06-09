from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .forms import UserUpdateForm, ProfileUpdateForm


def home(request):
    return render(request, 'chatterbox_app/home.html')

@login_required
def my_account(request):
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, instance=request.user.profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'chatterbox_app/my_account.html', context)