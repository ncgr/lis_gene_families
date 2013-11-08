from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'chadotest.views.home', name='home'),
    # url(r'^chadotest/', include('chadotest.foo.urls')),

     # include all the sub urls of the chado app
    url(r'^chado/', include('chado.urls')),

    # include all the sub urls of the d3viz_force_directed app
    url(r'^chado/d3viz_force_directed/', include('d3viz_force_directed.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
