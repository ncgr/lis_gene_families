#!/usr/bin/env perl

use strict;
use warnings;

# make sure have a gff file
if (@ARGV != 1) {
    print "\nUsage: add_first_column.pl <filename>\n";
}

# open the tabbed file
open(FILE, $ARGV[0]) || die "failed to read input file: $!";

my $unique_id = 0;
# read the file one line at a time and add the unique_id
while (my $line = <FILE>) {
    chomp $line;
    print "$unique_id\t$line\n";
    $unique_id++;
}

# close the file
close(FILE);

