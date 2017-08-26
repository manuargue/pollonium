import datetime

from django.db import models
from django.utils import timezone
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


FIELD_DESC = {
    'pub_date':     'published date',
    'single_vote':  'limit participants to a single vote',
    'limit_votes':  'limit the number of votes per option',
    'votes_max':    'votes per option',
    'only_invited': 'only invited people can see the poll',
}


class Poll(models.Model):
    title = models.CharField(max_length=200)
    pub_date = models.DateTimeField(FIELD_DESC['pub_date'])
    location = models.CharField(default='', blank=True, max_length=20)
    description = models.TextField(default='', blank=True)
    author = models.CharField(max_length=20)
    author_email = models.EmailField()
    limit_votes = models.BooleanField(FIELD_DESC['limit_votes'], default=False)
    votes_max = models.PositiveIntegerField(FIELD_DESC['votes_max'], default=0)
    hidden_poll = models.BooleanField(default=False)                                # TODO implement
    single_vote = models.BooleanField(FIELD_DESC['single_vote'], default=False)
    only_invited = models.BooleanField(FIELD_DESC['only_invited'], default=False)   # TODO implement

    def get_users(self):
        return list(set(v.user for v in self.vote_set.all()))

    def is_finished(self):
        return all(c.is_full() for c in self.choice_set.all())

    def user_already_vote(self, user):
        return any(c.is_voted_by(user) for c in self.choice_set.all())

    def was_published_recently(self):
        now = timezone.now()
        return now-datetime.timedelta(days=1) <= self.pub_date <= now

    def __str__(self):
        return self.title


class Choice(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    text = models.CharField(max_length=200)

    def get_users(self):
        return list(set(v.user for v in self.vote_set.all()))

    def is_voted_by(self, user):
        return self.vote_set.filter(user=user).exists()

    def is_full(self):
        return self.poll.limit_votes and self.vote_count() >= self.poll.votes_max

    def vote_count(self):
        return self.vote_set.count()

    def __str__(self):
        return self.text


class Vote(models.Model):
    poll = models.ForeignKey(Poll)
    choice = models.ForeignKey(Choice)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)

    def __str__(self):
        return 'Vote for %s by %s' % (self.choice, self.user)
