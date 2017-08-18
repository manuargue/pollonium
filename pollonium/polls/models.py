import datetime

from django.db import models
from django.utils import timezone


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
    hidden_poll = models.BooleanField(default=False)
    single_vote = models.BooleanField(FIELD_DESC['single_vote'], default=False)
    only_invited = models.BooleanField(FIELD_DESC['only_invited'], default=False)

    def was_published_recently(self):
        now = timezone.now()
        return now-datetime.timedelta(days=1) <= self.pub_date <= now

    def __str__(self):
        return self.title


class Choice(models.Model):
    question = models.ForeignKey(Poll, on_delete=models.CASCADE)
    text = models.CharField(max_length=200)
    votes = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.text