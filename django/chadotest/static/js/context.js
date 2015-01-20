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
                if( query_count >= query_length ) {
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

// custom colors used by the context viewer
//var context_color = d3.scale.ordinal().range(["#f0f8ff","#faebd7","#00ffff","#7fffd4","#f0ffff","#f5f5dc","#ffe4c4","#000000","#ffebcd","#0000ff","#8a2be2","#a52a2a","#deb887","#5f9ea0","#7fff00","#d2691e","#ff7f50","#6495ed","#fff8dc","#dc143c","#00ffff","#00008b","#008b8b","#b8860b","#a9a9a9","#006400","#a9a9a9","#bdb76b","#8b008b","#556b2f","#ff8c00","#9932cc","#8b0000","#e9967a","#8fbc8f","#483d8b","#2f4f4f","#2f4f4f","#00ced1","#9400d3","#ff1493","#00bfff","#696969","#696969","#1e90ff","#b22222","#fffaf0","#228b22","#ff00ff","#dcdcdc","#f8f8ff","#ffd700","#daa520","#808080","#008000","#adff2f","#808080","#f0fff0","#ff69b4","#cd5c5c","#4b0082","#fffff0","#f0e68c","#e6e6fa","#fff0f5","#7cfc00","#fffacd","#add8e6","#f08080","#e0ffff","#fafad2","#d3d3d3","#90ee90","#d3d3d3","#ffb6c1","#ffa07a","#20b2aa","#87cefa","#778899","#778899","#b0c4de","#ffffe0","#00ff00","#32cd32","#faf0e6","#ff00ff","#800000","#66cdaa","#0000cd","#ba55d3","#9370db","#3cb371","#7b68ee","#00fa9a","#48d1cc","#c71585","#191970","#f5fffa","#ffe4e1","#ffe4b5","#ffdead","#000080","#fdf5e6","#808000","#6b8e23","#ffa500","#ff4500","#da70d6","#eee8aa","#98fb98","#afeeee","#db7093","#ffefd5","#ffdab9","#cd853f","#ffc0cb","#dda0dd","#b0e0e6","#800080","#ff0000","#bc8f8f","#4169e1","#8b4513","#fa8072","#f4a460","#2e8b57","#fff5ee","#a0522d","#c0c0c0","#87ceeb","#6a5acd","#708090","#708090","#fffafa","#00ff7f","#4682b4","#d2b48c","#008080","#d8bfd8","#ff6347","#40e0d0","#ee82ee","#f5deb3","#ffffff","#f5f5f5","#ffff00","#9acd32"])
var context_color = d3.scale.ordinal().range([
"#7A2719",
"#5CE33C",
"#E146E9",
"#64C6DE",
"#E8B031",
"#322755",
"#436521",
"#DE8EBA",
"#5C77E3",
"#CEE197",
"#E32C76",
"#E54229",
"#2F2418",
"#E1A782",
"#788483",
"#68E8B2",
"#9E2B85",
"#E4E42A",
"#D5D9D5",
"#76404F",
"#589BDB",
"#E276DE",
"#92C535",
"#DE6459",
"#E07529",
"#A060E4",
"#895997",
"#7ED177",
"#916D46",
"#5BB0A4",
"#365167",
"#A4AE89",
"#ACA630",
"#38568F",
"#D2B8E2",
"#AF7B23",
"#81A158",
"#9E2F55",
"#57E7E1",
"#D8BD70",
"#316F4B",
"#5989A8",
"#D17686",
"#213F2C",
"#A6808E",
"#358937",
"#504CA1",
"#AA7CDD",
"#393E0D",
"#B02828",
"#5EB381",
"#47B033",
"#DF3EAA",
"#4E191E",
"#9445AC",
"#7A691F",
"#382135",
"#709628",
"#EF6FB0",
"#603719",
"#6B5A57",
"#A44A1C",
"#ABC6E2",
"#9883B0",
"#A6E1D3",
"#357975",
"#DC3A56",
"#561238",
"#E1C5AB",
"#8B8ED9",
"#D897DF",
"#61E575",
"#E19B55",
"#1F303A",
"#A09258",
"#B94781",
"#A4E937",
"#EAABBB",
"#6E617D",
"#B1A9AF",
"#B16844",
"#61307A",
"#ED8B80",
"#BB60A6",
"#E15A7F",
"#615C37",
"#7C2363",
"#D240C2",
"#9A5854",
"#643F64",
"#8C2A36",
"#698463",
"#BAE367",
"#E0DE51",
"#BF8C7E",
"#C8E6B6",
"#A6577B",
"#484A3A",
"#D4DE7C",
"#CD3488"]);
