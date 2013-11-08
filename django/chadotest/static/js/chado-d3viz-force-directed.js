/*
 * d3js visualization of gene families and gene ontology terms.
 */
var data;
var words4cloud;
var selectedNodes = [];
var forceLayoutSVG;
var wordCloudLayoutSVG;

 // when the DOM is ready, setup d3js layouts via this jquery initializer
$(document).ready( function() {
   
  // load the data_source_url global var, e.g.
  // /chado/d3viz_force_directed/phylonode/82449.json
  d3.json(data_source_url, function(error, json) {

    // the json data will be re-interpreted by various layouts, so save
    // to another json var here.
    data = buildGraph(json);

    setupForceLayout();
    setupWordCloudLayout();

    // add some info to the page heading
    $('#graph_info').text( 'phylonode_id: ' + phylonode_id + ' ');
    $('<a>',{
        text: '[source .json]',
        title: '[source .json]',
        href:  data.data_source_url,
    }).appendTo( $('#graph_info'));

    // hide the div with 'loading' animation
    $('#loading').hide();
    $('#selection_desc').show();
  });
});

/* massage the json from the generic format returned from the chado server
* into a format usable by the forcelayout graph. an array of nodes, and array
of links.

*/
function buildGraph(json) {
    var data = json;
    var nodeArray = []; // objects referenced by nodes, to constructruct node index
    data.nodes = [];
    data.links = [];

    // create graph nodes for polypeptides
    Object.keys(data.polypeptides).forEach( function(pp_id) {
        var pp = data.polypeptides[pp_id];
        data.nodes.push( {
            'name' : pp.name,
            'grp' : pp.organism_id, // use organism to color-code groups
            'desc' : '',
            'polypeptide_id' : pp_id,
        });
        nodeArray.push(pp);
    });

    // create graph nodes for cvterms
    Object.keys(data.cvterms).forEach( function(cvterm_id) {
        var cvterm = data.cvterms[cvterm_id];
        data.nodes.push( {
            'name' : cvterm.name,
            'grp' : 0, // cvterms will have the special group "0"
            'desc' : cvterm.definition,
            'cvterm_id' : cvterm_id,
        });
        nodeArray.push(cvterm);
    });

    // create links between the polypeps and the cvterms
    Object.keys(data.polypeptides).forEach( function(pp_id) {
        var pp = data.polypeptides[pp_id];
        if (! pp.cvterm_ids) { return; }
        pp.cvterm_ids.forEach( function(cvterm_id) {
            var cvterm = data.cvterms[cvterm_id];
            var link = {
                'source' : nodeArray.indexOf(pp),
                'target' : nodeArray.indexOf(cvterm),
                'value' : 5,
            };

            data.links.push(link);
        });
    });
    return data;
}


/*
d3.selection.prototype.moveToFront = function() {
  return this.each(function(){
    this.parentNode.appendChild(this);
  });
};
*/

Number.prototype.clamp = function(min, max) {
  return Math.min(Math.max(this, min), max);
};

var wordCloudLayout;

function setupWordCloudLayout() {
  var width = 800;
  var height = 200;

  $('#word_cloud').html('');

  words4cloud = getWordTags().map( function(d) {
    return { 'text' : d.key, 'size': d.value };
  });
  wordCount = Object.keys(words4cloud).length

  wordCloudLayoutSVG = d3.select('#word_cloud').append('svg')
    .attr('width', width)
    .attr('height', height);

  wordCloudLayout = d3.layout.cloud().size([width, height])
  .words(words4cloud)
  .padding(1)
  .rotate(function() { return ~~(Math.random() * 2) * 4; })
  .font('sans-serif')
  .fontSize(function(d) { 
    // size the word cloud text on a log scale, considering not only the word
    // count, but also the overall number of terms.
    var max = 30;
    var min = 8;
    var size = (min + min * (Math.log( 1 + d.size^2 / wordCount ))).clamp(min,max);
    return size;
  })
  .on('end', drawWordCloudLayout)
  .start();

  function drawWordCloudLayout(words) {

    wordCloudLayoutSVG
    .append('g')
    .attr('transform', 'translate(400,100)')
    .selectAll('text')
    .data(words)
    .enter().append('text')
    .style('font-size', function(d) { return d.size + 'px'; })
    .style('font-family', 'sans-serif')
    .style('fill', 'black')
    .attr('text-anchor', 'middle')
    .attr('transform', function(d) {
      return 'translate(' + [d.x, d.y] + ')rotate(' + d.rotate + ')';
    })
    .text(function(d) { return d.text; });
  } // drawWordCloudLayout()

} // setupWordCloudLayout()

function setupForceLayout() {

  var width = 800,
      height = 500;

  // setup a drag behavior, will be registered with the forcelayout below
  var drag = d3.behavior.drag()
  .origin(Object)
   .on('drag', dragmove)
   .on('dragstart', dragstart)
   .on('dragend', dragend);

  // Initialize tooltip plugin
  var tooltip = d3.tip().attr('class', 'd3-tip').html( function(d) { 
    return nodeShortDesc(d);
  });

  var linkDistance = (data.cvterms.length > 0) ? 
      linkDistance = 100 / Math.log( 1 + Object.keys(data.cvterms).length) :
      50;

  console.log('link distance: ' + linkDistance);

  var forceLayout = d3.layout.force()
  .charge( - linkDistance )
  .linkDistance( linkDistance )
  .size([width, height]);

  forceLayoutSVG = d3.select('#force_layout')
  .append('svg:svg')
  .attr('width', width)
  .attr('height', height)
  .call(tooltip)
  .call(drag);

  forceLayout
  .nodes(data.nodes)
  .links(data.links)
  .start();

  var link = forceLayoutSVG.selectAll('.link')
  .data(data.links)
  .enter().append('line')
  .attr('class', 'fl_link')
  .style('stroke-width', function(d) { return Math.sqrt(d.value); });

  var colorScale = d3.scale.category20();
  var nodes = forceLayoutSVG.selectAll('.node')
  .data(data.nodes)
  .enter().append('circle')
  .attr('r', 8)
  .attr('class', 'fl_node')
  .attr('fill', function(d) { 
    return (d.grp === 0) ? 'dimgrey' : colorScale(d.grp);
    });
  nodes
    .on('mouseover', tooltip.show )
    .on('mouseout', tooltip.hide );

  // this is the interactive mouse-drag which makes debugging difficult
  // this is enabled in most of the force directed layout examples though:
  // nodes.call(force.drag)

  /* dont add any title, because the tooltips plugin works better
  nodes.append('title')
  .text(function(d) { return d.name; });
  */

  /* this is what pins a node in position (.fixed)
  var drag = force.drag()
  .on('dragstart', dragstart);
  function dragstart(d) {
    d.fixed = true;
    d3.select(this).classed('fixed', true);
  }
  */

  // tick event is apparently the forcelayout simulation iterator
  forceLayout.on('tick', function() {
    link.attr('x1', function(d) { return d.source.x; })
    .attr('y1', function(d) { return d.source.y; })
    .attr('x2', function(d) { return d.target.x; })
    .attr('y2', function(d) { return d.target.y; });
    nodes.attr('cx', function(d) { return d.x; })
    .attr('cy', function(d) { return d.y; });
  });

  function selectForceLayoutNodes( d ) {
    $('#selection').text('');
    $('#word_cloud').text('');

    node = forceLayoutSVG.selectAll('circle.node')
    .data(data.nodes)
    .style('fill', function(d) {
      if( $.inArray(d, selectedNodes) != -1) { return 'yellow'; }
      return colorReMap[d.grp]; 
    });

    /* this re-tweaks the phsyics even more, dont do it
    force
    .nodes(data.nodes)
    .links(data.links)
    .start();
    */    
  } // selectForceLayoutNodes()

  // the d3 drag events may fire multiple times between mousedown and mouseup
  // so we need to track the current drag region and location
  var dragRegion = { x : 0, y : 0, width : 0, height: 0 }; // loc, width, height

  function dragstart(d) {
    d3.event.sourceEvent.stopPropagation(); // silence other listeners
    // reset the dragregion and recreate a drag_selection css element  
    var mouse = d3.mouse(this);
    dragRegion = { x : mouse[0], y : mouse[1], width : 0, height: 0 }; 
    forceLayoutSVG.append('rect')
      .attr({
        rx      : 6,
        ry      : 6,
        class   : 'drag_selection',
        x       : dragRegion.x,
        y       : dragRegion.y,
        width   : dragRegion.width,
        height  : dragRegion.height
      });
  }

  function dragmove(d) {
    var evt = d3.event;
    evt.sourceEvent.stopPropagation(); // silence other listeners

    // calculate the new dragRegion based on the current mouse position 
    // and it's delta since the last drag event
    var mouse = d3.mouse(this);
    var curX = mouse[0];
    var curY = mouse[1];

    // d3.event tracks the mouse deltas for us but not since the dragstart- so 
    // we need to track it here
    var delta = {
        x : curX - dragRegion.x,
        y : curY - dragRegion.y
    };

    if( delta.x < 1 || (delta.x * 2 < dragRegion.width)) {
      dragRegion.x = curX;
      dragRegion.width -= delta.x;
    } 
    else {
      dragRegion.width = delta.x;       
    }

    if( delta.y < 1 || (delta.y * 2 < dragRegion.height)) {
      dragRegion.y = curY;
      dragRegion.height -= delta.y;
    } 
    else {
      dragRegion.height = delta.y;      
    }

    // set the x,y,width,height attributes back onto the drag_selection element.
    forceLayoutSVG.select('rect.drag_selection').attr(dragRegion);

    // re-select any nodes within the current drag selection
    d3.selectAll('#force_layout circle .selected').classed('selected',false);
    selectedNodes = []
    d3.selectAll('#force_layout circle').each( function(node_data) {
      // find circle nodes (this) completely inside the selection frame 
      // dragRegion and set the selected class
      var circle = this;
      var r = circle.r.baseVal.value, // circle radius
        cx = circle.cx.baseVal.value,
        cy = circle.cy.baseVal.value;
      var selectThis = ( cx - r >= dragRegion.x &&
                         cx + r <= dragRegion.x + dragRegion.width &&
                         cy - r >= dragRegion.y &&
                         cy + r <= dragRegion.y + dragRegion.height );
      if( selectThis ) {
        selectedNodes.push(node_data);
        d3.select( this ).classed( 'selected', true);
      } else {
        d3.select( this ).classed( 'selected', false);
      }
    }); // d3.selectAll

  }

  function dragend(d) {
    d3.event.sourceEvent.stopPropagation(); // silence other listeners
    dragRegion = { x: 0, y: 0, width: 0, height: 0}; // reset the dragRegion
    forceLayoutSVG.selectAll('rect.drag_selection').remove();
    updateSelectionDesc();
    setupWordCloudLayout();
  }

} // end setupForceLayout()

function getWordTags() {
  var scanNodes = selectedNodes;
  if( ! scanNodes || scanNodes.length == 0) { 
    //console.log('warning: no selectedNodes, using all data.nodes ' + data.nodes.length);
    scanNodes = data.nodes;
  }

  // punctuation = /[!"&()*+,-\.\/:;<=>?\[\\\]^`\{|\}~]+/g
  // removed - / : from punctuation, it seems to appear a lot in GO terms.

  var text = '';
  var punctuation = /[!'"&()*+,\.<=>?\[\\\]^`\{|\}~]+/g;
  var wordSeparators = /[\s\u3031-\u3035\u309b\u309c\u30a0\u30fc\uff70]+/g;
  var maxLength = 30;
  var stopWords = /^(i|me|my|myself|we|us|our|ours|ourselves|you|your|yours|yourself|yourselves|he|him|his|himself|she|her|hers|herself|it|its|itself|they|them|their|theirs|themselves|what|which|who|whom|whose|this|that|these|those|am|is|are|was|were|be|been|being|have|has|had|having|do|does|did|doing|will|would|should|can|could|ought|i'm|you're|he's|she's|it's|we're|they're|i've|you've|we've|they've|i'd|you'd|he'd|she'd|we'd|they'd|i'll|you'll|he'll|she'll|we'll|they'll|isn't|aren't|wasn't|weren't|hasn't|haven't|hadn't|doesn't|don't|didn't|won't|wouldn't|shan't|shouldn't|can't|cannot|couldn't|mustn't|let's|that's|who's|what's|here's|there's|when's|where's|why's|how's|a|an|the|and|but|if|or|because|as|until|while|of|at|by|for|with|about|against|between|into|through|during|before|after|above|below|to|from|up|upon|down|in|out|on|off|over|under|again|further|then|once|here|there|when|where|why|how|all|any|both|each|few|more|most|other|some|such|no|nor|not|only|own|same|so|than|too|very|say|says|said|shall)$/;

  scanNodes.forEach( function (node) {
    var cvterm_ids = [];
    if( node.cvterm_id ) {
        // this node is 1 cvterm
        cvterm_ids.push(node.cvterm_id);
    }
    else if (node.polypeptide_id) {        
        // this is a polypeptie node
        var pp = data.polypeptides[node.polypeptide_id];
        if ( pp.cvterm_ids && pp.cvterm_ids.length > 0 ) {
            // having 1 or more cvterm ids
            cvterm_ids = cvterm_ids.concat( pp.cvterm_ids );
        } 
        else {
            // dont add the polypeptide name to the word cloud - per adf
            //text += ' ' + pp.name;
        }
    }

    cvterm_ids.forEach( function(cvterm_id) {
        var cvterm = data.cvterms[cvterm_id];
        text += ' ' + cvterm.name;
        text += ' ' + cvterm.definition
    });
  });

  var tags = {};
  var cases = {};
  text.split(wordSeparators).forEach(function(word) {
    word = word.replace(punctuation, '');
    if (stopWords.test(word.toLowerCase())) return;
    word = word.substr(0, maxLength);
    cases[word.toLowerCase()] = word;
    tags[word = word.toLowerCase()] = (tags[word] || 0) + 1;              
  });
  tags = d3.entries(tags).sort(function(a, b) { return b.value - a.value; });
  tags.forEach(function(d) { d.key = cases[d.key]; });
  return tags;

} // end getWordTags()

  /*
  * scan through the selectedNodes and write some descriptive info to the
  * #selection.
  */
function updateSelectionDesc() {
  $('#selection_desc').text( selectedNodes.length + ' items selected:');
  var buffer = [];
  $.each( selectedNodes, function(idx, node) {
    if( node.polypeptide_id ) {
        var pp = data.polypeptides[ node.polypeptide_id ];
        var organism = data.organisms[ pp.organism_id ];
        var markup = pp.name + '(' + organism.common_name + ')' 
        markup = markup.replace(/\\/g,'')
        buffer.push( $('<div></div>').html(markup));
    }
    else if( node.cvterm_id ) {
        var cvterm = data.cvterms[node.cvterm_id];
        var cv = data.cvtypes[cvterm.cv_id];
        var markup = cvterm.name+ ' (' + cv.name + ') '+ '</br>'+ cvterm.definition;
        markup = markup.replace(/\\/g,'');
        buffer.push( $('<div></div>').html(markup));
    }
  });  
  $('#selection_desc').append(buffer);
}

function clearSelectionDesc() {
   $('#selection_desc').html('');
}

function clearWordCloud() {
  $('#word_cloud').html('');
}

/*
* generate a short string, for the tooltip plugin
*/
function nodeShortDesc( node ) {
    if ( node.polypeptide_id ) {
        // check the polypeptides hash for details about this node
        var pp = data.polypeptides[ node.polypeptide_id ];
        var organism = data.organisms[ pp.organism_id ];
        return (pp.name + '<br/>'+ organism.common_name).replace(/\\/g,'')
    }
    else if(node.cvterm_id) {
        // check the cvterms hash or details about this node
        var cvterm = data.cvterms[node.cvterm_id];
        var cv_id =  cvterm.cv_id;
        var cv = data.cvtypes[cv_id]
        var descr = cvterm.definition;
        if(descr.length > 100) {
            descr = cvterm.definition.substr(0,100) + '...';
        }
        return (cvterm.name + ' (' + cv.name + ')<br/>' + descr).replace(/\\/g,'')
    }
}



