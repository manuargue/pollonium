from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, reverse
from django.utils import timezone
from django.contrib import messages

from formtools.wizard.views import SessionWizardView

from .models import Poll, Choice
from .forms import CreatePollGeneralForm, CreatePollChoicesForm, CreatePollSettingsForm


def index(request):
    latest_polls = Poll.objects.filter(pub_date__lte=timezone.now()).order_by('-pub_date')[:10]
    return render(request, 'polls/index.html', {'latest_polls': latest_polls})


def detail(request, pk):
    poll = get_object_or_404(Poll, pk=pk)
    if request.method == 'POST':
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


CREATE_FORMS = [('general', CreatePollGeneralForm),
                ('choices', CreatePollChoicesForm),
                ('settings', CreatePollSettingsForm),
]

CREATE_TEMPLATES = {i[0]: 'polls/create_%s.html' % i[0] for i in CREATE_FORMS}


class CreatePollWizard(SessionWizardView):
    form_list = [CreatePollGeneralForm, CreatePollChoicesForm, CreatePollSettingsForm]

    def get_template_names(self):
        return [CREATE_TEMPLATES[self.steps.current]]

    def done(self, form_list, **kwargs):
        if self.request.method == 'POST':
            poll = self.create_poll()
            return HttpResponseRedirect(reverse('polls:detail', args=(poll.id,)))

    def get_form(self, step=None, data=None, files=None):
        form = super(CreatePollWizard, self).get_form(step, data, files)

        if form.prefix == 'choices':
            # get the choices created at run-time in the client side
            choice_post = {k.strip('choices')[1:]: v
                           for (k, v) in self.get_form_step_data(form).items() if k.startswith('choices-choice')}
            choices = [choice_post[k] for k in sorted(choice_post)]    # sort choices ascending
            if choices:
                form.set_choice_fields(choices)

        return form

    def create_poll(self):
        # get the form fields
        fields = self.get_cleaned_data_for_step('general') or {}
        fields.update(self.get_cleaned_data_for_step('settings') or {})

        # create and save the models
        poll = Poll(title=fields['title'],
                    location=fields['location'],
                    description=fields['description'],
                    author=fields['author'],
                    author_email=fields['author_email'],
                    limit_votes=fields['limit_votes'],
                    votes_max=fields['votes_max'],
                    hidden_poll=fields['hidden_poll'],
                    only_invited=fields['only_invited'],
                    pub_date=timezone.now(),
                    )
        poll.save()

        field_choices = self.get_cleaned_data_for_step('choices')
        choices = [field_choices[k] for k in sorted(field_choices)]
        for c in choices:
            Choice.objects.create(poll=poll, text=c)

        return poll
