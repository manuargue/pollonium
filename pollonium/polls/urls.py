from django.conf.urls import url
from django.contrib.auth import views as auth_views

from . import views


app_name = 'polls'
urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^signup/$', views.SignUpView.as_view(), name='signup'),
    url(r'^login/$', auth_views.LoginView.as_view(redirect_authenticated_user=True,
                                                  template_name='polls/login.html'), name='login'),
    url(r'^logout/$', auth_views.LogoutView.as_view(next_page='polls:index',
                                                    template_name='polls/logout.html'), name='logout'),
    url(r'^(?P<pk>[0-9]+)/$', views.detail, name='detail'),
    url(r'^(?P<pk>[0-9]+)/edit/$', views.EditPollWizard.as_view(views.CREATE_FORMS), name='edit'),
    url(r'^create/$', views.CreatePollWizard.as_view(views.CREATE_FORMS), name='create'),
]