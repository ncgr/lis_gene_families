#!/usr/bin/env perl

use strict;
use warnings;
use Getopt::Long; # get getting command line options


# this script doesn't do much besides removing anything that's not a name from a fasta file (i.e. pac ids) and appending _pep or some other string to the end of the name


# get the command line options
my $outfile;
my $append = "_pep";

GetOptions("outfile=s"  => \$outfile,
           "append=s"   => \$append) || die("Error in command line arguments\n");

# make sure we only have one input file
if (@ARGV != 1) {
    die("Usage: gmod_fasta_peptide_renamer.pl <filename>.fasta [options]\n");
}

# open the fasta file
open(FILE, $ARGV[0]) || die("Failed to read input file\n");

# if we have an output file
sub deliver { print(@_); };
if ($outfile) {
    open(OUTFILE, '>'.$outfile) || die("Failed to open output file: $!\n");
    *deliver = sub { return print(OUTFILE @_); };
}

# read the file one line at a time
while (my $line = <FILE>) {
    chomp $line;
    # don't process anything that's not a description line
    if (index($line, '>') == -1) {
        deliver($line."\n");
        next;
    }
    # fix up the name
    ($line) = $line =~ />([^|]*)|/;
    # and send it on it's way
    deliver(">".$line."$append\n");
}

# close all the open files
close(FILE);
close(OUTFILE) if $outfile;

