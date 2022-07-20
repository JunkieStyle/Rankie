from django.shortcuts import render
from django.contrib.auth.decorators import login_required


def index(request):
    return render(request, "index.html")


@login_required
def ricardo(request):
    return render(request, "ricardo.html")
