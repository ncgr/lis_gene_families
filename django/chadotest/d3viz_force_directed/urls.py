from django.conf.urls import patterns, include, url

urlpatterns = patterns('d3viz_force_directed.views',
    url(r'^phylonode/viz/(\d+)/?$', 'viz'),
    url(r'^phylonode/vis/(\d+)/?$', 'viz'),
    url(r'^phylonode/(\d+).json$', 'phylonode_json')
) 
