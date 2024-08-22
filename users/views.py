from django.shortcuts import render, redirect
from django.contrib.auth import login,authenticate,logout
from .models import Profiles
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserForm
from django.core.mail import send_mail
from django.conf import settings

def LoginPage(request):

    if request.user.is_authenticated:
        return redirect('logout')

    if request.method == 'POST':
        # Process form data
        username = request.POST['username']
        password = request.POST['password']
        
        try:
            user = User.objects.get(username=username)
        except: 
            messages.error(request, 'Username does not exist')

        user = authenticate(request, username = username, password = password)

        if user is not None:
            login(request,user)
            messages.success(request, 'Login Successful')
            return redirect('live_news')

        else:
            messages.error(request, 'Password is incorrect')

    return render(request, 'users/login.html')

@login_required(login_url='login')
def LogoutPage(request):
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'Logout Successful')
        return redirect('login')
    return render(request, 'users/logout.html')


def SignupPage(request):
    form = UserForm()
    context = {'form':form}
    if request.method == 'POST':
        # Process form data
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save(commit = False)
            user.username = user.username.lower()
            user.save()


            subject = 'Welcome to Market Tracker'
            message = 'You have successfully signed up for our services. I hope you are ready to beat the markets'

            messages.success(request, 'Signup Successful')
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )
            login(request,user)
            print('registration done')

            return redirect('live_news')
    
    else :
        messages.error(request, 'Signup Failed')

    return render(request, 'users/signup.html',context)