from chado.models import Organism, Cvterm, Phylotree, Phylonode
from chado.models import Feature, FeatureCvterm, FeatureRelationship
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
import simplejson
from django.core.urlresolvers import reverse

#
# viz : render the template having the d3js visualization. it will fetch the
# json after it loads (or in response to external events or web-service-ish
# things)
#
def viz(request, phylonode_id):
    return render(request, 
                  'd3viz_force_directed/viz.html',
                  { 'phylonode_id' : phylonode_id });

#
# phylonode_json: return json of the gene tree and GO terms for this node. the
# json will be consumed by the view in viz(), and possibly other services. the
# json is not specific to d3js, so the data will need to be massaged a bit on
# the client side for visualization.
#
def phylonode_json(request, phylonode_id):

    phylonode = get_object_or_404(Phylonode, pk=phylonode_id)

    # use the left and right index to get the phylonode's child nodes directly:
    nodes = Phylonode.objects.filter(phylotree=phylonode.phylotree, 
                                     left_idx__gte=phylonode.left_idx,
                                     right_idx__lte=phylonode.right_idx)

    # phylonodes point directly to polypeptides, and these are the things that
    # our feature_cvterms are also pointing to
    polypeptide_pks = nodes.values_list('feature_id', flat=True) 

    if (polypeptide_pks.count() == 0):
        json_msg = {
        'error':
        'Polypeptides not available for any species in subtree'
        }
        return HttpResponse(simplejson.dumps(json_msg),
                            content_type = 'application/javascript')

    polypeptides = Feature.objects.filter(pk__in=polypeptide_pks) 

    json_organisms = {}
    json_polypeptides = {}
    json_go_terms = {}
    json_cv_types = {}

    for pp in polypeptides:

        json_polypeptides[ pp.feature_id ] = {
            'feature_id' : pp.feature_id,
            'name': pp.name,
            'organism_id' : pp.organism_id,
#            'cvterm_ids': pp_cvterm_ids,
        }

        if pp.organism_id not in json_organisms:
            json_organisms[ pp.organism_id ] = { 
            'organism_id' : pp.organism_id,
            'abbreviation' : pp.organism.abbreviation,
            'common_name' : pp.organism.common_name,
            'genus' : pp.organism.genus,
            'species' : pp.organism.species,
            'comment' : pp.organism.comment,
        }

        cvterms_rels = FeatureCvterm.objects.filter(feature_id=pp.feature_id)
        cvterm_pks = cvterms_rels.values_list('cvterm_id')
        if(cvterm_pks.count() == 0):
            continue
        cvterms = Cvterm.objects.filter(pk__in=cvterm_pks)
        pp_cvterm_ids = []
        
        for cvterm in cvterms:
            pp_cvterm_ids.append(cvterm.cvterm_id)
            if cvterm.cvterm_id not in json_go_terms:
                json_go_terms[ cvterm.cvterm_id ] = {
                    'cvterm_id' : cvterm.cvterm_id,
                    'name' : cvterm.name,
                    'definition' : cvterm.definition,
                    'cv_id' : cvterm.cv_id
                }
            if cvterm.cv_id not in json_cv_types:
                json_cv_types[ cvterm.cv_id ] = {
                  'cv_id' : cvterm.cv_id,
                  'name' : cvterm.cv.name,
                  'definition' : cvterm.cv.definition,
                }
        json_polypeptides[ pp.feature_id ][ 'cvterm_ids' ] = pp_cvterm_ids

    json_data = { 
        'phylonode_id' : phylonode_id,
        'data_source_url' : request.build_absolute_uri(),
        'organisms' : json_organisms,
        'polypeptides' : json_polypeptides,
        'cvterms' : json_go_terms,
        'cvtypes' : json_cv_types,
    }
    return HttpResponse(simplejson.dumps(json_data, sort_keys=True, indent=1), 
                        content_type = 'application/javascript')

