from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, reverse, redirect
from django.core.urlresolvers import reverse_lazy
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView

from formtools.wizard.views import SessionWizardView

from .models import Poll, Choice, Vote
from .forms import CreatePollGeneralForm, CreatePollChoicesForm, CreatePollSettingsForm, SignUpForm


class IndexView(ListView):
    """
    Display the polls index showing the ten latest :model:`polls.Poll` published.
    """
    template_name = 'polls/index.html'
    context_object_name = 'latest_polls'

    def get_queryset(self):
        """
        :return: query set with the ten latest no-hidden polls published
        """
        return Poll.objects.filter(pub_date__lte=timezone.now(), hidden_poll=False).order_by('-pub_date')[:10]


# TODO implement as class-based view
def detail(request, pk):
    """
    Display the partial results for a given :model:`polls.Poll`. Allow the user to vote for any of the options and
    display the current submitted votes.

    :param request: HTTP request
    :param pk: :model:`polls.Poll` instance primary-key
    :return: HTTP response
    """
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


""" Forms used by each step of the :view:`polls.CreatePollWizard` """
CREATE_FORMS = [('general', CreatePollGeneralForm),
                ('choices', CreatePollChoicesForm),
                ('settings', CreatePollSettingsForm),
]

""" Templates used by each step of the :view:`polls.CreatePollWizard` """
CREATE_TEMPLATES = {i[0]: 'polls/create_%s.html' % i[0] for i in CREATE_FORMS}


class CreatePollWizard(LoginRequiredMixin, SessionWizardView):
    """
    Multi-step form view to create a :model:`polls.Poll`. Implements a server-side session. User must be logged-in to
    access this view.
    """
    login_url = 'polls:login'
    form_list = [CreatePollGeneralForm, CreatePollChoicesForm, CreatePollSettingsForm]

    def done(self, form_list, **kwargs):
        """
        Process form data after all steps are completed. Create a new :model:`polls.Poll` instance using the submitted
        data.

        :param form_list: form instances for each step
        :param kwargs: arbitrary keyword arguments
        :return: HTTP redirect to the created :model:`polls.Poll` detail view
        """
        if self.request.POST:
            poll = self.create_poll()
            return HttpResponseRedirect(reverse('polls:detail', args=(poll.id,)))

    def get_template_names(self):
        """
        :return: the template name for the current step
        """
        return [CREATE_TEMPLATES[self.steps.current]]

    def get_form(self, step=None, data=None, files=None):
        """
        Construct the form for a given step. If no step is defined, the current step will be determined automatically.
        The form will be initialized using the data argument to prefill the new form.


        :param step: step to process or None for current step
        :param data: data to initialize the form instance
        :param files: files to initialize the form instance
        :return: form instance for the given step
        """
        form = super(CreatePollWizard, self).get_form(step, data, files)

        if form.prefix == 'choices':
            # get the choices created at run-time in the client side
            choice_post = {k.strip('choices')[1:]:v
                           for (k, v) in self.get_form_step_data(form).items() if k.startswith('choices-choice')}
            # sort choices ascending and add them to the form instance
            choices = [choice_post[k] for k in sorted(choice_post)]
            form.set_choice_fields(choices or ['',])

        return form

    def get_form_fields(self):
        """
        :return: a 2-item tuple containing the form fields that correspond to the :model:`polls.Poll` model at first
        index, and :model:`polls.Choice` model at second index
        """
        # fields for poll model
        poll_model_f = self.get_cleaned_data_for_step('general') or {}
        poll_model_f.update(self.get_cleaned_data_for_step('settings') or {})

        # field for choice model
        choice_model_f = self.get_cleaned_data_for_step('choices') or {}
        choice_model_f = [choice_model_f[k] for k in sorted(choice_model_f)]

        return poll_model_f, choice_model_f

    def create_poll(self):
        """
        Create a :model:`polls.Poll` instance with the data submitted in all steps.

        :return: the created :model:`polls.Poll` instance
        """
        poll_f, choice_f = self.get_form_fields()

        # create and save the models
        poll = Poll.objects.create(
            title=poll_f['title'],
            location=poll_f['location'],
            description=poll_f['description'],
            author=self.request.user,
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
    """
    Multi-step form view to edit the :model:`polls.Poll` content. Implements a server-side session. User must be
    logged-in to access this view.
    """
    def done(self, form_list, **kwargs):
        """
        Process form data after all steps are completed. Updates a :model:`polls.Poll` instance with the submitted data.

        :param form_list: form instances for each step
        :param kwargs: arbitrary keyword arguments
        :return: HTTP redirect to the created :model:`polls.Poll` detail view
        """
        if self.request.POST:
            poll = self.update_poll(self.kwargs['pk'])
            return HttpResponseRedirect(reverse('polls:detail', args=(poll.id,)))

    def get_form_initial(self, step):
        """
        Return a dictionary which will be passed as the initial argument when instantiating the form for the given
        step. Uses the :model:`polls.Poll` primary-key to get the poll instance.

        :param step: selected step
        :return: a dictionary containing the initialize data for the form of the given step
        """
        pk = self.kwargs['pk']
        if step == 'general' or step == 'settings':
            initial = Poll.objects.filter(pk=pk).values()[0]
        elif step == 'choices':
            ch = Poll.objects.get(pk=pk).choice_set.values()
            initial = {'choice%i' % i: ch[i-1]['text'] for i in range(1, len(ch)+1)}

        return self.initial_dict.get(step, initial or {})

    def update_poll(self, pk):
        """
        Update a :model:`polls.Poll` instance for the given primary-key, using the data submitted in all steps.
        The :model:`polls.Choice` set for the given :model:`polls.Poll` is cleared and then filled again with the new
        submitted options.

        :param pk: :model:`polls.Poll` primary-key
        :return: the updated :model:`polls.Poll` instance
        """
        poll_f, choice_f = self.get_form_fields()

        pq = Poll.objects.filter(pk=pk)
        pq.update(
            title=poll_f['title'],
            location=poll_f['location'],
            description=poll_f['description'],
            author=self.request.user,
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
        """
        Construct the form for a given step. If no step is defined, the current step will be determined automatically.
        The form will be initialized using the data argument to prefill the new form.

        For :model:`polls.Choice` step, the form instance is initialized with the fields created at dynamically at
        run-time in the client side.

        :param step: step to process or None for current step
        :param data: data to initialize the form instance
        :param files: files to initialize the form instance
        :return: form instance for the given step
        """
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
        """
        Return the template context for a given step. Set the editor_mode flag to be used in the template.

        :param form: Form instance of the current step
        :param kwargs: arbitrary keyword arguments
        :return: a dictionary containing the context for the given step
        """
        context = super(EditPollWizard, self).get_context_data(form=form, **kwargs)
        context.update({'editor_mode': True})
        return context


class SignUpView(CreateView):
    """
    Registration view for creating a new :model:`auth.User`.
    """
    form_class = SignUpForm
    template_name = 'polls/signup.html'
    success_url = reverse_lazy('polls:index')
    model = User

    def form_valid(self, form):
        """
        Create a new :model:`auth.User` and then performs authentication and log-in.

        :param form: Form instance
        :return: HTTP redirect to the index view
        """
        super(SignUpView, self).form_valid(form)
        form.save()
        username = form.cleaned_data.get('username')
        raw_password = form.cleaned_data.get('password1')
        user = authenticate(username=username, password=raw_password)
        login(self.request, user)

        return redirect(self.get_success_url())
