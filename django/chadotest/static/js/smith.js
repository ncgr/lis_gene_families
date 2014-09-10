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
var s = function( first, second ) {
	if( first === second ) {
		return 4;
	} return -1;
}

var gap = -1;

var smith = function( sequence, reference, accessor ) {
    var rows = reference.length + 1;
    var cols = sequence.length + 1;
    var a = Array.matrix( rows, cols, 0 );
    var i = 0, j = 0;
    var choice = [ 0, 0, 0, 0 ];
    var ref = [];
    var seq = [];
    var score, score_diag, score_up, scroe_left;
    
    // populate the matrix
	var last_i_align,
		last_j_align;
    for( i=1; i<rows; i++ ) {
        for( j=1; j<cols; j++ ) {
            choice[0] = 0;
            choice[1] = a[i-1][j-1] + s( accessor(reference[i-1]), accessor(sequence[j-1]) );
            choice[2] = a[i-1][j] + gap;
            choice[3] = a[i][j-1] + gap;
            a[i][j] = choice.max();
			if( a[i][j] === choice[1] ) {
				last_i_align = i;
				last_j_align = j;
			}
        }
    }

    // traceback
    i = reference.length;
    j = sequence.length;
	var total_score = 0;
	//if( !(last_i_align === undefined || last_j_align === undefined) ) {
	//	i = last_i_align ;
	//	j = last_j_align;
	//}
    //while( i>0 && j>0 ) {
    while( i>0 && j>0 ) {
        score = a[i][j];
		total_score += score;
        score_diag = a[i-1][j-1];
        score_up = a[i][j-1];
        score_left = a[i-1][j];
        if( score === (score_diag + s( accessor(reference[i-1]), accessor(sequence[j-1]) )) ) {
            ref.unshift( clone(reference[i-1]));
            seq.unshift( clone(sequence[j-1]));
            i -= 1;
            j -= 1;
        } else if( score === (score_left + gap) ) {
            ref.unshift( clone(reference[i-1]));
            seq.unshift( null );
            i -= 1;
        } else if( score === (score_up + gap) ) {
            ref.unshift( null );
            seq.unshift( clone(sequence[j-1]));
            j -= 1;
		} else {
			break;
		}
    }

	//if( last_j_align != sequence.length ) {
	//	for( var k = last_j_align; k < sequence.length; k++ ) {
	//		seq.push( sequence[k] );
	//		ref.push( -1 );
	//	}
	//}
    
    while( i>0 ) {
        ref.unshift( clone(reference[i-1]));
        seq.unshift( null );
        i -= 1;
    }
    
    while( j>0 ) {
        ref.unshift( null );
        seq.unshift( clone(sequence[j-1]));
        j -= 1;
    }
    
    return [seq, ref, total_score];
};

// returns the higher scoring alignment - forward or reverse
var align = function( sequence, reference, accessor ) {
    if( accessor === undefined ) {
        accessor = default_accessor;
    }
	var forward = smith( sequence, reference, accessor );
    reference_clone = reference.slice(0);
	reference_clone.reverse();
	var reverse = smith( sequence, reference_clone, accessor );
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
