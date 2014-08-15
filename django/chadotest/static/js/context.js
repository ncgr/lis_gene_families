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

// uses alignment to convert synteny data into viewer data
function synteny_to_alignment( data, slignment ) {

}
