from django.conf.urls import url

from batch_farm_monitor import views, views_json

app_name = 'batch_farm_monitor'

urlpatterns = [
	url(r'^$', views.IndexView.as_view(), name='index'),
	url(r'^(?P<farm_id>\d+)/$', views.monitor, name='monitor'),
	url(r'^(?P<farm_id>\d+)/update/$', views.update, name='update'),
	#url(r'^(?P<farm_id>\d+)/json/(?P<data_type>[a-z]{2,3})/$', views.jsonreq, name='jsonreq'),
	url(r'^(?P<farm_id>\d+)/json/(?P<data_type>[a-z]{2,3})/$', views_json.jsonreq, name='jsonreq'),
	#url(r'^(?P<pk>\d+)/$', views.DetailView.as_view(), name='detail'),
	#url(r'^(?P<pk>\d+)/results/$', views.ResultsView.as_view(), name='results'),
	#url(r'^(?P<poll_id>\d+)/vote/$', views.vote, name='vote'),
]
