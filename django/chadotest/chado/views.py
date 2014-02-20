
# import http stuffs
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils import simplejson
from django.core.urlresolvers import reverse
# file generation stuffs
import cStringIO as StringIO
# pagination stuffs
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
# for passing messages
from django.contrib import messages
# import our models and helpers
from chado.models import Organism, Cvterm, Feature, Phylotree, Featureloc, Phylonode, FeatureRelationship, Analysisfeature, FeatureCvterm
from django.db.models import Count
# make sure we have the csrf token!
from django.views.decorators.csrf import ensure_csrf_cookie
# search stuffs
import re
from django.db.models import Q


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


def search(request, template_name):
    # if there's a query
    if 'q' in request.GET and request.GET['q'].strip():
        query_string = request.GET['q']
        term_query = get_query(query_string, ['cvterm__name', 'cvterm__definition',])
        results = FeatureCvterm.objects.filter(term_query)
        return render(request, template_name, {'query_string' : query_string, 'results' : paginate(request, results, 'search_num'), 'result_nums' : RESULT_NUMS, 'selected' : get_results(request)})
    # redirect if there wasn't a query
	return redirect(request.META.get('HTTP_REFERER', '/chado/'))

def search_organism(request, template_name):
    # if there's a query
    if 'q' in request.GET and request.GET['q'].strip():
        organism_ids = Feature.objects.filter(pk__in=get_results(request).keys()).values_list('organism_id', flat=True)
        result_organisms = Organism.objects.filter(pk__in=organism_ids)
        return render(request, template_name, {'query_string' : request.GET['q'], 'result_organisms' : paginate(request, result_organisms, 'search_organism_num'), 'result_nums' : RESULT_NUMS})
    # redirect if there wasn't a query
	return redirect(request.META.get('HTTP_REFERER', '/chado/'))

def search_msa(request, template_name):
    # if there's a query
    if 'q' in request.GET and request.GET['q'].strip():
        # get the msas
        features = Feature.objects.filter(pk__in=get_results(request).keys())
        msa_ids = Featureloc.objects.filter(feature__in=features).values_list('srcfeature', flat=True)
        result_msas = Feature.objects.filter(type__name='consensus', pk__in=msa_ids)
        return render(request, template_name, {'query_string' : request.GET['q'], 'result_msas' : paginate(request, result_msas, 'search_msa_num'), 'result_nums' : RESULT_NUMS, 'selected' : get_results(request, 'msa')})
    # redirect if there wasn't a query
	return redirect(request.META.get('HTTP_REFERER', '/chado/'))

def search_phylo(request, template_name):
    # if there's a query
    if 'q' in request.GET and request.GET['q'].strip():
        # get the msas
        features = Feature.objects.filter(pk__in=get_results(request).keys())
        tree_ids = Phylonode.objects.filter(feature__in=features).values_list('phylotree', flat=True)
        result_trees = Phylotree.objects.filter(pk__in=tree_ids)
        return render(request, template_name, {'query_string' : request.GET['q'], 'result_trees' : paginate(request, result_trees, 'search_phylo_num'), 'result_nums' : RESULT_NUMS, 'selected' : get_results(request, 'phylo')})
    # redirect if there wasn't a query
	return redirect(request.META.get('HTTP_REFERER', '/chado/'))

def search_feature(request, template_name, who):
    if 'q' in request.GET and request.GET['q'].strip():
        result_features = None
        if who == 'phylo':
            #phylonode = get_object_or_404(Phylonode, pk=phylonode_id)
            result_features = Feature.objects.filter(pk__in=Phylonode.objects.filter(phylotree__pk__in=get_results(request, 'phylo')).values_list('feature_id', flat=True))
        else:
            #consensus_ids = get_object_or_404(Feature, pk=feature_id)
            result_features = Feature.objects.filter(pk__in=Featureloc.objects.filter(srcfeature__pk__in=get_results(request, 'msa').keys()).values_list('feature_id', flat=True))
        return render(request, template_name, {'query_string' : request.GET['q'], 'result_features' : paginate(request, result_features, 'search_feature_num'), 'result_nums' : RESULT_NUMS})
    # rediect if there wasn't a query
    return redirect(request.META.get('HTTP_REFERER', '/chado/'))

def initialize_results_session(request, who=''):
    request.session['results_'+who] = {}

def get_results(request, who=''):
    if 'results_'+who not in request.session:
        request.session['results_'+who] = {}
    return request.session['results_'+who]

def search_add_result_ajax(request, who):
    if request.is_ajax():
        result = None
        try:
            if who == 'phylo':
                result = Phylotree.objects.get(pk=request.GET['result'])
            else:
                result = Feature.objects.get(pk=request.GET['result'])
        except DoesNotExist:
            return HttpResponseBadRequest('Bad Request')
        if 'results_'+who not in request.session:
            initialize_results_session(request, who)
        request.session['results_'+who][result.pk] = result.name
        return HttpResponse('OK')
    return HttpResponseBadRequest('Bad Request')

def search_remove_result_ajax(request, who):
    if request.is_ajax():
        result = None
        try:
            if who == 'phylo':
                result = Phylotree.objects.get(pk=request.GET['result'])
            else:
                result = Feature.objects.get(pk=request.GET['result'])
        except DoesNotExist:
            return HttpResponseBadRequest('Bad Request')
        if 'results_'+who not in request.session:
            initialize_results_session(request, who)
        if result.pk in request.session['results_'+who]:
            del request.session['results_'+who][result.pk]
        return HttpResponse('OK')
    return HttpResponseBadRequest('Bad Request')

def search_clear_results_ajax(request, who):
    if request.is_ajax():
        initialize_results_session(request, who)
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
            xmltree += '<name>'+node.label+'</name>'
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

    # add the nodes to the xml tree
    xml, num_leafs = add_node(xml, root, nodes, 0)

    # close the tree's tags
    xml += '</phylogeny></phyloxml>'
    return xml, num_leafs


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
			node = Phylonode.objects.get(pk=request.GET['phylonode'])
			slidedict = {}
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
			return HttpResponse(simplejson.dumps(slidedict), content_type = 'application/javascript; charset=utf8')
		except:
			return HttpResponse("bad request")
                return HttpResponse("bad request")


def phylo_newick(request, phylotree_id, template_name):
    tree = get_object_or_404(Phylotree, pk=phylotree_id)
    return render(request, template_name, {'tree' : tree})


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


