from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, reverse, redirect
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.db import transaction

from formtools.wizard.views import SessionWizardView

from .models import Poll, Choice, Vote
from .forms import CreatePollGeneralForm, CreatePollChoicesForm, CreatePollSettingsForm, SignUpForm


def index(request):
    latest_polls = Poll.objects.filter(pub_date__lte=timezone.now()).order_by('-pub_date')[:10]
    return render(request, 'polls/index.html', {'latest_polls': latest_polls})


def results(request):
    return render(request, 'polls/index.html')


def detail(request, pk):
    poll = get_object_or_404(Poll, pk=pk)
    if request.POST:
        try:
            # get the pk of the choice voted
            selected_choice = poll.choice_set.get(pk=request.POST['choice'])
        except (KeyError, Choice.DoesNotExist):
            # redisplay the view with error message
            messages.error(request, 'Ops! Error processing your vote. Please, try again!')
        else:
            # check for single vote
            if poll.single_vote and poll.user_already_vote(request.user):
                messages.error(request, 'You only can vote once in this poll!')
            # check if the user has already vote this choice
            elif selected_choice.is_voted_by(request.user):
                messages.error(request, 'You cannot vote again this option. Please select another one and try again!')
            # check for poll vote limit per choice
            elif selected_choice.is_full():
                messages.error(request, 'The selected option cannot be voted anymore!')
            else:
                # submit the vote
                Vote.objects.create(poll=poll, choice=selected_choice, user=request.user)
                messages.success(request, 'Your vote has been submitted. Thanks for voting!')
            return HttpResponseRedirect(reverse('polls:detail', args=(poll.id,)))

    messages.get_messages(request).used = True
    return render(request, 'polls/details.html', {'poll': poll, 'users': poll.get_users()})


CREATE_FORMS = [('general', CreatePollGeneralForm),
                ('choices', CreatePollChoicesForm),
                ('settings', CreatePollSettingsForm),
]

CREATE_TEMPLATES = {i[0]: 'polls/create_%s.html' % i[0] for i in CREATE_FORMS}


class CreatePollWizard(SessionWizardView):
    form_list = [CreatePollGeneralForm, CreatePollChoicesForm, CreatePollSettingsForm]

    def done(self, form_list, **kwargs):
        if self.request.POST:
            poll = self.create_poll()
            return HttpResponseRedirect(reverse('polls:detail', args=(poll.id,)))

    def get_template_names(self):
        return [CREATE_TEMPLATES[self.steps.current]]

    def get_form(self, step=None, data=None, files=None):
        form = super(CreatePollWizard, self).get_form(step, data, files)

        if form.prefix == 'choices':
            # get the choices created at run-time in the client side
            choice_post = {k.strip('choices')[1:]:v
                           for (k, v) in self.get_form_step_data(form).items() if k.startswith('choices-choice')}
            choices = [choice_post[k] for k in sorted(choice_post)]    # sort choices ascending
            form.set_choice_fields(choices or ['',])

        return form

    def get_form_fields(self):
        # fields for poll model
        poll_model_f = self.get_cleaned_data_for_step('general') or {}
        poll_model_f.update(self.get_cleaned_data_for_step('settings') or {})

        # field for choice model
        choice_model_f = self.get_cleaned_data_for_step('choices') or {}
        choice_model_f = [choice_model_f[k] for k in sorted(choice_model_f)]

        return poll_model_f, choice_model_f

    def create_poll(self):
        poll_f, choice_f = self.get_form_fields()

        # create and save the models
        poll = Poll.objects.create(
            title=poll_f['title'],
            location=poll_f['location'],
            description=poll_f['description'],
            author=poll_f['author'],
            author_email=poll_f['author_email'],
            single_vote=poll_f['single_vote'],
            limit_votes=poll_f['limit_votes'],
            votes_max=poll_f['votes_max'],
            hidden_poll=poll_f['hidden_poll'],
            only_invited=poll_f['only_invited'],
            pub_date=timezone.now(),
        )
        poll.save()

        for c in choice_f:
            Choice.objects.create(poll=poll, text=c)

        return poll


class EditPollWizard(CreatePollWizard):

    def done(self, form_list, **kwargs):
        if self.request.POST:
            poll = self.update_poll(self.kwargs['pk'])
            return HttpResponseRedirect(reverse('polls:detail', args=(poll.id,)))

    def get_form_initial(self, step):
        pk = self.kwargs['pk']
        if step == 'general' or step == 'settings':
            initial = Poll.objects.filter(pk=pk).values()[0]
        elif step == 'choices':
            ch = Poll.objects.get(pk=pk).choice_set.values()
            initial = {'choice%i'%i:ch[i-1]['text'] for i in range(1,len(ch)+1)}

        return self.initial_dict.get(step, initial or {})

    def update_poll(self, pk):
        poll_f, choice_f = self.get_form_fields()

        pq = Poll.objects.filter(pk=pk)
        pq.update(
            title=poll_f['title'],
            location=poll_f['location'],
            description=poll_f['description'],
            author=poll_f['author'],
            author_email=poll_f['author_email'],
            single_vote=poll_f['single_vote'],
            limit_votes=poll_f['limit_votes'],
            votes_max=poll_f['votes_max'],
            hidden_poll=poll_f['hidden_poll'],
            only_invited=poll_f['only_invited'],
            pub_date=timezone.now(),
        )

        # delete previous choice entries
        poll = pq.first()
        for c in poll.choice_set.iterator():
            c.delete()
        # add new choices
        for c in choice_f:
            Choice.objects.create(poll=poll, text=c)

        poll.save()
        return poll

    def get_form(self, step=None, data=None, files=None):
        form = super(EditPollWizard, self).get_form(step, data, files)

        if form.prefix == 'choices':
            post_data = self.get_form_step_data(form)
            if self.kwargs['pk'] and not post_data:
                # first time entering the edit view, get form initial values
                choices_i = self.get_form_initial('choices')
                choices = [choices_i[k] for k in sorted(choices_i)]         # sort choices ascending
                form.set_choice_fields(choices)

        return form

    def get_context_data(self, form, **kwargs):
        context = super(EditPollWizard, self).get_context_data(form=form, **kwargs)
        context.update({'editor_mode': True})
        return context


@transaction.atomic
def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('polls:index')
    else:
        form = SignUpForm()
    return render(request, 'polls/signup.html', {'form': form, 'user':request.user})