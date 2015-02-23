from django.conf.urls import patterns, url

from batch_monitor import views

urlpatterns = patterns( '',
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^(?P<farm_id>\d+)/$', views.monitor, name='monitor'),
    url(r'^(?P<farm_id>\d+)/update/$', views.update, name='update'),
    url(r'^(?P<farm_id>\d+)/json/(?P<data_type>[a-z]{2})/$', views.jsonreq, name='jsonreq'),
    #url(r'^(?P<pk>\d+)/$', views.DetailView.as_view(), name='detail'),
    #url(r'^(?P<pk>\d+)/results/$', views.ResultsView.as_view(), name='results'),
    #url(r'^(?P<poll_id>\d+)/vote/$', views.vote, name='vote'),
)
