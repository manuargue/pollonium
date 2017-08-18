from django.shortcuts import render
from django.utils import timezone

from .models import Poll


def index(request):
    latest_polls = Poll.objects.filter(pub_date__lte=timezone.now()).order_by('-pub_date')[:10]
    return render(request, 'polls/index.html', {'latest_polls': latest_polls})


def detail(request):
    return render(request, 'polls/details.html')