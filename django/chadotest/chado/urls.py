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
    url(r'^phylo/(?P<phylotree_id>\d+)/$', 'phylo_view_slide', {'template_name' : 'chado/phylo/view_slide.html'}, name='phylo_view'),
    #url(r'^phylo/(?P<phylotree_id>\d+)/(?P<phylonode_id>\d+)/$', 'phylo_view', {'template_name' : 'chado/phylo/view.html'}, name='phylo_view'),
    url(r'^phylo/(?P<phylotree_id>\d+)/newick/$', 'phylo_newick', {'template_name' : 'chado/phylo/newick.html'}, name='phylo_newick'),
    url(r'^phylo/(?P<phylotree_id>\d+)/download/$', 'phylo_newick_download', name='phylo_newick_download'),
    url(r'^phylo/(?P<phylotree_id>\d+)/xml_download/$', 'phylo_xml_download', name='phylo_xml_download'),
    url(r'^phylo/node/gff_download/(?P<phylonode_id>\d+)/$', 'phylo_gff_download', name='phylo_gff_download'),
    url(r'^phylo/node/json/(?P<phylonode_id>\d+)/$', 'phylonode_json', name='phylonode_json'),
    # phylo tree slide
    url(r'^phylo_slide/(?P<phylotree_id>\d+)/$', 'phylo_view_slide', {'template_name' : 'chado/phylo/view_slide.html'}, name='phylo_view_slide'),
    # ajax
    url(r'^phylo_slide/node/slide/$', 'phylo_view_slide_ajax', name='phylo_view_slide_ajax'),

    # feature
    url(r'^feature/(?P<feature_id>\d+)/$', 'feature_view', {'template_name' : 'chado/feature/view.html'}, name='feature_view'),

    # cvterm
    url(r'^cvterm/(?P<cvterm_id>\d+)/$', 'cvterm_view', {'template_name' : 'chado/cvterm/view.html'}, name='cvterm_view'),

    # search
    #url(r'^search_new/$', 'search_new', {'template_name' : 'chado/search/index.html'}, name='search_new'),
    url(r'^search/$', 'search', name='search'),
    url(r'^search/(?P<depth>\d+)/new/$', 'search_feature', {'template_name' : 'chado/search/index.html', 'who' : 'search'}, name='search_new_feature'),
    url(r'^search/(?P<depth>\d+)/organism/$', 'search_organism', {'template_name' : 'chado/search/organism.html'}, name='search_organism'),
    url(r'^search/(?P<depth>\d+)/msa/$', 'search_msa', {'template_name' : 'chado/search/msa.html'}, name='search_msa'),
    url(r'^search/(?P<depth>\d+)/msa/feature/$', 'search_feature', {'template_name' : 'chado/search/feature.html', 'who' : 'msa'}, name='search_msa_feature'),
    url(r'^search/(?P<depth>\d+)/phylo/$', 'search_phylo', {'template_name' : 'chado/search/phylo.html'}, name='search_phylo'),
    url(r'^search/(?P<depth>\d+)/phylo/feature/$', 'search_feature', {'template_name' : 'chado/search/feature.html', 'who' : 'phylo'}, name='search_phylo_feature'),
    # ajax
    url(r'^search/(?P<depth>\d+)/add/$', 'search_add_result_ajax', {'who' : ''}, name='search_add_result_ajax'),
    url(r'^search/(?P<depth>\d+)/remove/$', 'search_remove_result_ajax', {'who' : ''}, name='search_remove_result_ajax'),
    url(r'^search/(?P<depth>\d+)/clear/$', 'search_clear_results_ajax', {'who' : ''}, name='search_clear_results_ajax'),
    url(r'^search/(?P<depth>\d+)/add_all/$', 'search_add_all_ajax', {'who' : ''}, name='search_add_all_ajax'),
    url(r'^search/(?P<depth>\d+)/remove_all/$', 'search_remove_all_ajax', {'who' : ''}, name='search_remove_all_ajax'),
    url(r'^search/(?P<depth>\d+)/msa/add/$', 'search_add_result_ajax', {'who' : 'msa'}, name='search_msa_add_result_ajax'),
    url(r'^search/(?P<depth>\d+)/msa/remove/$', 'search_remove_result_ajax', {'who' : 'msa'}, name='search_msa_remove_result_ajax'),
    url(r'^search/(?P<depth>\d+)/msa/clear/$', 'search_clear_results_ajax', {'who' : 'msa'}, name='search_msa_clear_results_ajax'),
    url(r'^search/(?P<depth>\d+)/msa/add_all/$', 'search_add_all_ajax', {'who' : 'msa'}, name='search_msa_add_all_ajax'),
    url(r'^search/(?P<depth>\d+)/msa/remove_all/$', 'search_remove_all_ajax', {'who' : 'msa'}, name='search_msa_remove_all_ajax'),
    url(r'^search/(?P<depth>\d+)/phylo/add/$', 'search_add_result_ajax', {'who' : 'phylo'}, name='search_phylo_add_result_ajax'),
    url(r'^search/(?P<depth>\d+)/phylo/remove/$', 'search_remove_result_ajax', {'who' : 'phylo'}, name='search_phylo_remove_result_ajax'),
    url(r'^search/(?P<depth>\d+)/phylo/clear/$', 'search_clear_results_ajax', {'who' : 'phylo'}, name='search_phylo_clear_results_ajax'),
    url(r'^search/(?P<depth>\d+)/phylo/add_all/$', 'search_add_all_ajax', {'who' : 'phylo'}, name='search_phylo_add_all_ajax'),
    url(r'^search/(?P<depth>\d+)/phylo/remove_all/$', 'search_remove_all_ajax', {'who' : 'phylo'}, name='search_phylo_remove_all_ajax'),
    url(r'^search/(?P<depth>\d+)/feature/add/$', 'search_add_result_ajax', {'who' : ''}, name='search_feature_add_result_ajax'),
    url(r'^search/(?P<depth>\d+)/feature/remove/$', 'search_remove_result_ajax', {'who' : ''}, name='search_feature_remove_result_ajax'),
    url(r'^search/(?P<depth>\d+)/feature/clear/$', 'search_clear_results_ajax', {'who' : ''}, name='search_feature_clear_results_ajax'),
    url(r'^search/(?P<depth>\d+)/feature/add_all/$', 'search_add_all_ajax', {'who' : ''}, name='search_feature_add_all_ajax'),
    url(r'^search/(?P<depth>\d+)/feature/remove_all/$', 'search_remove_all_ajax', {'who' : ''}, name='search_feature_remove_all_ajax'),
    )
