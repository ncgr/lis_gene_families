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
    var rows = reference.length + 1; // first item is at index 1
    var cols = sequence.length + 1; // first item is at index 1
    var a = Array.matrix( cols, rows, 0 );
    var i = 0, j = 0;
    var choice = [ 0, 0, 0, 0 ];
    var ref = [];
    var seq = [];
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
            choice[1] = a[j-1][i-1] + s( accessor(reference[i-1]), accessor(sequence[j-1]), scoring );
            choice[2] = a[j-1][i] + scoring.gap;
            choice[3] = a[j][i-1] + scoring.gap;
            a[j][i] = choice.max();
        }
    }

    // traceback - make a track for each qualified path in the matrix
    i = 0;
    j = sequence.length+1; // start in the extra cell
	var total_score = 0;
    while( !(i == 0 && j == 0) ) {
        if( i == 0 ) {
            j--;
            var max = a[j].max();
            var max_i = a[j].lastIndexOf( max );
            // only use i if it's a match
            if( max_i > 0  && j > 0 && accessor( reference[ max_i-1 ] ) === accessor( sequence[ j-1 ] ) ) {
                i = max_i;
                ref.unshift( clone(reference[i-1]) );
                seq.unshift( clone(sequence[j-1]) );
                total_score += max;
            } else if( j > 0 ){
                ref.unshift( null );
                seq.unshift( clone( sequence[j-1] ) );
            }
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
                    if( i!= 0  && j != 0 ) {
                        ref.unshift( clone(reference[i-1]) );
                        seq.unshift( clone(sequence[j-1]) );
                    } else if( i!= 0 ) {
                        ref.unshift( clone(reference[i-1]) );
                        seq.unshift( null );
                    } else if( j!= 0 ) {
                        ref.unshift( null );
                        seq.unshift( clone(sequence[j-1]) );
                    }
                    break;
                // up
                case 1:
                    i--;
                    if( i != 0 ) {
                        ref.unshift( clone(reference[i-1]) );
                        seq.unshift( null );
                    }
                    break;
                 // left
                 case 2:
                    j--;
                    if( j != 0 ) {
                        ref.unshift( null );
                        seq.unshift( clone(sequence[j-1]) );
                    }
                    break;
            }
        }
    }
    
    return [seq, ref, total_score];
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
	var forwards = smith( sequence, reference, accessor, scoring );
    reference_clone = reference.slice(0);
	reference_clone.reverse();
	var reverses = smith( sequence, reference_clone, accessor, scoring );
	if( forwards[2] >= reverses[2] ) {
		return [forwards[0], forwards[1]];
	} else {
        // clone each object in the array
        // flip the strand for each selected gene
        for( var i = 0; i < reverses[1].length; i++ ) {
            if( reverses[1][i] != null ) {
                reverses[1][i].strand = -1*reverses[1][i].strand;
            }
        }
	    return [reverses[0], reverses[1]];
    }
}
