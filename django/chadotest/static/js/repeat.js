/*
 * this is an implementation of the repeat algorithm, by Durbin et al
 * the code is derived from smtih.js
 */


// define the default accessor
function default_accessor( item ) {
    return item;
}

// let's compute scores over and over again...
var s = function( first, second, scoring ) {
	if( first === second ) {
		return scoring.match;
	} return scoring.mismatch; // passed value should be negative
}


var repeat_align = function( sequence, reference, accessor, scoring ) {
    // populate the matrix
    var rows = sequence.length + 1; // first item is at index 1
    var cols = reference.length + 1; // first item is at index 1
    var a = Array.matrix( cols, rows, 0 );
    var i; // cols
    var choice = [ 0, 0, 0, 0 ];
    
    for( i=1; i<cols; i++ ) { // first column is all 0's
        // handle unmatched regions and ends of matches
        var scores = a[i-1].map(function(score, j) {
            if( j > 0 ) {
                return score - scoring.threshold;
            } return score;
        });
        a[i][0] = scores.max();
        // handle starts of matches and extensions
        for( j=1; j<rows; j++ ) {
            choice[0] = a[i][0];
            choice[1] = a[i-1][j-1] + s( accessor(reference[i-1]), accessor(sequence[j-1]), scoring );
            choice[2] = a[i-1][j] + scoring.gap; // adding because passed value should be negative
            choice[3] = a[i][j-1] + scoring.gap;
            a[i][j] = choice.max();
        }
    }
 
    // traceback - make a track for each qualified path in the matrix   
    i = cols-1; // start in the extra cell
    var j = 0; // rows
    var alignments = [];
    var index = -1;
    var score_diag, score_up, scroe_left;
    var saving = false;

    while( !(i == 0 && j == 0) ) {
        if( j == 0 ) {
            var max = a[i].max();
            var max_j = a[i].lastIndexOf( max );
            // start a new alignment only if j is a match
            if( max_j > 0 && i > 0 && accessor( reference[ i-1 ] ) === accessor( sequence[ max_j-1 ] ) ) {
                j = max_j;
                // does the alignment's score meet the threshold
                saving = max >= scoring.threshold;
                if( saving ) {
                    alignments.push( [[],[]] );
                    index++;
                    for( var k = sequence.length-1; k >= j; k-- ) {
                        alignments[ index ][ 0 ].push( clone(sequence[ k ]) );
                        alignments[ index ][ 1 ].push( null );
                    }
                    alignments[ index ][ 0 ].unshift( clone(sequence[j-1]) );
                    alignments[ index ][ 1 ].unshift( clone(reference[i-1]) );
                }
            } else {
                i--;
            }
        } else if ( i == 0 ) {
            j = 0;
        } else {
            // diag, up, left
            var scores = [ a[i-1][j-1], a[i][j-1], a[i-1][j] ];
            var max = scores.max();
            // stop aligning if a 0 cell was reached
            if( max == 0 ) {
                i = 0;
            } else {
                switch( scores.indexOf( max ) ) {
                    // diag
                    case 0:
                        j--;
                        i--;
                        // no alignments happen in the first row or column
                        if( saving ) {
                            if( j >  0  && i > 0 ) {
                                alignments[ index ][ 0 ].unshift( clone(sequence[j-1]) );
                                alignments[ index ][ 1 ].unshift( clone(reference[i-1]) );
                            } else if( i > 0 ) {
                                alignments[ index ][ 0 ].unshift( null );
                                alignments[ index ][ 1 ].unshift( clone(reference[i-1]) );
                            } else if( j > 0 ) {
                                alignments[ index ][ 0 ].unshift( clone(sequence[j-1]) );
                                alignments[ index ][ 1 ].unshift( null );
                            }
                        }
                        break;
                    // up
                    case 1:
                        j--;
                        if( saving ) {
                            if( j > 0 ) {
                                alignments[ index ][ 0 ].unshift( clone(sequence[j-1]) );
                                alignments[ index ][ 1 ].unshift( null );
                            }
                        }
                        break;
                    // left
                    case 2:
                        i--;
                        if( saving ) {
                            if( i > 0 ) {
                                alignments[ index ][ 0 ].unshift( null );
                                alignments[ index ][ 1 ].unshift( clone(reference[i-1]) );
                            }
                        }
                        break;
                }
            }
            // add any missing genes
            if( i == 0 && saving ) {
                for( var k = j-2; k >= 0; k-- ) {
                    alignments[ index ][ 0 ].unshift( clone(sequence[ k ]) );
                    alignments[ index ][ 1 ].unshift( null );
                }
            }
        }
    }
    
    return alignments;
};

// returns the higher scoring alignment - forward or reverse
var repeat = function( sequence, reference, accessor, scoring ) {
    if( accessor === undefined ) {
        accessor = default_accessor;
    }
    if( scoring === undefined ) {
        scoring = {};
    }
    if( scoring.match === undefined ) {
        scoring.match = 5;
    }
    if( scoring.mismatch === undefined ) {
        scoring.mismatch = 0;
    }
    if( scoring.gap === undefined ) {
        scoring.gap = -1;
    }
    if( scoring.threshold === undefined ) {
        scoring.threshold = 10;
    }
	var forwards = repeat_align( sequence, reference, accessor, scoring );
    reference_clone = reference.slice(0);
	reference_clone.reverse();
	var reverses = repeat_align( sequence, reference_clone, accessor, scoring );
    // clone each object in the arrays
    // flip the strand for each selected gene
    var output = forwards;
    for( var i = 0; i < reverses.length; i++ ) {
        for( var j = 0; j < reverses[ i ][ 1 ].length; j++ ) {
            if( reverses[ i ][ 1 ][ j ] != null ) {
                reverses[ i ][ 1 ][ j ].strand = -1*reverses[ i ][ 1 ][ j ].strand;
            }
        }
        output.push( reverses[ i ] );
    }
	return output;
}
