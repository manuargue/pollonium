from django.contrib import admin

from .models import Poll, Choice


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 2


class PollAdmin(admin.ModelAdmin):
    fieldsets = [
        ('General',     {'fields': ['title', 'location', 'description', 'pub_date', 'author', 'author_email']}),
        ('Settings',    {'fields': ['hidden_poll', 'single_vote', 'limit_votes', 'votes_max']}),
        ('Sharing',     {'fields': ['only_invited']}),
    ]
    inlines = [ChoiceInline]
    list_display = ('title', 'pub_date', 'author')
    list_filter = ['pub_date']
    search_fields = ['title']


admin.site.register(Poll, PollAdmin)
