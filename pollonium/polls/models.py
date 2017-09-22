import datetime

from django.db import models
from django.utils import timezone
from django.conf import settings


""" Descriptions for the :model:`polls.Poll` fields. """
FIELD_DESC = {
    'pub_date':     'published date',
    'single_vote':  'limit participants to a single vote',
    'limit_votes':  'limit the number of votes per option',
    'votes_max':    'votes per option',
    'only_invited': 'only invited people can see the poll',
}


class Poll(models.Model):
    """
    Stores a poll and its settings.
    """
    title = models.CharField(max_length=200)
    pub_date = models.DateTimeField(FIELD_DESC['pub_date'])
    location = models.CharField(default='', blank=True, max_length=20)
    description = models.TextField(default='', blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL)
    limit_votes = models.BooleanField(FIELD_DESC['limit_votes'], default=False)
    votes_max = models.PositiveIntegerField(FIELD_DESC['votes_max'], default=0)
    hidden_poll = models.BooleanField(default=False)                                # TODO implement
    single_vote = models.BooleanField(FIELD_DESC['single_vote'], default=False)
    only_invited = models.BooleanField(FIELD_DESC['only_invited'], default=False)   # TODO implement

    def get_votes_list(self):
        return list(Vote.objects.filter(choice__poll__pk=self.pk
            ).values_list('user__username', 'choice'
            ).order_by('user__username'))

    def get_users(self):
        """
        :return: a list of all :model:`auth.User` that have voted in the :model:`polls.Poll`
        """
        return list(User.objects.prefetch_related('vote_set'
            ).filter(vote__choice__poll__pk=self.pk))

    def is_finished(self):
        """
        :return: True if all :model:`polls.Choice` of this :model:`polls.Poll` cannot be voted anymore, False otherwise.
        """
        if self.limit_votes:
            choices = self.choice_set.count()
            votes = Vote.objects.filter(choice__poll__pk=self.pk).count()
            return votes >= self.votes_max * choices
        return False

    def allowed_to_vote(self, user):
        return not (poll.single_vote and poll.user_already_vote(user))

    def user_already_vote(self, user):
        """
        :param user: :model:`auth.User` to test if has voted
        :return: True if the given :model:`auth.User` already voted in this :model:`polls.Poll`
        """
        return Vote.objects.filter(choice__poll__pk=self.pk
                        ).filter(user__username__exact=user).exists()

    def was_published_recently(self):
        """
        :return: True if this :model:`polls.Poll` has been published in the last day
        """
        now = timezone.now()
        return now-datetime.timedelta(days=1) <= self.pub_date <= now

    def __str__(self):
        """
        :return: string representation containing the :model:`polls.Poll` title field
        """
        return self.title


class Choice(models.Model):
    """
    Stores a choice for a given :model:`polls.Poll`. Related to :model:`polls.Vote`.
    """
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    text = models.CharField(max_length=200)

    def get_users(self):
        """
        :return: list of all :model:`auth.User` that have voted this :model:`polls.Choice`
        """
        return list(Choice.objects.get(pk=self.pk).vote_set.values_list('user__username'))

    def is_voted_by(self, user):
        """
        :param user: :model:`auth.User` to test
        :return: True if the given :model:`auth.User` has voted this :model:`polls.Choice`
        """
        return self.vote_set.filter(user=user).exists()

    def is_full(self):
        """
        :return: True if the vote count for this :model:`polls.Choice` reached the maximum, False otherwise or if the
        :model:`polls.Poll` doesn't have a vote limit set
        """
        #return self.poll.limit_votes and self.vote_count() >= self.poll.votes_max
        return Choice.objects.filter(pk=self.pk
            ).filter(poll__limit_votes=True
            ).annotate(total_votes=models.Count('vote')
            ).filter(total_votes__gte=models.F('poll__votes_max')
            ).exists()

    def vote_count(self):
        """
        :return: total :model:`polls.Vote` for this instance
        """
        return self.vote_set.count()

    def __str__(self):
        """
        :return: string representation containing the :model:`polls.Choice` text field
        """
        return self.text


class Vote(models.Model):
    """
    Store a single vote for a given :model:`polls.Choice`. Related :model:`polls.Poll`
    """
    poll = models.ForeignKey(Poll)
    choice = models.ForeignKey(Choice)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)

    def __str__(self):
        """
        :return: string representation containing voted :model:`polls.Choice` and the :model:`auth.User` who voted it
        """
        return 'Vote for %s by %s in %s' % (self.choice, self.user, self.poll)
