from django.conf.urls import patterns, url

urlpatterns = patterns('chado.views',
    # the index
    url(r'^$', 'index', {'template_name' : 'chado/index.html'}, name='index'),

    # organism
    url(r'^organism/$', 'organism_index', {'template_name' : 'chado/organism/index.html'}, name='organism_index'),
    url(r'^organism/(?P<organism_id>\d+)/$', 'organism_view', {'template_name' : 'chado/organism/view.html'}, name='organism_view'),

    # multiple sequence alignment
    url(r'^msa/$', 'msa_index', {'template_name' : 'chado/msa/index.html'}, name='msa_index'),
    url(r'^msa/(?P<feature_id>\d+)/$', 'msa_view', {'template_name' : 'chado/msa/view.html'}, name='msa_view'),
    url(r'^msa/(?P<feature_id>\d+)/consensus/$', 'msa_consensus', {'template_name' : 'chado/msa/consensus.html'}, name='msa_consensus'),
    url(r'^msa/(?P<feature_id>\d+)/download/$', 'msa_consensus_download', name='msa_consensus_download'),

    # phylo tree
    url(r'^phylo/$', 'phylo_index', {'template_name' : 'chado/phylo/index.html'}, name='phylo_index'),
    url(r'^phylo/(?P<phylotree_id>\d+)/$', 'phylo_view', {'template_name' : 'chado/phylo/view.html'}, name='phylo_view'),
    #url(r'^phylo/(?P<phylotree_id>\d+)/(?P<phylonode_id>\d+)/$', 'phylo_view', {'template_name' : 'chado/phylo/view.html'}, name='phylo_view'),
    url(r'^phylo/(?P<phylotree_id>\d+)/newick/$', 'phylo_newick', {'template_name' : 'chado/phylo/newick.html'}, name='phylo_newick'),
    url(r'^phylo/(?P<phylotree_id>\d+)/download/$', 'phylo_newick_download', name='phylo_newick_download'),
    url(r'^phylo/(?P<phylotree_id>\d+)/xml_download/$', 'phylo_xml_download', name='phylo_xml_download'),
    url(r'^phylo/node/gff_download/(?P<phylonode_id>\d+)/$', 'phylo_gff_download', name='phylo_gff_download'),
    # phylo tree slide
    url(r'^phylo_slide/(?P<phylotree_id>\d+)/$', 'phylo_view_slide', {'template_name' : 'chado/phylo/view_slide.html'}, name='phylo_view_slide'),
    # ajax
    url(r'^phylo_slide/node/slide/$', 'phylo_view_slide_ajax', name='phylo_view_slide_ajax'),

    # feature
    url(r'^feature/(?P<feature_id>\d+)/$', 'feature_view', {'template_name' : 'chado/feature/view.html'}, name='feature_view'),

    # cvterm
    url(r'^cvterm/(?P<cvterm_id>\d+)/$', 'cvterm_view', {'template_name' : 'chado/cvterm/view.html'}, name='cvterm_view'),

    # search
    url(r'^search/$', 'search', {'template_name' : 'chado/search/index.html'}, name='search'),
    )
