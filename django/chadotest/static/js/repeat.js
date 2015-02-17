/*
 * Source:
 *	  http://my.so-net.net.tw/tzuyichao/javascript/forfun/smithwaterman/smith.waterman.html
 * Description:
 *    Smith-Waterman Algorithm in JavaScript
 *    只是實作不考慮 scoring matrix 和 gap penality 設定這個問題
 *    所以很多東西都定在global scope |-) 
 * Reference:
 *    http://en.wikipedia.org/wiki/Smith-Waterman_algorithm
 * Required: 
 *    enhancement.js
 * Author:
 *    Terence Chao, 2009
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
    var rows = reference.length + 1;
    var cols = sequence.length + 1;
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

    // traceback
    i = 0;
    j = sequence.length;
	var total_score = 0;
    var qualified = false;
    while( !(i == 0 && j == 0) ) {
        if( i == 0 ) {
            j--;
            var max = a[j].max();
            i = a[j].lastIndexOf( max );
            qualified = max >= scoring.threshold;
            if( qualified ) {
                ref.unshift( clone(reference[i]));
                total_score += max;
            } else {
                ref.unshift( null );
            }
            seq.unshift( clone(sequence[j]));
        } else if ( j == 0 ) {
            i = 0;
        } else {
            // diag, up, left
            var scores = [ a[j-1][i-1], a[j][i-1], a[j-1][i] ];
            var max = scores.max();
            switch( scores.indexOf( max ) ) {
                // diag
                case 0:
                    if( qualified ) {
                        ref.unshift( clone(reference[i-1]));
                    } else {
                        ref.unshift( null );
                    }
                    seq.unshift( clone(sequence[j-1]));
                    i--;
                    j--;
                    break;
                // up
                case 1:
                    if( qualified ) {
                        ref.unshift( null );
                    }
                    seq.unshift( clone(sequence[j-1]));
                    j--;
                    break;
                 // left
                 case 2:
                    if( qualified ) {
                        ref.unshift( clone(reference[i-1]));
                        seq.unshift( null );
                    }
                    i--;
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
	var forward = smith( sequence, reference, accessor, scoring );
    reference_clone = reference.slice(0);
	reference_clone.reverse();
	var reverse = smith( sequence, reference_clone, accessor, scoring );
	if( forward[2] >= reverse[2] ) {
		return [forward[0], forward[1]];
	} else {
        // clone each object in the array
        // flip the strand for each selected gene
        for( var i = 0; i < reverse[1].length; i++ ) {
            if( reverse[1][i] != null ) {
                reverse[1][i].strand = -1*reverse[1][i].strand;
            }
        }
	    return [reverse[0], reverse[1]];
    }
}
