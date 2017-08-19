from django.conf.urls import url

from . import views

app_name = 'polls'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^(?P<pk>[0-9]+)/$', views.detail, name='detail'),
    url(r'^create/general/$', views.create_general, name='create_general'),
    url(r'^create/choices/$', views.create_choices, name='create_choices'),
    url(r'^create/settings/$', views.create_settings, name='create_settings'),
    url(r'^(?P<pk>[0-9]+)/results/$', views.results, name='results'),
]