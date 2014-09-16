// a helper function that moves things to an back of the svg element
d3.selection.prototype.moveToBack = function() { 
    return this.each(function() { 
        var firstChild = this.parentNode.firstChild; 
        if (firstChild) { 
            this.parentNode.insertBefore(this, firstChild); 
        } 
    }); 
};

// show tips in all plots
function show_tips( gene_selection, rail_selection ) {
    d3.selectAll(".gene").style("opacity", .1);
	if( gene_selection !== undefined ) {
		gene_selection.style("opacity", 1);
		gene_selection.selectAll(".tip").style("visibility", "visible");
	}
	d3.selectAll(".rail").style("opacity", .1);
	if( rail_selection !== undefined ) {
		rail_selection.style("opacity", 1);
		rail_selection.selectAll(".tip").style("visibility", "visible");
	}
}

// hide tips in all plots
function hide_tips( gene_selection, rail_selection ) {
	d3.selectAll(".gene").style("opacity", 1);
	if( gene_selection !== undefined ) {
		gene_selection.selectAll(".tip").style("visibility", "hidden");
	}
	d3.selectAll(".rail").style("opacity", 1);
	if( rail_selection !== undefined ) {
		rail_selection.selectAll(".tip").style("visibility", "hidden");
	}
}

// return the length of the trakcs based on the data
function get_track_length( data ) {
	return d3.max( data.groups, function(d) { 
        return d3.max( d.genes, function(e) {
            return +e.x;
        }); 
    })+1;
}

// return a family id to name map
function get_family_name_map( data ) {
	// make a family id name map
	var family_names = {};
	for( var i = 0; i < data.families.length; i++ ) {
		var fam = data.families[i];
		family_names[ fam.id ] = fam.name;
	}
	return family_names;
}

// return a family size map
function get_family_size_map( data ) {
	// make a family size map
	var family_sizes = {};
	for( var i = 0; i < data.groups.length; i++ ) {
		for( var j = 0; j < data.groups[i].genes.length; j++ ) {
			var family = data.groups[i].genes[j].family;
			if( family in family_sizes ) {
				family_sizes[ family ] += 1;
			} else {
				family_sizes[ family ] = 1;
			}
		}
	}
	return family_sizes;
}

// merges multiple alignments and sets coordinates for the context viewer
function merge_alignments( context_data, selected_groups, alignments ) {
    var num_groups = context_data.groups.length;
    // update the context data with the alignment
    for( var k = 0; k < alignments.length; k++ ) {
        var query_count = 0,
            query_length = context_data.groups[0].genes.length,
            pre_query = 0,
            insertion_count = 0,
            alignment = alignments[k],
            index = num_groups+k;
        context_data.groups.push(selected_groups[k]);
        context_data.groups[index].genes = [];
        for( var i = 0; i < alignment[0].length; i++ ) {
            // keep track of how many selected genes come before the query genes
            if( alignment[0][i] == null && query_count == 0 ) {
                pre_query++;
            // it must be an insertion
            } else if( alignment[0][i] == null ) {
                // position the genes that come after the query genes
                if( query_count > query_length ) {
                    alignment[1][i].x = query_count++;
                    alignment[1][i].y = k+1;
                    context_data.groups[index].genes.push(alignment[1][i]);
                // track how many genes were inserted
                } else {
                    insertion_count++;
                }
            // a deletion
            } else if( alignment[1][i] == null ) {
                query_count++;
            // an alignment
            } else {
                // position the genes that came before the query
                if( pre_query > 0 ) {
                    for( var j = 0; j < pre_query; j++ ) {
                        alignment[1][j].x = -1*(pre_query-(j+1));
                        alignment[1][j].y = k+1;
                        context_data.groups[index].genes.push(alignment[1][j]);
                    }
                    pre_query = 0;
                // position the genes that go between query genes
                } else if( insertion_count > 0 ) {
                    var step = 1/(insertion_count+1);
                    for( var j = i-insertion_count; j < i; j++ ) {
                        alignment[1][j].x = query_count+(step*(i-j))-1;
                        alignment[1][j].y = k+1;
                        context_data.groups[index].genes.push(alignment[1][j]);
                    }
                    insertion_count = 0;
                }
                alignment[1][i].x = query_count++;
                alignment[1][i].y = k+1;
                context_data.groups[index].genes.push(alignment[1][i]);
            }
        }
    }
}
