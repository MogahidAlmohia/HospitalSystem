from django.shortcuts import render


def home(request):
    if not request.user.is_authenticated:
        from django.shortcuts import redirect
        return redirect("accounts:login")

    return render(request, "accounts/dashboard.html")
