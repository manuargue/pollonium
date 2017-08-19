from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, reverse
from django.utils import timezone
from django.contrib import messages

from .models import Poll, Choice


def index(request):
    latest_polls = Poll.objects.filter(pub_date__lte=timezone.now()).order_by('-pub_date')[:10]
    return render(request, 'polls/index.html', {'latest_polls': latest_polls})


def detail(request, pk):
    poll = get_object_or_404(Poll, pk=pk)
    if request.POST:
        try:
            # get the pk of the choice voted
            selected_choice = poll.choice_set.get(pk=request.POST['choice'])
        except (KeyError, Choice.DoesNotExist):
            # redisplay the view with error message
            messages.add_message(request, messages.ERROR, 'Ops! Error processing your vote. Please, try again!')
        else:
            # submit the vote
            selected_choice.votes += 1
            selected_choice.save()
            messages.add_message(request, messages.SUCCESS, 'Your vote has been submitted. Thanks for voting!')
            return HttpResponseRedirect(reverse('polls:detail', args=(poll.id,)))

    messages.get_messages(request).used = True
    return render(request, 'polls/details.html', {'poll': poll})


def create_general(request):
    return render(request, 'polls/create_general.html')


def create_choices(request):
    return render(request, 'polls/create_choices.html')


def create_settings(request):
    return render(request, 'polls/create_settings.html')


def results(request):
    return render(request, 'polls/results.html')