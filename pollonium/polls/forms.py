from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from .models import Poll


class CreatePollGeneralForm(forms.ModelForm):
    form_title = "What's the ocassion?"

    class Meta:
        model = Poll
        fields = ('title', 'location', 'description')
        widgets = {
            'title': forms.TextInput(attrs={'class':'form-control', 'placeholder': "What's the poll about"}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Where is happening"}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tell the people more about this'}),
        }


class CreatePollChoicesForm(forms.Form):
    form_title = 'What are the options?'

    def __init__(self, *args, **kwargs):
        super(CreatePollChoicesForm, self).__init__(*args, **kwargs)
        self.set_choice_fields(['', ])

    def set_choice_fields(self, choices):
        self.fields.clear()

        for i, c in zip(range(1, len(choices)+1), choices):
            self.fields['choice%s' % i] = forms.CharField(
                initial=c,
                required=True,
                label=i,
                widget=forms.TextInput(
                    attrs={'class': 'input form-control',
                   'placeholder': 'Option',
                   'id': 'choice%s' % i,
                   'name': 'choice%s'% i,
                   })
            )


class CreatePollSettingsForm(forms.ModelForm):
    form_title = 'Configure your poll'

    class Meta:
        model = Poll
        fields = ('author', 'author_email', 'single_vote', 'limit_votes', 'votes_max', 'hidden_poll', 'only_invited')
        widgets = {
            'author': forms.TextInput(attrs={'class':'form-control'}),
            'author_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'single_vote': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'limit_votes': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'limit_votes'}),
            'votes_max': forms.NumberInput(attrs={'class': 'form-control', 'id': 'votes_max'}),
            'hidden_poll': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'only_invited': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class SignUpForm(UserCreationForm):

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2',)
