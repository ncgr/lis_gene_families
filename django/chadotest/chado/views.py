
# import http stuffs
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseBadRequest, Http404
from django.utils import simplejson
from django.core.urlresolvers import reverse
# file generation stuffs
import cStringIO as StringIO
# pagination stuffs
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
# for passing messages
from django.contrib import messages
# import our models and helpers
from chado.models import Organism, Cvterm, Feature, Phylotree, Featureloc, Phylonode, FeatureRelationship, Analysisfeature, FeatureCvterm, GeneOrder, Featureprop
from django.db.models import Count
# make sure we have the csrf token!
from django.views.decorators.csrf import ensure_csrf_cookie
# search stuffs
import re
from django.db.models import Q
# for sending messages to the templates
from django.contrib import messages
# context view
import operator


#########
# index #
#########


def index(request, template_name):
    organisms = Organism.objects.all()
    consensus = get_object_or_404(Cvterm, name="consensus")
    msas = Feature.objects.filter(type_id=consensus)
    return render(request, template_name, {'organisms' : organisms, 'msas' : msas})


########################
# search functionality *
########################
# http://julienphalip.com/post/2825034077/adding-search-to-a-django-site-in-a-snap

def normalize_query(query_string, findterms=re.compile(r'"([^"]+)"|(\S+)').findall, normspace=re.compile(r'\s{2,}').sub):
    ''' Splits the query string in invidual keywords, getting rid of unecessary spaces and grouping quoted words together.'''
    return [normspace(' ', (t[0] or t[1]).strip()) for t in findterms(query_string)] 


def get_query(query_string, search_fields):
    ''' Returns a query, that is a combination of Q objects.
	That combination aims to search keywords within a model by testing the given search fields.'''
    query = None # Query to search for every search term        
    terms = normalize_query(query_string)
    for term in terms:
        or_query = None # Query to search for a given term in each field
        for field_name in search_fields:
            q = Q(**{"%s__icontains" % field_name: term})
            if or_query is None:
                or_query = q
            else:
                or_query = or_query | q
        if query is None:
            query = or_query
        else:
            query = query & or_query
    return query


# a helper function that destroys all previous carts when a new search is conducted
def search(request):
    if 'q' in request.GET and request.GET['q'].strip():
        # remove the previous search session data
        for k in request.session.keys():
            if k.startswith('results_'):
                del request.session[k]
        return redirect('/chado/search/0/new/?q='+request.GET['q']);
    return redirect(request.META.get('HTTP_REFERER', '/chado/'))


#def search(request, template_name):
#    print "searching"
#    # if there's a query
#    if 'q' in request.GET and request.GET['q'].strip():
#        query_string = request.GET['q']
#        term_query = get_query(query_string, ['cvterm__name', 'cvterm__definition',])
#        results = FeatureCvterm.objects.filter(term_query)
#        return render(request, template_name, {'query_string' : query_string, 'results' : paginate(request, results, 'search_num'), 'result_nums' : RESULT_NUMS, 'selected' : get_results(request, 0)})
#    # redirect if there wasn't a query
#	return redirect(request.META.get('HTTP_REFERER', '/chado/'))

def search_organism(request, depth, template_name, who):
    # if there's a query
    if 'q' in request.GET and request.GET['q'].strip() and (who == 'feature' or who == 'msa' or who == 'phylo'):
        depth = int(depth)
        prev_results = get_results(request, depth, who)
        if len(prev_results) == 0:
            messages.error(request, 'No results selected!')
            return redirect(request.META.get('HTTP_REFERER'))
        features = None
        if who == 'feature':
            features = Feature.objects.filter(pk__in=prev_results.keys())
        elif who == 'msa':
            features = Feature.objects.filter(pk__in=Featureloc.objects.filter(srcfeature__pk__in=prev_results.keys()).values_list('feature_id', flat=True))
        else:
            features = Feature.objects.filter(pk__in=Phylonode.objects.filter(phylotree__pk__in=prev_results).values_list('feature_id', flat=True))
        nav = get_nav(request, depth, 'organism_'+who)
        depth += 1
        result_organisms = Organism.objects.filter(pk__in=features.values_list('organism_id', flat=True))
        return render(request, template_name, {'query_string' : request.GET['q'], 'result_organisms' : paginate(request, result_organisms, 'search_organism_num'), 'result_nums' : RESULT_NUMS, 'depth' : depth, 'prev_depth' : depth-1, 'nav' : nav})
    # redirect if there wasn't a query
	return redirect(request.META.get('HTTP_REFERER', '/chado/'))

def search_msa(request, depth, template_name, who):
    # if there's a query
    if 'q' in request.GET and request.GET['q'].strip() and (who == 'feature' or who == 'phylo'):
        # get the msas
        depth = int(depth)
        prev_results = get_results(request, depth, who)
        if len(prev_results) == 0:
            messages.error(request, 'No reuslts selected!')
            return redirect(request.META.get('HTTP_REFERER'))
        features = None
        if who == 'feature':
            features = Feature.objects.filter(pk__in=prev_results.keys())
        else:
            features = Feature.objects.filter(pk__in=Phylonode.objects.filter(phylotree__pk__in=prev_results).values_list('feature_id', flat=True))
        msa_ids = Featureloc.objects.filter(feature__in=features).values_list('srcfeature', flat=True)
        result_msas = Feature.objects.filter(type__name='consensus', pk__in=msa_ids)
        nav = get_nav(request, depth, 'msa_'+who)
        depth += 1
        selected = get_results(request, depth, 'msa')
        return render(request, template_name, {'query_string' : request.GET['q'], 'result_msas' : paginate(request, result_msas, 'search_msa_num'), 'result_nums' : RESULT_NUMS, 'selected' : selected, 'depth' : depth, 'prev_depth' : depth-1, 'nav' : nav})
    # redirect if there wasn't a query
	return redirect(request.META.get('HTTP_REFERER', '/chado/'))

def search_phylo(request, depth, template_name, who):
    # if there's a query
    if 'q' in request.GET and request.GET['q'].strip() and (who == 'feature' or who == 'msa'):
        # get the msas
        depth = int(depth)
        prev_results = get_results(request, depth, who)
        if len(prev_results) == 0:
            messages.error(request, 'No results selected!')
            return redirect(request.META.get('HTTP_REFERER'))
        feature = None
        if who == 'feature':
            features = Feature.objects.filter(pk__in=prev_results.keys())
        else:
            features = Feature.objects.filter(pk__in=Featureloc.objects.filter(srcfeature__pk__in=prev_results.keys()).values_list('feature_id', flat=True))
        tree_ids = Phylonode.objects.filter(feature__in=features).values_list('phylotree', flat=True)
        result_trees = Phylotree.objects.filter(pk__in=tree_ids)
        nav = get_nav(request, depth, 'phylo_'+who)
        depth += 1
        selected = get_results(request, depth, 'phylo')
        return render(request, template_name, {'query_string' : request.GET['q'], 'result_trees' : paginate(request, result_trees, 'search_phylo_num'), 'result_nums' : RESULT_NUMS, 'selected' : selected, 'depth' : depth, 'prev_depth' : depth-1, 'nav' : nav})
    # redirect if there wasn't a query or the sender wasn't recognized
    messages.error(request, 'Bad request!')
    return redirect(request.META.get('HTTP_REFERER'))

def search_feature(request, depth, template_name, who):
    if 'q' in request.GET and request.GET['q'].strip() and (who == 'feature' or who == 'msa' or who == 'phylo'):
        depth = int(depth)
        # note, depth is incremented every time features come around
        result_features = None
        if who == 'feature':
            query_string = request.GET['q']
            term_query = get_query(query_string, ['cvterm__name', 'cvterm__definition', 'feature__uniquename'])
            results = Feature.objects.filter(featurecvterm_feature__in=FeatureCvterm.objects.filter(term_query))
        else:
            prev_results = get_results(request, depth, who)
            if len(prev_results) == 0:
                messages.error(request, 'No results selected!')
                return redirect(request.META.get('HTTP_REFERER'))
            elif who == 'msa':
                results = Feature.objects.filter(pk__in=Featureloc.objects.filter(srcfeature__pk__in=prev_results.keys()).values_list('feature_id', flat=True))
            else:
                results = Feature.objects.filter(pk__in=Phylonode.objects.filter(phylotree__pk__in=prev_results).values_list('feature_id', flat=True))
        nav = get_nav(request, depth, 'feature_'+who)
        depth += 1
        selected = get_results(request, depth, 'feature')
        return render(request, template_name, {'query_string' : request.GET['q'], 'results' : paginate(request, results, 'search_feature_num'), 'result_nums' : RESULT_NUMS, 'selected' : selected, 'depth' : depth, 'prev_depth' : depth-1, 'nav' : nav})
    # rediect if there wasn't a query or the sender wasn't recognized
    messages.error(request, 'Bad request!')
    return redirect(request.META.get('HTTP_REFERER', '/chado/'))

def initialize_results_session(request, depth, who=''):
    request.session['results_'+str(depth)+who] = {}

def get_results(request, depth, who):
    if 'results_'+str(depth)+who not in request.session:
        request.session['results_'+str(depth)+who] = {}
    return request.session['results_'+str(depth)+who]

def get_nav(request, depth, who):
    depth = int(depth)
    if 'results_nav' not in request.session:
        request.session['results_nav'] = []
    request.session['results_nav'] = request.session['results_nav'][0 : depth]
    request.session['results_nav'].append({'depth' : depth, 'who' : who})
    return request.session['results_nav']

def search_add_result_ajax(request, depth, who):
    if request.is_ajax():
        result = None
        try:
            if who == 'phylo':
                result = Phylotree.objects.get(pk=request.GET['result'])
            else:
                result = Feature.objects.get(pk=request.GET['result'])
        except DoesNotExist:
            return HttpResponseBadRequest('Bad Request')
        if 'results_'+str(depth)+who not in request.session:
            initialize_results_session(request, depth, who)
        request.session['results_'+str(depth)+who][result.pk] = result.name
        return HttpResponse('OK')
    return HttpResponseBadRequest('Bad Request')

def search_remove_result_ajax(request, depth, who):
    if request.is_ajax():
        result = None
        try:
            if who == 'phylo':
                result = Phylotree.objects.get(pk=request.GET['result'])
            else:
                result = Feature.objects.get(pk=request.GET['result'])
        except DoesNotExist:
            return HttpResponseBadRequest('Bad Request')
        if 'results_'+str(depth)+who not in request.session:
            initialize_results_session(request, depth, who)
        if result.pk in request.session['results_'+str(depth)+who]:
            del request.session['results_'+str(depth)+who][result.pk]
        return HttpResponse('OK')
    return HttpResponseBadRequest('Bad Request')

def search_add_all_ajax(request, depth, who):
    if request.is_ajax():
        if 'results_'+str(depth)+who not in request.session:
            initialize_results_session(request, depth, who)
        results = None
        if who == 'phylo':
            results = Phylotree.objects.filter(pk__in=request.GET.getlist('results[]'))
        else:
            results = Feature.objects.filter(pk__in=request.GET.getlist('results[]'))
        for r in results:
            request.session['results_'+str(depth)+who][r.pk] = r.name
        return HttpResponse('OK');
    return HttpResponseBadRequest('Bad Request')

def search_remove_all_ajax(request, depth, who):
    if request.is_ajax():
        if 'results_'+str(depth)+who not in request.session:
            initialize_results_session(request, depth, who)
        else:
            results = Feature.objects.filter(pk__in=request.GET.getlist('results[]'))
            for pk in map(int, request.GET.getlist('results[]')):
                if pk in request.session['results_'+str(depth)+who]:
                    del request.session['results_'+str(depth)+who][pk]
        return HttpResponse('OK');
    return HttpResponseBadResquest('Bad Request')

def search_clear_results_ajax(request, depth, who):
    if request.is_ajax():
        initialize_results_session(request, depth, who)
        return HttpResponse('OK')
    return HttpResponseBadRequest('Bad Request')


############
# organism #
############


def organism_index(request, template_name):
    return render(request, template_name, {'organisms' : paginate(request, Organism.objects.all(), 'organism_num'), 'result_nums' : RESULT_NUMS})


def organism_view(request, organism_id, template_name):
    organism = get_object_or_404(Organism, pk=organism_id)
    features = Feature.objects.filter(organism=organism).defer("feature_id", "dbxref", "organism", "name", "uniquename", "residues", "seqlen", "md5checksum", "is_analysis", "is_obsolete", "timeaccessioned", "timelastmodified")
    num_features = features.values('type__name').annotate(count=Count('type'))
    return render(request, template_name, {'organism' : organism, 'total_features' : features.count(), 'num_features' : simplejson.dumps(list(num_features))})


#######
# msa #
#######


def msa_index(request, template_name):
    return render(request, template_name, {'msas' : paginate(request, Feature.objects.filter(type__name='consensus'), 'msa_num'), 'result_nums' : RESULT_NUMS})


def msa_view(request, feature_id, template_name):
    consensus = get_object_or_404(Feature, pk=feature_id)
    featurelocs = Featureloc.objects.filter(srcfeature=consensus)
    # I'm sure there's a better way to get a count of the organisms but the values method was giving me trouble
    organism_pks = list(featurelocs.values_list('feature__organism', flat=True))
    organisms = Organism.objects.filter(pk__in=organism_pks)
    num_organisms = []
    for o in organisms:
        num_organisms.append({'organism' : o.common_name, 'count' : organism_pks.count(o.pk)})
    return render(request, template_name, {'consensus' : consensus, 'featurelocs' : featurelocs, 'num_organisms' : simplejson.dumps(list(num_organisms))})


def msa_consensus(request, feature_id, template_name):
    consensus = get_object_or_404(Feature, pk=feature_id)
    featurelocs = Featureloc.objects.filter(srcfeature=consensus)
    return render(request, template_name, {'consensus' : consensus, 'featurelocs' : featurelocs})


def msa_consensus_download(request, feature_id):
    # get consensus stuffs
    consensus = get_object_or_404(Feature, pk=feature_id)
    featurelocs = Featureloc.objects.filter(srcfeature=consensus)

    # write the file to be downloaded
    myfile = StringIO.StringIO()
    myfile.write(">"+consensus.name+"\n"+consensus.residues+"\n")
    for f in featurelocs:
        myfile.write(">"+f.feature.name+"\n"+f.residue_info+"\n")

    # generate the file
    response = HttpResponse(myfile.getvalue(), content_type='text/plain')
    response['Content-Length'] = myfile.tell()
    response['Content-Disposition'] = 'attachment; filename='+consensus.name+'_msa.fa'

    return response


#############
# phylogeny #
#############


def phylo_index(request, template_name):
    return render(request, template_name, {'trees' : paginate(request, Phylotree.objects.all(), 'phylo_num'), 'result_nums' : RESULT_NUMS})


#def phylo_view(request, phylotree_id, phylonode_id, template_name):
def phylo_view(request, phylotree_id, template_name):
    # get trees stuffs
    tree = get_object_or_404(Phylotree, pk=phylotree_id)
    #xml, num_leafs = phylo_xml(tree, phylonode_id)
    url = 'http://velarde.ncgr.org:7070/isys/launch?svc=org.ncgr.cmtv.isys.CompMapViewerService%40--style%40http://velarde.ncgr.org:7070/isys/bin/Components/cmtv/conf/cmtv_combined_map_style.xml%40--combined_display%40http://'+request.get_host()+'/chado/phylo/node/gff_download/'
    xml, num_leafs = phylo_xml(tree, url)
    return render(request, template_name, {'tree' : tree, 'xml' : xml, 'num_leafs' : num_leafs})


#def phylo_xml(tree, node_id):
def phylo_xml(tree, url):
    nodes = Phylonode.objects.filter(phylotree=tree)
    root = nodes.get(left_idx=1)
    #root = nodes.get(pk=node_id)

    # function that adds nodes to a xml tree and counts number of leaf nodes so we can dynamically set the tree height in the template
    def add_node(xmltree, node, family, leafs):
        xmltree += '<clade><branch_length>'+(str(node.distance) if node.distance else ".01")+'</branch_length>'
        #xmltree += '<clade><branch_length>'+str(node.distance)+'</branch_length>'
        if node.label:
            leafs += 1
            #xmltree += '<name>'+node.label+'</name><chart><component>'+node.feature.organism.genus+'_'+node.feature.organism.species+'</component><content>'+str(node.feature.seqlen)+'</content></chart>'
            xmltree += '<name>'+node.label+'</name><chart><component>'+node.feature.organism.genus+'_'+node.feature.organism.species+'</component><content>'+(str(node.feature.seqlen) if node.feature.seqlen else '0')+'</content></chart>'
        else:
            xmltree += '<name>&#9675;</name>'
        #xmltree += '<desc>This is a description</desc>'
        #xmltree += '<uri>/chado/phylo/node/'+str(node.phylonode_id)+'/gff_download</uri></annotation>'
        #xmltree += '<uri>http://velarde.ncgr.org:7070/isys/launch?svc=org.ncgr.cmtv.isys.CompMapViewerService%40http://'+request.get_host()+'/chado/phylo/node/'+str(node.phylonode_id)+'/gff_download</uri></annotation>'
        #if node.distance:
        #xmltree += '<annotation><uri>http://velarde.ncgr.org:7070/isys/launch?svc=org.ncgr.cmtv.isys.CompMapViewerService%40--style%40http://velarde.ncgr.org:7070/isys/bin/Components/cmtv/conf/cmtv_combined_map_style.xml%40--combined_display%40http://'+request.get_host()+'/chado/phylo/node/'+str(node.phylonode_id)+'/gff_download</uri></annotation>'
        xmltree += '<annotation><uri>'+url+str(node.phylonode_id)+'</uri></annotation>'
	    #xmltree += '<annotation><uri>http://www.google.com/|http://www.comparative-legumes.org/|http://www.ncbi.nlm.nih.gov/</uri></annotation>'
        #xmltree += '<uri>http://velarde.ncgr.org:7070/isys/launch?svc=org.ncgr.cmtv.isys.CompMapViewerService%40--style%40http://velarde.ncgr.org:7070/isys/bin/Components/cmtv/conf/cmtv_combined_map_style.xml%40--no_graphic%40http://'+request.get_host()+'/chado/phylo/node/'+str(node.phylonode_id)+'/gff_download</uri></annotation>'
        #xmltree += '<uri>http://velarde.ncgr.org:7070/isys/launch?svc=org.ncgr.cmtv.isys.CompMapViewerService%40--no_graphic%40http://'+request.get_host()+'/chado/phylo/node/'+str(node.phylonode_id)+'/gff_download</uri></annotation>'
        #xmltree += '<uri>http://velarde.ncgr.org:7070/isys/launch?svc=org.ncgr.cmtv.isys.CompMapViewerService%40--style%40http://velarde.ncgr.org:7070/isys/bin/Components/cmtv/conf/cmtv_combined_map_style.xml%40http://'+request.get_host()+'/chado/phylo/node/'+str(node.phylonode_id)+'/gff_download</uri></annotation>'
        for child in family.filter(parent_phylonode=node):
            xmltree, leafs = add_node(xmltree, child, family, leafs)
        xmltree += '</clade>'
        return xmltree, leafs

    # the xml tree
    xml = '<phyloxml xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.phyloxml.org http://www.phyloxml.org/1.10/phyloxml.xsd" xmlns="http://www.phyloxml.org"><phylogeny rooted="true">'
    # add binary 'arcs' to the trees to represent organisms
    xml += '<render><charts><component type="binary" thickness="10" /><content type="bar" fill="#666" width="0.5" /></charts><styles>'
    # add a style for each organism in the tree
    features = Feature.objects.filter(pk__in=nodes.values_list('feature'))
    organisms = Organism.objects.filter(pk__in=features.values_list('organism'))
    organism_colors = {}

    for o in organisms:
        xml += '<'+o.genus+'_'+o.species+' fill="#A93" stroke="#DDD" />'
    xml += '<barChart fill="#333" stroke-width="0" /></styles></render>'

    # add the nodes to the xml tree
    xml, num_leafs = add_node(xml, root, nodes, 0)

    # close the tree's tags
    xml += '</phylogeny></phyloxml>'
    return xml, num_leafs


def generate_phylo_newick(tree):
    root = Phylonode.objects.get(phylotree=tree, left_idx=1)

    # function that adds nodes to a newick tree
    def add_node(newick, node, tree):
        if node.label:
            newick += node.label+':'+str(node.distance)+','
        else:
            newick += '('
            for child in Phylonode.objects.filter(phylotree=tree, parent_phylonode=node):
                newick = add_node(newick, child, tree)
            if newick[-1] == ',':
                newick = newick[0:-1]
            newick += '):'+str(node.distance)+','
        return newick

    # add the nodes to the newick tree
    newick = add_node('', root, tree)
    if newick[-1] == ',':
        newick = newick[0:-1]
    newick += ';'

    return newick

def phylo_view_d3(request, phylotree_id, template_name):
    # get trees stuffs
    tree = get_object_or_404(Phylotree, pk=phylotree_id)
    newick = generate_phylo_newick(tree)

    # we've got the goods
    return render(request, template_name, {'tree' : tree, 'newick' : newick, 'num_leafs' : Phylonode.objects.filter(phylotree=tree).count})


def phylo_view_slide(request, phylotree_id, template_name):
    # get trees stuffs
    tree = get_object_or_404(Phylotree, pk=phylotree_id)
    xml, num_leafs = phylo_xml(tree, '')

    # we've got the goods
    return render(request, template_name, {'tree' : tree, 'xml' : xml, 'num_leafs' : num_leafs})


def phylo_view_slide_ajax(request):
	if request.is_ajax():
		try:
                        import re;
                        if 'phylonode' in request.GET:
			    node = get_object_or_404(Phylonode, pk=request.GET['phylonode'])
                        elif 'gene' in request.GET:
                            node = get_object_or_404(Feature, pk=request.GET['gene'])
                            node.label = node.name
			slidedict = {}
            # external nodes
			if node.label:
				slidedict['label'] = node.label
				slidedict['meta'] = "This is meta information for "+node.label
                                slidedict['links'] = []
                                if re.match('^Medtr',node.label):
                                    slidedict['links'].append({'LIS Mt4.0 GBrowse':'http://medtr.comparative-legumes.org/gb2/gbrowse/Mt4.0?name='+node.label})
                                    slidedict['links'].append({'LIS Mt3.5.1 GBrowse':'http://medtr.comparative-legumes.org/gb2/gbrowse/Mt3.5.1?name='+node.label})
                                    slidedict['links'].append({'JCVI JBrowse':'http://www.jcvi.org/medicago/jbrowse/?data=data%2Fjson%2Fmedicago&loc='+node.label})
                                    slidedict['links'].append({'Mt HapMap':'http://www.medicagohapmap.org/fgb2/gbrowse/mt35/?name='+node.label})
                                    slidedict['links'].append({'Phytozome':'http://www.phytozome.net/cgi-bin/gbrowse/medicago/?name='+node.label})
                                    slidedict['links'].append({'LegumeIP':'http://plantgrn.noble.org/LegumeIP/getseq.do?seq_acc=IMGA|'+node.label})
                                    gene = node.label.split('.')[0]
                                    #for whatever reason, medicago seems to have gotten their nomenclature into NCBI
                                    slidedict['links'].append({'NCBI Gene':'http://www.ncbi.nlm.nih.gov/gene/?term='+gene})
                                    #but that doesn't mean that it gave other people the message!
                                    slidedict['links'].append({'Genomicus':'http://www.genomicus.biologie.ens.fr/genomicus-plants/cgi-bin/search.pl?view=default&amp;query=MTR_'+gene.replace("Medtr","")})

                                elif re.match('^Glyma',node.label):
                                    slidedict['links'].append({'Soybase':'http://soybase.org/gb2/gbrowse/gmax1.01/?name='+node.label})
                                    slidedict['links'].append({'Phytozome':'http://www.phytozome.net/cgi-bin/gbrowse/soybean/?name='+node.label})
                                    slidedict['links'].append({'SoyKB':'http://soykb.org/gene_card.php?gene='+node.label})
                                    gene = node.label.split('.')[0]
                                    slidedict['links'].append({'Genomicus':'http://www.genomicus.biologie.ens.fr/genomicus-plants/cgi-bin/search.pl?view=default&amp;query='+gene})
                                elif re.match('^Phvul',node.label):
                                    gene = node.label.split('.')[0] + '.' + node.label.split('.')[1];
                                    slidedict['links'].append({'LIS GBrowse':'http://phavu.comparative-legumes.org/gb2/gbrowse/Pv1.0/?name='+gene})
                                    slidedict['links'].append({'Phytozome':'http://www.phytozome.net/cgi-bin/gbrowse/commonbean/?name='+node.label})
                                elif re.match('^AT',node.label):
                                    slidedict['links'].append({'TAIR':'http://www.arabidopsis.org/servlets/TairObject?type=locus&name='+node.label})
                                elif re.match('^LOC_Os',node.label):
                                    slidedict['links'].append({'MSU':'http://rice.plantbiology.msu.edu/cgi-bin/gbrowse/rice/?name='+node.label})
                                elif re.match('^GRMZM',node.label):
                                    gene = node.label.split('_')[0]
                                    slidedict['links'].append({'MaizeGDB':'http://maizegdb.org/cgi-bin/displaygenemodelrecord.cgi?id='+gene})
                                    slidedict['links'].append({'Gramene':'http://www.gramene.org/Zea_mays/Gene/Summary?g='+gene})
                                elif re.match('^Solyc',node.label):
                                    slidedict['links'].append({'Sol Genomics Network':'http://solgenomics.net/gbrowse/bin/gbrowse/ITAG2.3_genomic/?name='+node.label+'&h_feat='+node.label})
                                elif re.match('^Vitvi',node.label):
                                    gene = node.label.split('.')[1]
                                    slidedict['links'].append({'Genoscope':'http://www.genoscope.cns.fr/cgi-bin/ggb/vitis/12X/gbrowse/vitis/?name='+gene})
                                slidedict['links'].append({'google':'http://www.google.com/search?q='+node.label})
            # internal nodes
			else:
				slidedict['label'] = "Interior Node"
                                slidedict['links'] = [{'CMTV':'http://velarde.ncgr.org:7070/isys/launch?svc=org.ncgr.cmtv.isys.CompMapViewerService%40--style%40http://velarde.ncgr.org:7070/isys/bin/Components/cmtv/conf/cmtv_combined_map_style.xml%40--combined_display%40http://'+request.get_host()+'/chado/phylo/node/gff_download/'+str(node.phylonode_id)}]
                                slidedict['links'].append({'NodeGraphWordCloud':'/chado/d3viz_force_directed/phylonode/viz/'+str(node.phylonode_id)}) 
                                #TODO: extract the subset MSA for the sequences in the subtree
                                #slidedict['links'].append({'MSA':'/chado/msa/'+str(node.feature_id)})
                                #hack: use the naming convention to get the consensus feature; trees don't appear to
                                #be easily connected with their MSAs otherwise
                                #consensus_feature = features.get(uniquename=node.phylotree.name+'-consensus');
                                consensus_feature = Feature.objects.get(uniquename=node.phylotree.name+'-consensus');
                                slidedict['links'].append({'MSA':'/chado/msa/'+str(consensus_feature.feature_id)})
                                # load the context viewer with each node in the subtree as a focus gene 
                                slidedict['links'].append({'Context Viewer':'/chado/context_viewer/'+str(node.pk)})
                                slidedict['links'].append({'Context Viewer Fancy':'/chado/context_viewer/demo/'+str(node.pk)})
			return HttpResponse(simplejson.dumps(slidedict), content_type = 'application/javascript; charset=utf8')
		except:
			return HttpResponse("bad request")
                return HttpResponse("bad request")


def phylo_newick(request, phylotree_id, template_name):
    tree = get_object_or_404(Phylotree, pk=phylotree_id)
    return render(request, template_name, {'tree' : tree, 'newick' : generate_phylo_newick(tree)})


def phylo_xml_download(request, phylotree_id):
    # get the tree
    tree = get_object_or_404(Phylotree, pk=phylotree_id)
    xml, num_leafs = phylo_xml(tree, "")

    # write the file to be downloaded
    myfile = StringIO.StringIO()
    myfile.write(xml);

    # generate the file
    response = HttpResponse(myfile.getvalue(), content_type='text/plain')
    response['Content-Length'] = myfile.tell()
    response['Content-Disposition'] = 'attachment; filename='+tree.name+'_xml'

    return response


def phylo_newick_download(request, phylotree_id):
    # get the tree
    tree = get_object_or_404(Phylotree, pk=phylotree_id)

    # write the file to be downloaded
    myfile = StringIO.StringIO()
    myfile.write(tree.comment+"\n")

    # generate the file
    response = HttpResponse(myfile.getvalue(), content_type='text/plain')
    response['Content-Length'] = myfile.tell()
    response['Content-Disposition'] = 'attachment; filename='+tree.name+'_newick'

    return response


def phylo_gff_download(request, phylonode_id):
    # get the selected node and it's children
    phylonode = get_object_or_404(Phylonode, pk=phylonode_id)
    nodes = Phylonode.objects.filter(phylotree=phylonode.phylotree, left_idx__gte=phylonode.left_idx, right_idx__lte=phylonode.right_idx)
    organisms = Organism.objects.all()

    # check if all the nodes have central dogma
    #node_pks = nodes.values_list('pk', flat=True)
    node_pks = nodes.values_list('feature_id', flat=True)
    polypeptide_relationships = FeatureRelationship.objects.filter(subject_id__in=node_pks)
    #FIXME: with the embedded call for this gff in the CMTV launch link, this error does not get reported until
    #the launch. Better would be to have logic that doesn't provide these capabilities for inappropriate subtrees
    if (polypeptide_relationships.count() == 0):
        messages.add_message(request, messages.ERROR, "Genes not available for any species in the subtree")
        return redirect(request.META['HTTP_REFERER'])

    # get the genes and their scores
    mrna_pks = polypeptide_relationships.values_list('object_id', flat=True)
    mrna_relationships = FeatureRelationship.objects.filter(subject_id__in=mrna_pks)
    gene_pks = mrna_relationships.values_list('object_id', flat=True)
    genes = Feature.objects.filter(pk__in=gene_pks)
    analyses = Analysisfeature.objects.filter(feature_id__in=gene_pks)

    # get the feature locations and chromosome for the genes
    featurelocs = Featureloc.objects.filter(feature_id__in=gene_pks)
    chromosome_pks = featurelocs.values_list('srcfeature_id', flat=True)
    #chromosomes = Feature.objects.filter(pk__in=chromosome_pks);
    chromosomes = Feature.objects.filter(pk__in=chromosome_pks).defer("residues").extra(select={'feature_length': "length(residues)"});
    # write the file gff file
    myfile = StringIO.StringIO()
    for c in chromosomes:
        species = organisms.get(organism_id=c.organism_id)
        #myfile.write("##sequence-region " + species.genus+"_"+species.species+":"+c.name + " 1 " + str(len(c.residues))+"\n");
        myfile.write("##sequence-region " + species.genus+"_"+species.species+":"+c.name + " 1 " + str(c.feature_length)+"\n");
        

    for g in genes:
        featureloc = featurelocs.get(feature_id=g.feature_id)
        chromosome = chromosomes.get(feature_id=featureloc.srcfeature_id)
        species = organisms.get(organism_id=chromosome.organism_id)
        analysis = analyses.get(feature_id=g.feature_id)
        score = "."
        if analysis.significance is not None:
            score = str(analysis.significance)
        strand = "."
        if featureloc.strand is not None:
            strand = str(featureloc.strand)
        phase = "."
        if featureloc.phase is not None:
            phase = str(featureloc.phase)
        myfile.write(species.genus+"_"+species.species+":"+chromosome.name+"\t.\tgene\t"+str(featureloc.fmin)+"\t"+str(featureloc.fmax)+"\t"+score+"\t"+strand+"\t"+phase+"\tID="+g.uniquename+";Name="+g.name+";Trait="+phylonode.phylotree.name+"\n")

    # generate the file
    response = HttpResponse(myfile.getvalue(), content_type='text/plain')
    response['Content-Length'] = myfile.tell()
    response['Content-Disposition'] = 'attachment; filename='+phylonode.phylotree.name+'_n'+str(phylonode.left_idx)+'-'+str(phylonode.right_idx)+'.gff'

    return response

##
# phylonode_json: return json of the gene tree and GO terms for this
# phylonode. the json will be consumed by the view in viz(), and possibly
# other services.
#

from pprint import pprint
import inspect

def phylonode_json(request, phylonode_id):

    phylonode = get_object_or_404(Phylonode, pk=phylonode_id)

    # use the left and right index to get the phylonode's child nodes directly:
    nodes = Phylonode.objects.filter(phylotree=phylonode.phylotree,
                                     left_idx__gte=phylonode.left_idx,
                                     right_idx__lte=phylonode.right_idx)

    # the 1st level of FeatureRelationships is polypeptides. we have trust this
    # knowing the chado database was loaded thusly.
    polypeptide_pks = nodes.values_list('feature_id', flat=True)
    #polypeptide_rels = FeatureRelationship.objects.filter(subject_id__in=node_pks)

    # return a json error message unless there is 1 or more polypeptides
    #if (polypeptide_rels.count() == 0):
        #json_msg = {
        #'error':
        #'Polypeptides not available for any species in subtree'
        #}
        #return HttpResponse(simplejson.dumps(json_msg),
                            #content_type = 'application/javascript')
    #polypeptide_pks = polypeptide_rels.values_list('object_id', flat=True)
    polypeptides = Feature.objects.filter(pk__in=polypeptide_pks)

    for pp in polypeptides:
        pprint(pp.feature_id)
        cvterms_rels = FeatureCvterm.objects.filter(feature_id=pp.feature_id)
        cvterm_pks = cvterms_rels.values_list('cvterm_id')
        pprint(cvterm_pks)
        cvterms = Cvterm.objects.filter(pk__in=cvterm_pks)
        for cvterm in cvterms:
            pprint(cvterm)

    json_data = [] # TODO
    return HttpResponse(simplejson.dumps(json_data),
                        content_type = 'application/javascript')


def phylo_sample(request, template_name):
    return render(request, template_name, {})


###########
# feature #
###########

def feature_view(request, feature_id, template_name):
    feature = get_object_or_404(Feature, pk=feature_id)
    return render(request, template_name, {'feature' : feature})


##########
# cvterm #
##########


def cvterm_view(request, cvterm_id, template_name):
    cvterm = get_object_or_404(Cvterm, pk=cvterm_id)
    count = Feature.objects.filter(type=cvterm).count()
    features = Feature.objects.filter(type=cvterm).defer("feature_id", "dbxref", "name", "uniquename", "residues", "seqlen", "md5checksum", "is_analysis", "is_obsolete", "timeaccessioned", "timelastmodified")
    num_features_by_organism = features.values('organism__common_name').annotate(count=Count('organism__common_name'))
    return render(request, template_name, {'cvterm' : cvterm, 'count' : count, 'num_features_by_organism' : simplejson.dumps(list(num_features_by_organism))})


###########
# helpers #
###########

# these are how many results can be shown on a paginated page
# a list and a dictionary for convenience - ordered list -> templates, dictionary -> string lookups in view
RESULT_NUMS = [25, 50, 100, 250, 500]
RESULT_DICT = {}
for n in RESULT_NUMS:
    RESULT_DICT[str(n)] = n

# the one stop paginator - if these things weren't so closely related and always called together, I would call this function god
def paginate(request, objects, who):
    # determines the number of results to be shown on a paginated page
    num = RESULT_DICT.itervalues().next()
    if 'num' in request.GET and request.GET['num'] in RESULT_DICT:
        num = RESULT_DICT[request.GET['num']]
        request.session[who] = num
    elif who in request.session:
        num = request.session[who]
    # paginate the objects
    paginator = Paginator(objects, num)
    page = request.GET.get('page')
    try:
        objects = paginator.page(page)
    except PageNotAnInteger:
        objects = paginator.page(1)
    except EmptyPage:
        objects = paginator.page(paginator.num_pages)
    # give objects a range of pages (10) to be linked
    if objects.paginator.num_pages > 10:
        if objects.number < 7:
            objects.paginator.display_page_range = range(1, 11)
        elif objects.paginator.num_pages - objects.number < 4:
            objects.paginator.display_page_range = range(objects.paginator.num_pages-10, objects.paginator.num_pages+1)
        else:
            objects.paginator.display_page_range = range(objects.number-5, objects.number+5)
    else:
        objects.paginator.display_page_range = objects.paginator.page_range
    return objects


#######################
# gene context viewer #
#######################

def context_viewer(request, node_id, template_name):
    # get all the nodes in the subtree
    root = get_object_or_404(Phylonode, pk=node_id)
    nodes = Phylonode.objects.filter(phylotree=root.phylotree, left_idx__gt=root.left_idx, right_idx__lt=root.right_idx)
    peptide_ids = nodes.values_list('feature', flat=True)

    # the colors for the gene families
    before_colors = ['#afd45a', '#6cbfa9', '#7ea9d8', '#484848', '#ad8dc1', '#d783a7', '#f26f64', '#faa938', '#f0e24a', '#323232']
    focus_color = '#72ae35'
    after_colors = ['#39945c', '#3c73a4', '#67569b', '#ac3f65', '#d11b12', '#dea736', '#f55621', '#e4ddc9', '#fbc6d1', '#5ac9f7']
    color_map = {}

    # work our way to the genes and their locations
    mrna_ids = list(FeatureRelationship.objects.filter(subject__in=peptide_ids).values_list('object', flat=True))
    gene_ids = list(FeatureRelationship.objects.filter(subject__in=mrna_ids).values_list('object', flat=True))
    genes = list(Feature.objects.only('pk').filter(pk__in=gene_ids))

    # make the tracks
    tracks = []
    num = 4
    if 'num' in request.GET:
        try:
            num = int(request.GET['num'])
        except:
            pass
    if num > 10:
        num = 4

    # the gene_family cvterm
    family_term = list(Cvterm.objects.filter(name='gene family')[:1])[0]
    floc_ids = []
    for gene in genes:
        focus = list(Featureloc.objects.only('fmin', 'fmax', 'strand').filter(feature=gene)[:1])[0]
        floc_ids.append(focus.pk)
        # make the track
        track = {'focus' : focus}
        # set the family
        focus.family = root.phylotree
        # give the family a color
        color_map[focus.family.name] = {'color' : focus_color, 'id' : focus.family.pk}
        focus.family.color = focus_color;
        # get the focus position
        focus_pos = GeneOrder.objects.get(gene=gene)
        # get the genes that come before the focus
        before_genes = list(GeneOrder.objects.filter(chromosome=focus_pos.chromosome_id, number__lt=focus_pos.number, number__gte=focus_pos.number-num).values_list('gene', flat=True))
        track['before'] = list(Featureloc.objects.only('fmin', 'fmax', 'strand').filter(feature__in=before_genes).order_by('fmin'))
        for g in track['before']:
            floc_ids.append(g.pk)
            family_ids = list(Featureprop.objects.only('name').filter(type=family_term, feature=g.feature_id).values_list('value', flat=True))
            g.families = list(Phylotree.objects.only('name').filter(pk__in=map(int, family_ids)))
            for t in g.families:
                if t.name not in color_map:
                    color_map[t.name] = {'color' : before_colors.pop(), 'id' : t.pk}
                t.color = color_map[t.name]['color']
        # get the genes that come after the focus
        after_genes = list(GeneOrder.objects.filter(chromosome=focus_pos.chromosome_id, number__gt=focus_pos.number, number__lte=focus_pos.number+num).values_list('gene', flat=True))
        track['after'] = list(Featureloc.objects.only('fmin', 'fmax', 'strand').filter(feature__in=after_genes).order_by('fmin'))
        for g in track['after']:
            floc_ids.append(g.pk)
            family_ids = list(Featureprop.objects.only('name').filter(type=family_term, feature=g.feature_id).values_list('value', flat=True)) 
            g.families = list(Phylotree.objects.only('name').filter(pk__in=map(int, family_ids)))
            for t in g.families:
                if t.name not in color_map:
                    color_map[t.name] = {'color' : after_colors.pop(), 'id' : t.pk}
                t.color = color_map[t.name]['color']
        tracks.append(track)

    return render(request, template_name, {'tracks' : tracks, 'color_map' : color_map, 'floc_id_string' : ','.join(map(str,floc_ids))})


def context_viewer_demo(request, node_id, template_name):
    # make sure the node actually exists
    get_object_or_404(Phylonode, pk=node_id)
    # how many genes will be displayed?
    num = 4
    if 'num' in request.GET:
        try:
            num = int(request.GET['num'])
        except:
            pass
    if num > 10:
        num = 4
    # get all the nodes in the subtree
    root = get_object_or_404(Phylonode, pk=node_id)
    nodes = Phylonode.objects.filter(phylotree=root.phylotree, left_idx__gt=root.left_idx, right_idx__lt=root.right_idx)
    peptide_ids = nodes.values_list('feature', flat=True)
    # work our way to the genes and their locations
    mrna_ids = list(FeatureRelationship.objects.filter(subject__in=peptide_ids).values_list('object', flat=True))
    gene_ids = list(FeatureRelationship.objects.filter(subject__in=mrna_ids).values_list('object', flat=True))
    focus_genes = list(Feature.objects.only('pk','name').filter(pk__in=gene_ids))
    focus_genes_and_orientations = [ (g, 0) for g in focus_genes ]
    # generate the context view using the focus genes
    json, floc_id_string = context_viewer_json(focus_genes_and_orientations, num)
    return render(request, template_name, {'json' : json, 'floc_id_string' : floc_id_string})

# focus_genes is a list of tuples, the first element is a gene object, the second is the orientation (-1 flip, 1 leave as is, 0 flip if on reverse strand)
def context_viewer_json(focus_genes, num):
    ## get all the nodes in the subtree
    #root = get_object_or_404(Phylonode, pk=node_id)
    #nodes = Phylonode.objects.filter(phylotree=root.phylotree, left_idx__gt=root.left_idx, right_idx__lt=root.right_idx)
    #peptide_ids = nodes.values_list('feature', flat=True)

    ## work our way to the genes and their locations
    #mrna_ids = list(FeatureRelationship.objects.filter(subject__in=peptide_ids).values_list('object', flat=True))
    #gene_ids = list(FeatureRelationship.objects.filter(subject__in=mrna_ids).values_list('object', flat=True))
    #focus_genes = list(Feature.objects.only('pk','name').filter(pk__in=gene_ids))

    # what we'll use to construct the json
    tracks = []
    #families = {root.phylotree_id:root.phylotree.name}
    families = {}
    genes = []
    flocs = []

    # the gene_family cvterm
    y = 0
    family_term = list(Cvterm.objects.filter(name='gene family')[:1])[0]
    for gene in focus_genes:
        # get the focus featureloc
        focus_loc = list(Featureloc.objects.only('fmin', 'fmax', 'strand').filter(feature=gene[0])[:1])[0]
        flocs.append(focus_loc.pk)
        srcfeature = Feature.objects.only('name').get(pk=focus_loc.srcfeature_id)
        organism = Organism.objects.only('genus', 'species').get(pk=gene[0].organism_id)
        family_ids = list(Featureprop.objects.only('name').filter(type=family_term, feature=gene[0].feature_id).values_list('value', flat=True))
        family_objects = list(Phylotree.objects.only('name').filter(pk__in=map(int, family_ids)))
        for f in family_objects:
            if f.pk not in families:
                families[f.pk] = f.name
        # make sure the focus has a positive orientation
        flip = 1
        if (gene[1] == 0 and focus_loc.strand == -1) or gene[1] == -1:
            flip = -1
        tracks.append('{"chromosome_name":"'+srcfeature.name+'",'
                    +'"chromosome_id":'+str(srcfeature.feature_id)+','
                    +'"species_name":"'+organism.genus[0]+'.'+organism.species+'",'
                    +'"species_id":'+str(gene[0].organism_id)+'}')
        # add the gene entry for the focus
        genes.append('{"name":"'+gene[0].name+'",'
                    +'"id":'+str(gene[0].pk)+','
                    +'"fmin":'+str(focus_loc.fmin)+','
                    +'"fmax":'+str(focus_loc.fmax)+','
                    +'"x":'+str(num)+','
                    +'"y":'+str(y)+','
                    +'"strand":'+str(flip*focus_loc.strand)+','
                    +'"family":['+','.join(family_ids)+']}')
                    #+'"family":['+str(root.phylotree_id)+']}')
        # get the focus position
        focus_pos = GeneOrder.objects.get(gene=gene[0])
        # get the genes that come before the focus
        before_genes = list(GeneOrder.objects.filter(chromosome=focus_pos.chromosome_id, number__lt=focus_pos.number, number__gte=focus_pos.number-num).values_list('gene', flat=True))
        before_locs = list(Featureloc.objects.only('fmin', 'fmax', 'strand').filter(feature__in=before_genes).order_by('fmin'))
        # add gene entries for the before_locs
        offset = num-len(before_locs)
        x = ( offset if flip == 1 else (num*2)-offset )
        for l in before_locs:
            flocs.append(l.pk)
            family_ids = list(Featureprop.objects.only('name').filter(type=family_term, feature=l.feature_id).values_list('value', flat=True))
            genes.append('{"name":"'+l.feature.name+'",'
                        +'"id":'+str(l.feature_id)+','
                        +'"fmin":'+str(l.fmin)+','
                        +'"fmax":'+str(l.fmax)+','
                        +'"x":'+str(x)+','
                        +'"y":'+str(y)+','
                        +'"strand":'+str(flip*l.strand)+','
                        +'"family":['+','.join(family_ids)+']}')
            family_objects = list(Phylotree.objects.only('name').filter(pk__in=map(int, family_ids)))
            for f in family_objects:
                if f.pk not in families:
                    families[f.pk] = f.name
            x+=flip
        # get the genes that come after the focus
        after_genes = list(GeneOrder.objects.filter(chromosome=focus_pos.chromosome_id, number__gt=focus_pos.number, number__lte=focus_pos.number+num).values_list('gene', flat=True))
        after_locs = list(Featureloc.objects.only('fmin', 'fmax', 'strand').filter(feature__in=after_genes).order_by('fmin'))
        x = ( num+1 if flip == 1 else num-1 )
        for l in after_locs:
            flocs.append(l.pk)
            family_ids = list(Featureprop.objects.only('name').filter(type=family_term, feature=l.feature_id).values_list('value', flat=True))
            genes.append('{"name":"'+l.feature.name+'",'
                        +'"id":'+str(l.feature_id)+','
                        +'"fmin":'+str(l.fmin)+','
                        +'"fmax":'+str(l.fmax)+','
                        +'"x":'+str(x)+','
                        +'"y":'+str(y)+','
                        +'"strand":'+str(flip*l.strand)+','
                        +'"family":['+','.join(family_ids)+']}')
            family_objects = list(Phylotree.objects.only('name').filter(pk__in=map(int, family_ids)))
            for f in family_objects:
                if f.pk not in families:
                    families[f.pk] = f.name
            x+=flip
        y+=1

    # write the contents of the file
    json = '{"tracks":['+(','.join(tracks))+'],"families":['
    fams = []
    for key, value in families.iteritems():
        fams.append('{"name":"'+value+'","id":'+str(key)+'}')
    json += ','.join(fams)+'],"genes":['+','.join(genes)+']}'

    return json, ','.join(map(str, flocs))

def context_viewer_search(request, template_name):
    # make sure there's the right number of gene families
    if 'families' not in request.GET:
        raise Http404
    family_ids = request.GET['families'].split(',')
    num = len(family_ids)
    if num > 21 or num%2 == 0:
        raise Http404
    # get the focus gene of the query track
    #if 'focus' not in request.GET:
    #    raise Http404
    #query_focus = Feature.objects.only('pk', 'name').get(pk=request.GET['focus'])
    #if not query_focus:
    #    raise Http404
    #query_focus_loc = Featureloc.objects.only('strand').filter(feature=query_focus.feature_id)
    #if not query_focus:
    #    raise Http404
    #if query_focus_loc.strand == -1:
    #    feature_ids = feature_ids[::-1]
    # actually get the gene families
    gene_family_type = list(Cvterm.objects.only('pk').filter(name='gene family'))
    if len(gene_family_type) == 0:
        raise Http404
    gene_family_type = gene_family_type[0]
    # get all the genes associated with those families
    gene_families = Featureprop.objects.only('feature', 'value').filter(type=gene_family_type, value__in=family_ids)
    gene_family_map = {}
    for f in gene_families:
        gene_family_map[ f.feature_id ] = f.value
    feature_ids = gene_families.values_list('feature_id', flat=True)
    # get all the feature locations associated with the genes
    feature_locs = Featureloc.objects.only('feature', 'srcfeature').filter(feature__in=feature_ids)
    # get the features' chromosomes
    chromosome_ids = set(feature_locs.values_list('srcfeature_id', flat=True))
    # look for tracks on each chromosome
    #tracks = []
    focus_genes_and_orientations = []
    for ch in chromosome_ids:
        track_gene_ids = list(feature_locs.filter(srcfeature=ch).values_list('feature_id', flat=True))
        # get the ordering number of each track gene on the chromosome
        gene_orders = list(GeneOrder.objects.filter(chromosome=ch, gene__in=track_gene_ids).order_by('number'))
        # find genes that are close enough to make a track
        candidates = []
        for i in range(len(gene_orders)-1):
            gap = 0
            included = 1
            for j in range(i+1, len(gene_orders)):
                new_gap = gene_orders[ j ].number-gene_orders[ i ].number+1
                if new_gap > num:
                    j -= 1
                    # the set needs to have more than one member to be considered
                    if included > 1:
                        # make sure it's not a subset of an existing set
                        repeat = False
                        for c in candidates:
                            repeat = gene_orders[ j ].number <= gene_orders[ c[ 1 ] ].number
                            if repeat:
                                break
                        if not repeat:
                            candidates.append((i, j, gap))
                    break
                else:
                    gap = new_gap
                    included += 1
        # align the new genes with the query track
        for c in candidates:
            #if c[ 2 ] == num:
            #    print "adding a full track"
            #    tracks.append(list(GeneOrder.objects.filter(chromosome=c, number__gte=gene_orders[ c[ 0 ] ].number, number__lte=gene_orders[ c[ 1 ] ].number)))
            #else:
            play = num-c[ 2 ]
            first_number = gene_orders[ c[ 0 ] ].number
            best_play = 0
            best_hits = 0
            orientation = 1
            # two assumptions are being made here
            # 1) there is a family id for every gene on the query track (-1 for genes without families)
            # 2) the family ids are in the order they appeared on the track
            # even if there isn't play we should choose an orientation
            for i in range(play+1):
                # check the same orientation
                hits = 0
                for j in range(c[ 0 ], c[ 1 ]+1):
                    first = family_ids[ gene_orders[ j ].number-first_number+i ]
                    second = gene_family_map[ gene_orders[ j ].gene_id ]
                    if first == second:
                        hits += 1
                if hits > best_hits:
                    best_hits = hits
                    best_play = i
                    orientation = 1
                # check the reverse orientation
                hits = 0
                for j in range(c[ 0 ], c[ 1 ]+1):
                    first = family_ids[ (num-1)-(gene_orders[ j ].number-first_number+i) ]
                    second = gene_family_map[ gene_orders[ j ].gene_id ]
                    if first == second:
                        hits += 1
                if hits > best_hits:
                    best_hits = hits
                    best_play = i
                    orientation = -1
            # make a track using the best alignment... mind the gap
            #tracks.append(list(GeneOrder.objects.filter(chromosome=c, number__gte=first_number-best_play, number__lte=first_number-best_play+c[ 2 ]-1)))
            focus_id = list(GeneOrder.objects.filter(chromosome=ch, number=(first_number-best_play)+((num-1)/2)).values_list('gene_id', flat=True))
            # this is unfortunate
            if len(focus_id) > 0:
                focus = Feature.objects.only('pk', 'name').get(pk=focus_id[0])
                focus_genes_and_orientations.append((focus, orientation))

    # generate the context view using the focus genes
    json, floc_id_string = context_viewer_json(focus_genes_and_orientations, (num-1)/2)
    return render(request, template_name, {'json' : json, 'floc_id_string' : floc_id_string})

def context_gff_download(request):
    if 'flocs' not in request.GET:
        raise Http404

    flocs = list(Featureloc.objects.only('fmin', 'fmax', 'strand').filter(pk__in=map(int, request.GET['flocs'].split(','))))

    # write the file gff file
    chromosome_map = {}
    family_term = list(Cvterm.objects.filter(name='gene family')[:1])[0]
    myfile = StringIO.StringIO()
    myfile.write("##gff-version 3\n")
    for f in flocs:
        gene = Feature.objects.only('name').get(pk=f.feature_id)
        if f.srcfeature_id not in chromosome_map:
            chromosome_map[f.srcfeature_id] = Feature.objects.only('name').get(pk=f.srcfeature_id)
        family_ids = list(Featureprop.objects.filter(type=family_term, feature=f.feature_id).values_list('value', flat=True)) 
        families = list(Phylotree.objects.only('name').filter(pk__in=map(int, family_ids)).values_list('name', flat=True))
        families_str = ','.join(families)
        #for some reason, this diagnostic is throwing errors in some contexts
        #print chromosome_map[f.srcfeature_id].name+"\t.\tgene\t"+str(f.fmin)+"\t"+str(f.fmax)+"\t.\t"+("+" if f.strand == 1 else "-")+"\t.\tID="+gene.uniquename+";Name="+gene.uniquename+(";Family="+families_str if len(families) > 0 else "")
        myfile.write(chromosome_map[f.srcfeature_id].name+"\t.\tgene\t"+str(f.fmin)+"\t"+str(f.fmax)+"\t.\t"+("+" if f.strand == 1 else "-")+"\t.\tID="+gene.uniquename+";Name="+gene.uniquename+(";Family="+families_str if len(families) > 0 else "")+"\n")

    # generate the file
    response = HttpResponse(myfile.getvalue(), content_type='text/plain')
    response['Content-Length'] = myfile.tell()
    response['Content-Disposition'] = 'attachment; filename=context.gff'

    return response


