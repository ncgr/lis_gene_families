/*
 * Terence Chao ¾ã²z
 */
// Function Enhancement
Function.prototype.method = function(name, fn) {
    this.prototype[name] = fn;
};

// String Enhancement
String.prototype.trim = function() {
    return this.replace(/^\s+|\s+$|\n$|^\n/g, '');
};

String.prototype.isPartOf = function(str) {
    var re = new RegExp( '(^|\\s)' + this + '(^|\\s)' );
    return re.test( str );
};

// Array Enhancement
Array.prototype.foreach = function(fn) {
    for( var i=0; i<this.length; i++) {
        fn.call( this[i] );
    } // for
};

Array.method( 'max', function() {
    var i = 0;
    var tmp = this[i];
    for( i=0; i<this.length; i++ ) {
        if( tmp < this[i] )
            tmp = this[i];
    } // for
    return tmp;
} );

// multi dimension array from JavaScript: The Good Parts
Array.matrix = function (m, n, initial) {
    var a, i, j, mat = [];
    for (i = 0; i < m; i += 1) {
        a = [];
        for (j = 0; j < n; j += 1) {
            a[j] = initial;
        }
        mat[i] = a;
    }
    return mat;
};

Array.identity = function (n) {
    var i, mat = Array.matrix(n, n, 0);
    for (i = 0; i < n; i += 1) {
        mat[i][i] = 1;
    }
    return mat;
};


