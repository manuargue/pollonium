from django.conf.urls import url

from . import forms
from . import views


app_name = 'polls'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^(?P<pk>[0-9]+)/$', views.detail, name='detail'),
    url(r'^create/$', views.CreatePollWizard.as_view(views.CREATE_FORMS), name='create'),
    #url(r'^(?P<pk>[0-9]+)/results/$', views.results, name='results'),
]