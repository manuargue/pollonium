from django.conf.urls import url

from . import views


app_name = 'polls'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^(?P<pk>[0-9]+)/$', views.detail, name='detail'),
    url(r'^(?P<pk>[0-9]+)/edit/$', views.EditPollWizard.as_view(views.CREATE_FORMS), name='edit'),
    url(r'^(?P<pk>[0-9]+)/results/$', views.results, name='results'),
    url(r'^create/$', views.CreatePollWizard.as_view(views.CREATE_FORMS), name='create'),
]