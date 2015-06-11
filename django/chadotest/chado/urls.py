from django.conf.urls import patterns, url

urlpatterns = patterns('chado.views',
    # the index
    url(r'^$', 'index', {'template_name' : 'chado/index.html'}, name='index'),

    # organism
    url(r'^organism/$', 'organism_index', {'template_name' : 'chado/organism/index.html'}, name='organism_index'),
    url(r'^organism/(?P<organism_id>\d+)/$', 'organism_view', {'template_name' : 'chado/organism/view.html'}, name='organism_view'),

    # multiple sequence alignment
    url(r'^msa/$', 'msa_index', {'template_name' : 'chado/msa/index.html'}, name='msa_index'),
    url(r'^msa/(?P<feature_name>[^\/]+)/$', 'msa_view', {'template_name' : 'chado/msa/view.html'}, name='msa_view'),
    url(r'^msa/consn\.(?P<feature_name>.+)/consensus/$', 'msa_consensus', {'template_name' : 'chado/msa/consensus.html'}, name='msa_consensus'),
    url(r'^msa/(?P<feature_name>.+)/download/$', 'msa_consensus_download', name='msa_consensus_download'),

    # phylo tree
    url(r'^phylo/$', 'phylo_index', {'template_name' : 'chado/phylo/index.html'}, name='phylo_index'),
    url(r'^phylo/(?P<phylotree_name>[^\/]+)/$', 'phylo_view', {'template_name' : 'chado/phylo/view.html'}, name='phylo_view'),
    url(r'^phylo/(?P<phylotree_name>[^\/]+)/newick/$', 'phylo_newick', {'template_name' : 'chado/phylo/newick.html'}, name='phylo_newick'),
    url(r'^phylo/(?P<phylotree_name>[^\/]+)/download/$', 'phylo_newick_download', name='phylo_newick_download'),
    url(r'^phylo/(?P<phylotree_name>[^\/]+)/xml_download/$', 'phylo_xml_download', name='phylo_xml_download'),
    url(r'^phylo/node/gff_download/(?P<phylonode_id>\d+)/$', 'phylo_gff_download', name='phylo_gff_download'),
    # d3
    url(r'^phylo_d3/(?P<phylotree_id>\d+)/$', 'phylo_view_d3', {'template_name' : 'chado/phylo/view_d3.html'}, name='phylo_view_d3'),
    # ajax
    url(r'^phylo/node/slide/$', 'phylo_view_ajax', name='phylo_view_ajax'),

    # feature
    url(r'^feature/(?P<feature_name>[^\/]+)/$', 'feature_view', {'template_name' : 'chado/feature/view.html'}, name='feature_view'),

    # cvterm
    url(r'^cvterm/(?P<cvterm_id>\d+)/$', 'cvterm_view', {'template_name' : 'chado/cvterm/view.html'}, name='cvterm_view'),

    # gene context
    url(r'^context_viewer/json/(?P<node_id>\d+)/$', 'context_viewer_json', name='context_viewer_json'),
    url(r'^context_gff_download/$', 'context_gff_download', {}, name='context_gff_download'),
    url(r'^context_viewer/(?P<node_id>\d+)/$', 'context_viewer', {'template_name' : 'chado/context/index.html'}, name='context_viewer'),
    url(r'^context_viewer/search/$', 'context_viewer_search', {'template_name' : 'chado/context/index.html'}, name='context_viewer_search'),
    url(r'^context_viewer/search/(?P<focus_name>[^\/]+)/$', 'context_viewer_search', {'template_name' : 'chado/context/search.html'}, name='context_viewer_search'),
    url(r'^context_viewer/search_repeat/$', 'context_viewer_search', {'template_name' : 'chado/context/index.html'}, name='context_viewer_search'),
    url(r'^context_viewer/search_repeat/(?P<focus_name>[^\/]+)/$', 'context_viewer_search', {'template_name' : 'chado/context/search_repeat.html'}, name='context_viewer_search'),
    url(r'^context_viewer/search_plotted/(?P<focus_name>[^\/]+)/$', 'context_viewer_search', {'template_name' : 'chado/context/search_plotted.html'}, name='context_viewer_search_plotted'),
    url(r'^context_viewer/synteny/(?P<focus_id>\d+)/$', 'context_viewer_synteny', {'template_name' : 'chado/context/synteny.html'}, name='context_viewer_synteny'),
    # simple views
    url(r'^context_viewer/iframe/(?P<node_id>\d+)/$', 'context_viewer', {'template_name' : 'chado/context/index_iframe.html'}, name='context_viewer'),
    # ajax
    url(r'^context_viewer/search_tracks/$', 'context_viewer_search_tracks_ajax', name='context_viewer_search_tracks_ajax'),
    url(r'^context_viewer/search_global/$', 'context_viewer_search_global_ajax', name='context_viewer_search_global_ajax'),
    )
