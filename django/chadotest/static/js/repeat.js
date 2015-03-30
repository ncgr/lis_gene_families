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
	} return scoring.mismatch;
}


var smith = function( sequence, reference, accessor, scoring ) {
    var rows = sequence.length + 1; // first item is at index 1
    var cols = reference.length + 1; // first item is at index 1
    var a = Array.matrix( cols, rows, 0 );
    var i = 0, j = 0;
    var choice = [ 0, 0, 0, 0 ];
    var alignments = [];
    var index = -1;
    var score_diag, score_up, scroe_left;
    
    // populate the matrix
    for( j=1; j<cols; j++ ) {
        // handle unmatched regions and ends of matches
        var scores = a[j-1].map(function(score, index) {
            if( index > 0 ) {
                return score - scoring.threshold;
            } return score;
        });
        // handle starts of matches and extensions
        for( i=1; i<rows; i++ ) {
            choice[0] = a[j][0];
            choice[1] = a[j-1][i-1] + s( accessor(reference[j-1]), accessor(sequence[i-1]), scoring );
            choice[2] = a[j-1][i] + scoring.gap;
            choice[3] = a[j][i-1] + scoring.gap;
            a[j][i] = choice.max();
        }
    }

    // traceback - make a track for each qualified path in the matrix
    i = 0;
    j = cols; // start in the extra cell
    var saving = false;
    while( !(i == 0 && j == 0) ) {
        if( i == 0 ) {
            j--;
            var max = a[j].max();
            var max_i = a[j].lastIndexOf( max );
            // start a new alignment only if i is a matcha
            if( max_i > 0  && j > 0 && accessor( reference[ j-1 ] ) === accessor( sequence[ max_i-1 ] ) ) {
                i = max_i;
                // does the alignment's score meet the threshold
                saving = max >= scoring.threshold;
                if( saving ) {
                    alignments.push( [[],[]] );
                    index++;
                    for( var k = sequence.length-1; k >= i; k-- ) {
                        alignments[ index ][ 0 ].push( clone(sequence[ k ]) );
                        alignments[ index ][ 1 ].push( null );
                    }
                    alignments[ index ][ 0 ].unshift( clone(sequence[i-1]) );
                    alignments[ index ][ 1 ].unshift( clone(reference[j-1]) );
                }
            }
            //} else if( j > 0 ){
            //    alignments[ index ][ 0 ].unshift( null );
            //    alignments[ index ][ 1 ].unshift( clone( reference[j-1] ) );
            //}
        } else if ( j == 0 ) {
            i = 0;
        } else {
            // diag, up, left
            var scores = [ a[j-1][i-1], a[j][i-1], a[j-1][i] ];
            var max = scores.max();
            switch( scores.indexOf( max ) ) {
                // diag
                case 0:
                    i--;
                    j--;
                    // no alignments happen in the first row or column
                    if( saving ) {
                        if( i >  0  && j > 0 ) {
                            alignments[ index ][ 0 ].unshift( clone(sequence[i-1]) );
                            alignments[ index ][ 1 ].unshift( clone(reference[j-1]) );
                        } else if( j > 0 ) {
                            alignments[ index ][ 0 ].unshift( null );
                            alignments[ index ][ 1 ].unshift( clone(reference[j-1]) );
                        } else if( i > 0 ) {
                            alignments[ index ][ 0 ].unshift( clone(sequence[i-1]) );
                            alignments[ index ][ 1 ].unshift( null );
                        }
                    }
                    break;
                // up
                case 1:
                    i--;
                    if( saving ) {
                        if( i > 0 ) {
                            alignments[ index ][ 0 ].unshift( clone(sequence[i-1]) );
                            alignments[ index ][ 1 ].unshift( null );
                        }
                    }
                    break;
                // left
                case 2:
                    j--;
                    if( saving ) {
                        if( j > 0 ) {
                            alignments[ index ][ 0 ].unshift( null );
                            alignments[ index ][ 1 ].unshift( clone(reference[j-1]) );
                        }
                    }
                    break;
            }
        }
    }
    
    return alignments;
};

// returns the higher scoring alignment - forward or reverse
var align = function( sequence, reference, accessor, scoring ) {
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
	var forwards = smith( sequence, reference, accessor, scoring );
    reference_clone = reference.slice(0);
	reference_clone.reverse();
	var reverses = smith( sequence, reference_clone, accessor, scoring );
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
