
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
    consensus = get_object_or_404(Cvterm, name="consensus_region")
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
        result_msas = Feature.objects.filter(type__name='consensus_region', pk__in=msa_ids)
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
    return render(request, template_name, {'msas' : paginate(request, Feature.objects.filter(type__name='consensus_region'), 'msa_num'), 'result_nums' : RESULT_NUMS})


def msa_view(request, feature_name, template_name):
    consensus = Feature.objects.get(name=feature_name)
    #consensus = get_object_or_404(Feature, pk=feature_id)
    featurelocs = Featureloc.objects.filter(srcfeature=consensus)
    # I'm sure there's a better way to get a count of the organisms but the values method was giving me trouble
    organism_pks = list(featurelocs.values_list('feature__organism', flat=True))
    organisms = Organism.objects.filter(pk__in=organism_pks)
    num_organisms = []
    for o in organisms:
        num_organisms.append({'organism' : o.common_name, 'count' : organism_pks.count(o.pk)})
    return render(request, template_name, {'consensus' : consensus, 'featurelocs' : featurelocs, 'num_organisms' : simplejson.dumps(list(num_organisms))})


def msa_consensus(request, feature_name, template_name):
    #consensus = get_object_or_404(Feature, pk=feature_id)
    consensus = Feature.objects.get(name=feature_name)
    featurelocs = Featureloc.objects.filter(srcfeature=consensus)
    return render(request, template_name, {'consensus' : consensus, 'featurelocs' : featurelocs})


def msa_consensus_download(request, feature_name):
    # get consensus stuffs
    #consensus = get_object_or_404(Feature, pk=feature_id)
    consensus = Feature.objects.get(name=feature_name)
    featurelocs = Featureloc.objects.filter(srcfeature=consensus)

    # write the file to be downloaded
    myfile = StringIO.StringIO()
    if consensus.residues:
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


def phylo_view(request, phylotree_name, template_name):
    # get trees stuffs
    #tree = get_object_or_404(Phylotree, pk=phylotree_id)
    tree = Phylotree.objects.get(name=phylotree_name)
    xml, num_leafs = phylo_xml(tree, '')

    # we've got the goods
    return render(request, template_name, {'tree' : tree, 'xml' : xml, 'num_leafs' : num_leafs})


def phylo_view_ajax(request):
	if request.is_ajax():
		try:
                        import re;
                        if 'phylonode' in request.GET:
			    node = get_object_or_404(Phylonode, pk=request.GET['phylonode'])
			    tree = get_object_or_404(Phylotree, pk=node.phylotree_id)
                        elif 'gene' in request.GET:
                            node = get_object_or_404(Feature, pk=request.GET['gene'])
                            node.label = node.name
			slidedict = {}
            # external nodes
			if node.label:
                                import sys
                                sys.stderr.write("label is " + node.label + "\n")
				slidedict['label'] = node.label
				slidedict['meta'] = "This is meta information for "+node.label
                                slidedict['links'] = []
                                #FIXME: will need to check dbxref when we have more than phytozome trees
                                slidedict['links'].append({'Phytozome Gene Family':'http://phytozome.jgi.doe.gov/pz/portal.html#!showCluster?search=1&detail=0&method=4835&searchText=clusterid:'+tree.name})
                                m = re.match('^([a-z]{5,5})\.(.*?)(\.[0-9]+)?$', node.label);
                                species=m.group(1)
                                gene=m.group(2)
                                if m.group(3):
                                    transcript=gene+m.group(3)
                                sys.stderr.write("species is " + species)
                                sys.stderr.write("gene is " + gene)
                                sys.stderr.write("transcript is " + transcript)
                                if species == 'medtr':
                                    slidedict['links'].append({'LIS Mt4.0 GBrowse':'http://medtr.comparative-legumes.org/gb2/gbrowse/Mt4.0?name='+gene})
                                    slidedict['links'].append({'LIS Mt3.5.1 GBrowse':'http://medtr.comparative-legumes.org/gb2/gbrowse/Mt3.5.1?name='+gene})
                                    slidedict['links'].append({'JCVI JBrowse':'http://www.jcvi.org/medicago/jbrowse/?data=data%2Fjson%2Fmedicago&loc='+transcript})
                                    slidedict['links'].append({'Mt HapMap':'http://www.medicagohapmap.org/fgb2/gbrowse/mt35/?name='+gene})
                                    slidedict['links'].append({'Phytozome':'http://phytozome.jgi.doe.gov/pz/portal.html#!results?search=0&crown=1&star=0&method=4432&searchText='+gene})
                                    slidedict['links'].append({'LegumeIP':'http://plantgrn.noble.org/LegumeIP/getseq.do?seq_acc=IMGA|'+gene})
                                    #for whatever reason, medicago seems to have gotten their nomenclature into NCBI
                                    slidedict['links'].append({'NCBI Gene':'http://www.ncbi.nlm.nih.gov/gene/?term='+gene})
                                    #but that doesn't mean that it gave other people the message!
                                    slidedict['links'].append({'Genomicus':'http://www.genomicus.biologie.ens.fr/genomicus-plants/cgi-bin/search.pl?view=default&amp;query=MTR_'+gene.replace("Medtr","")})

                                elif species == 'glyma':
                                    slidedict['links'].append({'Soybase':'http://soybase.org/gb2/gbrowse/gmax2.0/?name='+gene})
                                    slidedict['links'].append({'Phytozome':'http://phytozome.jgi.doe.gov/pz/portal.html#!results?search=0&crown=1&star=0&method=4433&searchText='+gene})
                                    slidedict['links'].append({'SoyKB':'http://soykb.org/gene_card.php?gene='+gene})
                                    slidedict['links'].append({'Genomicus':'http://www.genomicus.biologie.ens.fr/genomicus-plants/cgi-bin/search.pl?view=default&amp;query='+gene})
                                elif species == 'phavu':
                                    slidedict['links'].append({'LIS GBrowse':'http://phavu.comparative-legumes.org/gb2/gbrowse/Pv1.0/?name='+gene})
                                    slidedict['links'].append({'Phytozome':'http://phytozome.jgi.doe.gov/pz/portal.html#!results?search=0&crown=1&star=0&method=3253&searchText='+gene})
                                elif species == 'arath':
                                    slidedict['links'].append({'TAIR':'http://www.arabidopsis.org/servlets/TairObject?type=locus&name='+gene})
                                    slidedict['links'].append({'Phytozome':'http://phytozome.jgi.doe.gov/pz/portal.html#!results?search=0&crown=1&star=0&method=2296&searchText='+gene})
                                elif species == 'orysa':
                                    slidedict['links'].append({'MSU':'http://rice.plantbiology.msu.edu/cgi-bin/gbrowse/rice/?name='+gene})
                                    slidedict['links'].append({'Phytozome':'http://phytozome.jgi.doe.gov/pz/portal.html#!results?search=0&crown=1&star=0&method=3301&searchText='+gene})
                                elif species == 'zeama':
                                    slidedict['links'].append({'MaizeGDB':'http://maizegdb.org/cgi-bin/displaygenemodelrecord.cgi?id='+gene})
                                    slidedict['links'].append({'Gramene':'http://www.gramene.org/Zea_mays/Gene/Summary?g='+gene})
                                    slidedict['links'].append({'Phytozome':'http://phytozome.jgi.doe.gov/pz/portal.html#!results?search=0&crown=1&star=0&method=4431&searchText='+gene})
                                elif species == 'solly':
                                    slidedict['links'].append({'Sol Genomics Network':'http://solgenomics.net/gbrowse/bin/gbrowse/ITAG2.3_genomic/?name='+gene+'&h_feat='+gene})
                                    slidedict['links'].append({'Phytozome':'http://phytozome.jgi.doe.gov/pz/portal.html#!results?search=0&crown=1&star=0&method=3308&searchText='+gene})
                                elif species == 'vitvi':
                                    slidedict['links'].append({'Genoscope':'http://www.genoscope.cns.fr/cgi-bin/ggb/vitis/12X/gbrowse/vitis/?name='+gene})
                                    slidedict['links'].append({'Phytozome':'http://phytozome.jgi.doe.gov/pz/portal.html#!results?search=0&crown=1&star=0&method=2299&searchText='+gene})
                                elif species == 'ambtr':
                                    slidedict['links'].append({'Phytozome':'http://phytozome.jgi.doe.gov/pz/portal.html#!results?search=0&crown=1&star=0&method=4851&searchText='+transcript})
                                slidedict['links'].append({'google':'http://www.google.com/search?q='+gene})
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
                                #consensus_feature = Feature.objects.get(uniquename='consn.'+node.phylotree.name);
                                #slidedict['links'].append({'MSA':'/chado/msa/'+str(consensus_feature.feature_id)})
                                # load the context viewer with each node in the subtree as a focus gene 
                                #slidedict['links'].append({'Context Viewer':'/chado/context_viewer/demo'+str(node.pk)})
                                slidedict['links'].append({'Context Viewer':'/chado/context_viewer/'+str(node.pk)})
			return HttpResponse(simplejson.dumps(slidedict), content_type = 'application/javascript; charset=utf8')
		except:
			return HttpResponse("bad request")
                return HttpResponse("bad request")


def phylo_newick(request, phylotree_name, template_name):
    #tree = get_object_or_404(Phylotree, pk=phylotree_id)
    tree = Phylotree.objects.get(name=phylotree_name)
    return render(request, template_name, {'tree' : tree, 'newick' : generate_phylo_newick(tree)})


def phylo_xml_download(request, phylotree_name):
    # get the tree
    #tree = get_object_or_404(Phylotree, pk=phylotree_id)
    tree = Phylotree.objects.get(name=phylotree_name)
    xml, num_leafs = phylo_xml(tree, "")

    # write the file to be downloaded
    myfile = StringIO.StringIO()
    myfile.write(xml);

    # generate the file
    response = HttpResponse(myfile.getvalue(), content_type='text/plain')
    response['Content-Length'] = myfile.tell()
    response['Content-Disposition'] = 'attachment; filename='+tree.name+'_xml'

    return response


def phylo_newick_download(request, phylotree_name):
    # get the tree
    #tree = get_object_or_404(Phylotree, pk=phylotree_id)
    tree = Phylotree.objects.get(name=phylotree_name)

    # write the file to be downloaded
    myfile = StringIO.StringIO()
    myfile.write(generate_phylo_newick(tree)+"\n")

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
        myfile.write("##sequence-region " + species.genus+"_"+species.species+":"+c.name + " 1 " + str(c.seqlen)+"\n");
        

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

# keep!
def context_viewer(request, node_id, template_name):
    # make sure the node actually exists
    get_object_or_404(Phylonode, pk=node_id)
    # how many genes will be displayed?
    num = 10
    if 'num' in request.GET:
        try:
            num = int(request.GET['num'])
        except:
            pass
    if num > 40:
        num = 40
    # get all the nodes in the subtree
    root = get_object_or_404(Phylonode, pk=node_id)
    nodes = Phylonode.objects.filter(phylotree=root.phylotree, left_idx__gt=root.left_idx, right_idx__lt=root.right_idx)
    peptide_ids = nodes.values_list('feature', flat=True)
    # work our way to the genes and their locations
    mrna_ids = list(FeatureRelationship.objects.filter(subject__in=peptide_ids).values_list('object', flat=True))
    gene_ids = list(FeatureRelationship.objects.filter(subject__in=mrna_ids).values_list('object', flat=True))
    focus_genes = list(Feature.objects.only('pk','name').filter(pk__in=gene_ids))
    focus_genes = [ g for g in focus_genes ]
    # generate the context view using the focus genes
    json, floc_id_string, focus_family = context_viewer_json_refactor(focus_genes, num)
    return render(request, template_name, {'json' : json, 'floc_id_string' : floc_id_string, 'focus_family' : focus_family})

# focus_genes is a list of tuples, the first element is a gene object, the second is the orientation (-1 flip, 1 leave as is, 0 flip if on reverse strand)
def context_viewer_json_refactor(focus_genes, num):

    # what we'll use to construct the json
    groups = []
    #families = {root.phylotree_id:root.phylotree.name}
    families = {}
    flocs = []

    # the gene_family cvterm
    y = 0
    family_term = list(Cvterm.objects.filter(name='gene family')[:1])[0]
    focus_family_id = None
    for gene in focus_genes:
        genes = []
        # get the focus featureloc
        focus_loc = list(Featureloc.objects.only('fmin', 'fmax', 'strand').filter(feature=gene)[:1])[0]
        flocs.append(focus_loc.pk)
        srcfeature = Feature.objects.only('name').get(pk=focus_loc.srcfeature_id)
        organism = Organism.objects.only('genus', 'species').get(pk=gene.organism_id)
        family_id = list(Featureprop.objects.only('name').filter(type=family_term, feature=gene.feature_id).values_list('value', flat=True))
        if len(family_id) > 0:
            focus_family_id = family_id = family_id[0]
            if family_id not in families:
                families[family_id] = '{"name":"'+family_id+'", "id":"'+family_id+'"}'
        # make sure the focus has a positive orientation
        flip = 1
        if focus_loc.strand == -1:
            flip = -1
        group = '{"chromosome_name":"'+srcfeature.name+'", "chromosome_id":'+str(srcfeature.feature_id)+', "species_name":"'+organism.genus[0]+'.'+organism.species+'", "species_id":'+str(gene.organism_id)+', "genes":['
        # add the gene entry for the focus
        genes.append('{"name":"'+gene.name+'",'
                    +'"id":'+str(gene.pk)+','
                           +'"fmin":'+str(focus_loc.fmin)+','
                           +'"fmax":'+str(focus_loc.fmax)+','
                           +'"x":'+str(num)+','
                           +'"y":'+str(y)+','
                           +'"strand":'+str(flip*focus_loc.strand)+','
                           +'"family":"'+family_id+'"}')
                           #+'"family":['+str(root.phylotree_id)+']}')
        # get the focus position
        focus_pos = GeneOrder.objects.get(gene=gene)
        # get the genes that come before the focus
        before_genes = list(GeneOrder.objects.filter(chromosome=focus_pos.chromosome_id, number__lt=focus_pos.number, number__gte=focus_pos.number-num).values_list('gene', flat=True))
        before_locs = list(Featureloc.objects.only('fmin', 'fmax', 'strand').filter(feature__in=before_genes).order_by('fmin'))
        # add gene entries for the before_locs
        offset = num-len(before_locs)
        x = ( offset if flip == 1 else (num*2)-offset )
        for l in before_locs:
            flocs.append(l.pk)
            family_id = list(Featureprop.objects.only('name').filter(type=family_term, feature=l.feature_id).values_list('value', flat=True))
            if len(family_id) > 0:
                family_id = family_id[0]
                if family_id not in families:
                        families[family_id] = '{"name":"'+family_id+'", "id":"'+family_id+'"}'
            else:
                family_id = ''
            genes.append('{"name":"'+l.feature.name+'",'
                        +'"id":'+str(l.feature_id)+','
                               +'"fmin":'+str(l.fmin)+','
                               +'"fmax":'+str(l.fmax)+','
                               +'"x":'+str(x)+','
                               +'"y":'+str(y)+','
                               +'"strand":'+str(flip*l.strand)+','
                               +'"family":"'+family_id+'"}')
            x+=flip
        # get the genes that come after the focus
        after_genes = list(GeneOrder.objects.filter(chromosome=focus_pos.chromosome_id, number__gt=focus_pos.number, number__lte=focus_pos.number+num).values_list('gene', flat=True))
        after_locs = list(Featureloc.objects.only('fmin', 'fmax', 'strand').filter(feature__in=after_genes).order_by('fmin'))
        x = ( num+1 if flip == 1 else num-1 )
        for l in after_locs:
            flocs.append(l.pk)
            family_id = list(Featureprop.objects.only('name').filter(type=family_term, feature=l.feature_id).values_list('value', flat=True))
            if len(family_id) > 0:
                family_id = family_id[0]
                if family_id not in families:
                   families[family_id] = '{"name":"'+family_id+'", "id":"'+family_id+'"}'
            else:
                family_id = ''
            genes.append('{"name":"'+l.feature.name+'",'
                        +'"id":'+str(l.feature_id)+','
                        +'"fmin":'+str(l.fmin)+','
                        +'"fmax":'+str(l.fmax)+','
                        +'"x":'+str(x)+','
                        +'"y":'+str(y)+','
                        +'"strand":'+str(flip*l.strand)+','
                        +'"family":"'+family_id+'"}')
            x+=flip
        y+=1
        group += ','.join(genes)+']}'
        groups.append(group)

    # write the contents of the file
    json = '{"families":['+','.join(families.values())+'], "groups":['+','.join(groups)+']}'

    return json, ','.join(map(str, flocs)), focus_family_id

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
        for family_id in family_ids:
            if family_id not in families:
                #adf: what sense does this make?
                families[family_id] = family_id
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
            for family_id in family_ids:
                if family_id not in family_ids:
                    #adf : what sense does this make
                    families[family_id] = family_id
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
            for family_id in family_ids:
                if family_id not in families:
                    #adf : what sense does this make?
                    families[family_id] = family_id
            x+=flip
        y+=1

    # write the contents of the file
    json = '{"tracks":['+(','.join(tracks))+'],"families":['
    fams = []
    for key, value in families.iteritems():
        fams.append('{"name":"'+value+'","id":"'+str(key)+'"}')
    json += ','.join(fams)+'],"genes":['+','.join(genes)+']}'

    return json, ','.join(map(str, flocs))


def context_viewer_search( request, template_name, focus_name=None ):
    # get the focus gene of the query track
    focus = Feature.objects.only( 'pk', 'name' ).get( name=focus_name )
    if not focus:
        raise Http404
    focus_id=focus.pk
    focus_order = list( GeneOrder.objects.filter( gene=focus ) )
    if len( focus_order ) == 0:
        raise Http404
    focus_order = focus_order[ 0 ]

    # get the parameters for the algorithm
    single = 'single' in request.GET and request.GET['single'] == 'true'

    # how many neighbors should there be?
    num = 4
    if 'num' in request.GET:
        try:
            num = int( request.GET['num'] )
        except:
            pass
    # how many matched_families should there be?
    num_matched_families = 3
    if 'num_matched_families' in request.GET:
        try:
            num_matched_families = int( request.GET['num_matched_families'] )
        except:
            pass
    max_num = 40
    max_length = max_num
    if 'length' in request.GET:
        if request.GET['length'] == 'double':
            max_length = 2*num+1
        else:
            try:
                max_length = int( request.GET['length'] )
            except:
               pass
    max_genes = max_num*2+1
    if num > max_num:
        num = max_num

    # what are the parameters for smith-waterman?
    match = 1
    if 'match' in request.GET:
        try:
            match = int( request.GET['match'] )
        except:
            pass
    mismatch = 0 
    if 'mismatch' in request.GET:
        try:
            mismatch = int( request.GET['mismatch'] )
        except:
            pass
    gap = -1
    if 'gap' in request.GET:
        try:
            gap = int( request.GET['gap'] )
        except:
            pass


    # get the focus gene of the query track
    focus = Feature.objects.only( 'pk', 'name' ).get( pk=focus_id )
    if not focus:
        raise Http404
    focus_order = list( GeneOrder.objects.filter( gene=focus ) )
    if len( focus_order ) == 0:
        raise Http404
    focus_order = focus_order[ 0 ]

    # get the gene family type
    gene_family_type = list( Cvterm.objects.only( 'pk' ).filter( name='gene family' ) )
    if len( gene_family_type ) == 0:
        raise Http404
    gene_family_type = gene_family_type[ 0 ]

    # get the neighbors of focus via their ordering
    neighbor_orders = GeneOrder.objects.only( ).filter( chromosome=focus_order.chromosome_id, number__gte=focus_order.number-num, number__lte=focus_order.number+num ).order_by( 'number' )
    neighbor_ids = neighbor_orders.values_list( 'gene_id', flat=True )

    # actually get the gene families
    neighbor_families = Featureprop.objects.only( 'value' ).filter( type=gene_family_type, feature__in=neighbor_ids )#.values_list( 'value', flat=True )
    neighbor_family_map = dict( ( o.feature_id, o.value ) for o in neighbor_families )
    neighbor_families = neighbor_families.values_list( 'value', flat=True )
    family_ids = []
    query_families = {}
    for n in neighbor_families:
        if n not in family_ids:
            family_ids.append( n )
            query_families[n] = 1

    # make the first (query) track
    # get the gene names
    neighbor_features = Feature.objects.only( 'name' ).filter( pk__in=neighbor_ids )
    neighbor_name_map = dict( (o.pk, o.name ) for o in neighbor_features )
    # get the gene flocs
    neighbor_flocs = Featureloc.objects.only( 'fmin', 'fmax', 'strand' ).filter( feature__in=neighbor_ids )
    neighbor_floc_map = dict( ( o.feature_id, o ) for o in neighbor_flocs )
    # get the track chromosome
    chromosome = Feature.objects.only( 'name' ).filter( pk=neighbor_floc_map[ int( focus.pk ) ].srcfeature_id )
    chromosome = chromosome[ 0 ]
    # get the track organism
    organism = Organism.objects.only( 'genus', 'species' ).filter( pk=chromosome.organism_id )
    organism = organism[ 0 ]
    # generate the json for the genes
    genes = []
    query_align = []
    for i in range( len( neighbor_orders ) ):
        g = neighbor_orders[ i ].gene_id
        family = str( neighbor_family_map[ g ] ) if g in neighbor_family_map else ''
        floc = neighbor_floc_map[ g ]
        genes.append('{"name":"'+neighbor_name_map[ g ]+'", "id":'+str( g )+', "family":"'+family+'", "fmin":'+str( floc.fmin )+', "fmax":'+str( floc.fmax )+', "strand":'+str( floc.strand )+', "x":'+str( i )+', "y":0}')
        query_align.append( ( g, family ) )
    query_group = '{"species_name":"'+organism.genus[ 0 ]+'.'+organism.species+'", "species_id":'+str( organism.pk )+', "chromosome_name":"'+chromosome.name+'", "chromosome_id":'+str( chromosome.pk )+', "genes":['+','.join( genes )+']}'

    # find all genes with the same families (excluding the query genes)
    related_genes = Featureprop.objects.only( 'feature' ).filter( type=gene_family_type, value__in=neighbor_families ).exclude(feature_id__in=neighbor_ids)
    related_gene_ids = related_genes.values_list('feature', flat=True )
    #related_genes = Feature.objects.only().filter( pk__in=related_gene_ids )
    #id_gene_map = dict( ( o.pk, o ) for o in related_genes )
    #get rid of genes from query

    # get the orders (and chromosomes) of the genes
    related_orders = GeneOrder.objects.only( 'number' ).filter( gene__in=related_gene_ids )
    gene_order_map = dict( ( o.gene_id, o.number ) for o in related_orders )
    related_family_map = dict( ( o.feature_id, o.value ) for o in related_genes )

    # find the chromosomes the genes are on
    #chromosome_relations = list(FeatureRelationship.objects.filter(subject__in=related_genes))

    # group the genes by their chromosomes
    chromosome_genes_map = {}
    #for o in chromosome_relations:
    for o in related_orders:
        if o.chromosome_id in chromosome_genes_map:
            #chromosome_genes_map[ o.chromosome_id ].append( id_gene_map[ o.gene_id ] )
            chromosome_genes_map[ o.chromosome_id ].append( o.gene_id )
        else:
            #chromosome_genes_map[ o.chromosome_id ] = [ id_gene_map[ o.gene_id ] ]
            chromosome_genes_map[ o.chromosome_id ] = [ o.gene_id ]

    # fetch all the chromosome names (organism_id and pk are implicit)
    chromosomes = Feature.objects.only( 'name' ).filter( pk__in=chromosome_genes_map.keys() )
    id_chromosome_map = dict( ( o.pk, o ) for o in chromosomes )

    # fetch the chromosome organisms
    organism_ids = chromosomes.values_list( 'organism_id', flat=True )
    organisms = Organism.objects.only( 'genus', 'species' ).filter( pk__in=organism_ids )
    id_organism_map = dict( ( o.pk, o.genus[ 0 ]+'.'+o.species ) for o in organisms )

    # userful variables for finding similar tracks
    #adf: though apparently not used anymore...
    query_size = num*2+1
    stratification_coefficient = max_genes/( query_size*1.0 )
    num_results = 20

    chromosome_candidates = {}

    # a function that will help us order genes
    #def get_gene_order( g ):
    #    return gene_order_map[ g.pk ]
    def get_gene_order( g_id ):
        return gene_order_map[ g_id ]

    #adf: not used?
    # a function that will help us order subsets by distance
    def get_candidate_distance( c ):
        return c['distance']

    # construct tracks for each chromosome
    for chromosome_id, genes in chromosome_genes_map.iteritems():
        if len( genes ) < 2:
            continue
        genes.sort( key=get_gene_order )
        # find all subsets of the genes of maximum order-gap size between first and last members <= max_length and whose symmetric difference and intersection with all other such sets are non-empty
        candidates = []
        last_j = 0
        for i in range( len( genes ) ):
            prev_size = 0
            matched_families = {}
            #import sys
            #sys.stderr.write("key is " + str(genes[i])+"\n")
            if genes[i] in related_family_map and query_families[related_family_map[genes[i]]] :
                matched_families[ related_family_map[ genes[i] ] ] = 1
            for j in range( i+1, len( genes ) ):
                if genes[j] in related_family_map and query_families[related_family_map[genes[j]]] :
                    matched_families[ related_family_map[ genes[j] ] ] = 1
                #size = gene_order_map[ genes[ j ].pk ]-gene_order_map[ genes[ i ].pk ]
                size = gene_order_map[ genes[ j ] ]-gene_order_map[ genes[ i ] ]
                #if size < max_num:
                if size < max_length :
                    prev_size = size
                    if j+1 == len( genes ) and j > last_j and len(matched_families.keys()) >= num_matched_families :
                        candidates.append( { 'first':i, 'last':j, 'size':prev_size, 'hits':j-i+1 } )
                        last_j = j
                else:
                    # no subsets allowed!
                    if prev_size > 0 and j-1 > last_j and len(matched_families.keys()) >= num_matched_families :
                        candidates.append( { 'first':i, 'last':j-1, 'size':prev_size, 'hits':j-i } )
                        last_j = j-1
                    break
        if candidates:
            chromosome_candidates[ chromosome_id ] = candidates

    # a helper function for accessing gene families during the alignment
    def accessor( gene_tuple ):
        return gene_tuple[1]

    # a helper function for creating new tuple elements during the alignment
    def new_element( value ):
        return ( None, value )

    # fill in the tracks
    groups = [ query_group ]
    y = 1
    for chromosome_id, candidates in chromosome_candidates.iteritems():
        for c in candidates:
            # get all the gene ids
            track_gene_ids = GeneOrder.objects.only( '' ).filter( chromosome=chromosome_id, number__gte=gene_order_map[ chromosome_genes_map[ chromosome_id ][ c[ 'first' ] ] ], number__lte=gene_order_map[ chromosome_genes_map[ chromosome_id ][ c[ 'last' ] ] ] ).values_list( 'gene_id', flat=True )

            # get all the gene families
            track_families = Featureprop.objects.only( 'value' ).filter( type=gene_family_type, feature__in=track_gene_ids )
            gene_family_map = dict( ( o.feature_id, o.value ) for o in track_families )
            for f in track_families.values_list( 'value', flat=True ):
                if f not in family_ids:
                    family_ids.append( f )

            # create a list of tuples to feed to smith and waterman
            align = []
            for g in track_gene_ids:
                if g in gene_family_map:
                    align.append( ( g, gene_family_map[ g ] ) )
                else:
                    align.append( ( g, -1 ) )

            # run smith-waterman on the forward and reverse of the track
            forward_score, forward_alignment = smith_waterman( align, query_align, accessor, new_element, match = match, mismatch = mismatch, gap = gap )
            reverse_score, reverse_alignment = smith_waterman( align[::-1], query_align, accessor, new_element, match = match, mismatch = mismatch, gap = gap )

            # only keep the remaining genes
            track_gene_ids = []
            if reverse_score > forward_score:
                reverse_alignment = reverse_alignment[::-1]
                for t in reverse_alignment:
                    if t[ 0 ]:
                        track_gene_ids.append( t[ 0 ] )
            else:
                for t in forward_alignment:
                    if t[ 0 ]:
                        track_gene_ids.append( t[ 0 ] )

            # exclude tracks with only one gene
            if len( track_gene_ids ) < 2:
                continue

            # exclude single family tracks
            if not single:
                unique_families = set( gene_family_map.values() )
                if( len( unique_families ) < 2 ):
                    continue


            # get all the gene names
            track_names = Feature.objects.only( 'name' ).filter( pk__in=track_gene_ids )
            gene_name_map = dict( ( o.pk, o.name ) for o in track_names ) 

            # get all the gene featurelocs
            track_locs = Featureloc.objects.only( 'fmin', 'fmax', 'strand' ).filter( feature__in=track_gene_ids )
            gene_loc_map = dict( ( o.feature_id, o ) for o in track_locs )

            genes = []
            for i in range( len( track_gene_ids ) ):
                g = track_gene_ids[ i ]
                family = gene_family_map[ g ] if g in gene_family_map else ''
                genes.append('{"name":"'+gene_name_map[ g ]+'", "id":'+str( g )+', "family":"'+family+'", "fmin":'+str( gene_loc_map[ g ].fmin )+', "fmax":'+str( gene_loc_map[ g ].fmax )+', "x":'+str( i )+', "y":'+str( y )+', "strand":'+str( gene_loc_map[ g ].strand )+'}')
            group = '{"species_name":"'+str( id_organism_map[ id_chromosome_map[ chromosome_id ].organism_id ] )+'", "species_id":'+str( id_chromosome_map[ chromosome_id ].organism_id )+', "chromosome_name":"'+id_chromosome_map[ chromosome_id ].name+'", "chromosome_id":'+str( chromosome_id )+', "genes":['+','.join( genes )+']}'
            groups.append( group )

            y += 1

    families = []
    for f in family_ids :
        families.append('{"name":"'+f+'", "id":"'+f+'"}')

    json = '{"families":['+','.join( families )+'], "groups":['

    json += ','.join( groups )+']}'

    return render(request, template_name, {'json' : json, 'single' : single, 'num' : num, 'length' : max_length, 'match' : match, 'mismatch' : mismatch, 'gap' : gap, 'num_matched_families' : num_matched_families})

# https://github.com/kevinakwok/bioinfo/tree/master/Smith-Waterman
def smith_waterman( seqA, seqB, accessor, new_element, match = 1, mismatch = 0, gap = -1 ):
    seqB = seqB[:-1]

    #seqA = "-"+seqA
    seqA.insert( 0, new_element('-') )
    #seqB = "-"+seqB
    seqB.insert( 0, new_element('-') )

    #Sets the values for match, mismatch, and gap.
    #match = 1 
    #mismatch = 0 
    #gap = -1

    row = len(seqA)
    col = len(seqB)

    #Creates blank matrix
    def create_matrix(row,col):
        A = [0] * row 
        for i in range(row):
            A[i] = [0] * col 
        return A

    def isMatch(i,j):
        if accessor( seqA[i] ) == accessor( seqB[j] ):
            matchVal = match
        else:
            matchVal = mismatch
        return matchVal

    #Returns the new value if diagonal is used
    def diag(i,j):
        return A[i-1][j-1] + isMatch(i,j)

    #Returns the new value if up is used
    def up(i,j):
        return A[i-1][j] + isMatch(i,j) + gap 

    #Returns the new value if left is used
    def left(i,j):
        return A[i][j-1] + isMatch(i,j) + gap 

    #Fills matrix with correct scores.
    def complete_matrix(row,col):
        for i in range(1,row):
            for j in range(1,col):
                A[i][j] = max(0,diag(i,j),up(i,j),left(i,j))
        return A

    #FInd the highest scoring cell.
    def get_max(A):
        local_max = [[0,0]]
        for i in range(row):
            for j in range(col):
                if A[i][j] == A[local_max[0][0]][local_max[0][1]]:
                    local_max.append([i,j])
                elif A[i][j] > A[local_max[0][0]][local_max[0][1]]:
                    local_max = [[i,j]]
        return local_max

    #Gives you the next location.
    def get_next(A,location):
        i = location[0]
        j = location[1]
        maxVal = max(A[i-1][j-1],A[i-1][j]+gap,A[i][j-1]+gap)
        if A[i-1][j-1] == maxVal:
            return [i-1,j-1]
        #Is this the right ordering of the three?
        elif A[i][j-1]+gap == maxVal:
            return [i,j-1]
        else:
            return [i-1,j]

    #Traces the path back given starting location
    def trace_back(A,tracer):
        if A[tracer[len(tracer)-1][0]][tracer[len(tracer)-1][1]] == 0:
            return tracer
        next_cell = get_next(A,tracer[len(tracer)-1])
        #tracer.insert(0,next_cell)
        tracer.append(next_cell)
        return trace_back(A,tracer)

    #Uses tracer to return final sequence
    def get_seq(A,tracer,k,seq):
        if k == 0:
            original_sequence = seqA
        else:
            original_sequence = seqB
        N = len(tracer)
        for i in range(0,N-1):
            if tracer[i][k] == tracer[i+1][k]+1:
                #seq = seq + original_sequence[tracer[i][k]]
                seq.append( original_sequence[tracer[i][k]] )
            elif tracer[i][k] == tracer[i+1][k]:
                #seq = seq + "-"
                seq.append( new_element('-') )
        return seq

    #Shows the relevant lines for matching pairs
    def get_middle(finalA,finalB):
        middle = ""
        for k in range(len(finalA)):
            mid = " "
            if finalA[k] == finalB[k]:
                mid = "|"
            middle = middle + mid
        return middle

    # find the local alignment
    A = create_matrix(row,col)

    A = complete_matrix(row,col)

    answers = get_max(A)

    # return the first highest scoring local alignment and it's score
    tracer = trace_back( A, [answers[0]] )
    alignment = get_seq( A, tracer, 0, [])
    alignment = alignment[::-1]
    score = A[answers[0][0]][answers[0][1]]
    return score, alignment


def context_viewer_synteny(request, template_name, focus_id=None):
    # get the focus gene of the query track
    focus = Feature.objects.only('pk', 'name').get(pk=focus_id)
    if not focus:
        raise Http404
    focus_order = list(GeneOrder.objects.filter(gene=focus))
    if len(focus_order) == 0:
        raise Http404
    focus_order = focus_order[0]
    # get the gene family type
    gene_family_type = list(Cvterm.objects.only('pk').filter(name='gene family'))
    if len(gene_family_type) == 0:
        raise Http404
    gene_family_type = gene_family_type[0]
    # how many neighbors should there be?
    num = 10
    if 'num' in request.GET:
        try:
            num = int(request.GET['num'])
        except:
            pass
    if num > 10:
        num = 10
    # get the neighbors of focus via their ordering
    neighbor_orders = GeneOrder.objects.filter(chromosome=focus_order.chromosome_id, number__gte=focus_order.number-num, number__lte=focus_order.number+num).order_by('number')
    neighbor_ids = neighbor_orders.values_list('gene_id', flat=True)
    # actually get the gene families
    neighbor_featureprops = Featureprop.objects.only('feature', 'value').filter(type=gene_family_type, feature__in=neighbor_ids)
    # dictionaryify the results
    neighbor_family_map = dict( (o.feature_id, o.value) for o in neighbor_featureprops )
    neighbor_family_ids = neighbor_featureprops.values_list("value", flat=True)
    json = '{"families":['
    families = []
    for f in neighbor_family_ids:
        families.append('{"name":"'+f+'", "id":"'+f+'"}')
    json += ','.join(families)+']'
    # make a y axis lookup for the query track in the scatter plot
    family_members = {}
    for f in neighbor_family_ids:
        family_members[f] = []
    # populate the lookup
    neighbor_json = {}
    x = 0
    for n in neighbor_orders:
        if n.gene_id in neighbor_family_map:
            #neighbor_json[n.gene_id] = '{"name":"'+n.gene.name+'", "id":'+str(n.gene_id)+', "x":'+str(x)+', "y":0, "family":'+str(neighbor_family_map[n.gene_id])+','
            neighbor_json[n.gene_id] = '{"name":"'+n.gene.name+'", "id":'+str(n.gene_id)+', "family":"'+str(neighbor_family_map[n.gene_id])+'",'
            x+=1
            family_members[neighbor_family_map[n.gene_id]].append(n.gene_id)
    # get all the genes associated with those families
    gene_families = Featureprop.objects.only('feature', 'value').filter(type=gene_family_type, value__in=neighbor_family_ids)
    gene_family_map = dict( (o.feature_id, o.value) for o in gene_families )
    # get all the feature locations associated with the genes
    gene_locs = Featureloc.objects.only('feature', 'srcfeature', 'fmin', 'fmax', 'strand').filter(feature__in=gene_family_map.keys())
    # dictionaryify the positions
    #gene_position_map = dict( (o.feature_id, o.fmin+(o.fmax-o.fmin)) for o in gene_locs )
    gene_floc_map = dict( (o.feature_id, {'fmin':o.fmin, 'fmax':o.fmax, 'position': o.fmin+(o.fmax-o.fmin), 'strand': o.strand}) for o in gene_locs )
    # get the gene names
    gene_names = Feature.objects.only('name').filter(pk__in=gene_family_map.keys())
    gene_name_map = dict( (o.feature_id, o.name) for o in gene_names )
    # get the genes' chromosomes
    chromosome_ids = set(gene_locs.values_list('srcfeature_id', flat=True))
    chromosome_gene_map = {}
    for ch in chromosome_ids:
        chromosome_gene_map[ch] = []
    for f in gene_locs:
        chromosome_gene_map[f.srcfeature_id].append(f.feature_id)
    chromosome_names = Feature.objects.only('name').filter(pk__in=chromosome_ids)
    # get the chromosome organisms
    organism_ids = chromosome_names.values_list('organism_id', flat=True)
    organisms = list(Organism.objects.only('genus', 'species').filter(pk__in=organism_ids))
    # dictionaryify the results
    organism_map = dict( (o.pk, o.genus[0]+"."+o.species) for o in organisms )
    # dictionaryify the results
    chromosome_name_map = dict( (o.pk, [o.name, o.organism_id, organism_map[o.organism_id]]) for o in chromosome_names )
    json += ', "groups":[{"species_name": "'+str(chromosome_name_map[focus_order.chromosome_id][2])+'", "species_id": '+str(chromosome_name_map[focus_order.chromosome_id][1])+', "chromosome_id": '+str(focus_order.chromosome_id)+', "chromosome_name": "'+chromosome_name_map[focus_order.chromosome_id][0]+'", "genes" : ['
    # construct a scatter plot for each chromosome
    plots = []
    for ch, ch_gene_ids in chromosome_gene_map.iteritems():
        if len(ch_gene_ids) > 1:
            plot = '{"species_name": "name", "species_id": 0, "chromosome_id":'+str(ch)+', "chromosome_name": "'+chromosome_name_map[ch][0]+'", '
            points = []
            for gene_id in ch_gene_ids:
                family = gene_family_map[gene_id]
                for m in family_members[family]:
                    f = gene_floc_map[gene_id]
                    points.append('{"x":'+str(f['position'])+', '
                                 +'"y":'+str(gene_floc_map[m]['position'])+', '
                                 +'"family":"'+str(family)+'", '
                                 +'"id":'+str(gene_id)+', '
                                 +'"fmin":'+str(f['fmin'])+', '
                                 +'"fmax":'+str(f['fmax'])+', '
                                 +'"name":"'+gene_name_map[gene_id]+'", '
                                 +'"strand":'+str(f['strand'])+'}')
                if gene_id in neighbor_family_map:
                    f = gene_floc_map[gene_id]
                    neighbor_json[gene_id] += '"x":'+str(f['position'])+', "y": '+str(f['position'])+', "fmin":'+str(f['fmin'])+', "fmax":'+str(f['fmax'])+', "strand":'+str(f['strand'])+'}'
            plot += '"genes":['+','.join(points)+']}'
            plots.append(plot)
    json += ','.join(neighbor_json.values())+']},'
    json += ','.join(plots) + ']}'

    return render(request, template_name, {'json' : json})

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
        families_str = ','.join(family_ids)
        #for some reason, this diagnostic is throwing errors in some contexts
        #print chromosome_map[f.srcfeature_id].name+"\t.\tgene\t"+str(f.fmin)+"\t"+str(f.fmax)+"\t.\t"+("+" if f.strand == 1 else "-")+"\t.\tID="+gene.uniquename+";Name="+gene.uniquename+(";Family="+families_str if len(families) > 0 else "")
        myfile.write(chromosome_map[f.srcfeature_id].name+"\t.\tgene\t"+str(f.fmin)+"\t"+str(f.fmax)+"\t.\t"+("+" if f.strand == 1 else "-")+"\t.\tID="+gene.uniquename+";Name="+gene.uniquename+(";Family="+families_str if len(family_ids) > 0 else "")+"\n")

    # generate the file
    response = HttpResponse(myfile.getvalue(), content_type='text/plain')
    response['Content-Length'] = myfile.tell()
    response['Content-Disposition'] = 'attachment; filename=context.gff'

    return response


