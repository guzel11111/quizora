from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required


def landing(request):
    return render(request, "main/landing.html")


@login_required
def dashboard(request):
    return render(request, "main/dashboard.html")


def register_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("main:dashboard")  # Изменено с landing на dashboard
    else:
        form = UserCreationForm()

    return render(request, "main/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("main:dashboard")  # Изменено с landing на dashboard
    else:
        form = AuthenticationForm(request)

    return render(request, "main/login.html", {"form": form})


def logout_view(request):
    if request.method == "POST":
        logout(request)
        return redirect("main:landing")