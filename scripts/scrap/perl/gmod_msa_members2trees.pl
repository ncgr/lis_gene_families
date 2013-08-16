#!/usr/bin/env perl

use strict;
use warnings;
use Getopt::Long; # gets command line options


=head1 NAME

$0 - Takes a list of fasta files with the proper names for the features in the msa files and updates the names in the tree file.

=head1 SYNOPSIS

  % gmod_msa_members2trees.pl <filename> [options]

=head1 COMMAND-LINE OPTIONS

  --members     A comma seperated list of all the fasta files with proper names
  --outfile     The name of the output file

-head1 DESCRIPTION

The --members flag is required. The argument should look like this: <file1>,<file2>,<file3>.

If the --outfile flag is not used then the output will go to stdout.

=head1 AUTHOR

Alan Cleary

Copyright (c) 2013

This library is free software; you can redistribute it and/or modify it under the same terms as Perl itself.

=cut


# get command line options
my ($outfile, $members);

GetOptions("outfile=s"  => \$outfile,
           "members=s"  => \$members) || die("Error in command line arguments\n");

# die if we didn't get any member files
if (!$members) {
    die("--members is a required flag\n");
}

# make sure we have an input file
if (@ARGV != 1) {
    die("Usage: gmod_msa_members2msas.pl <filename> [options]\n");
}

# if we have an output file to write to
sub deliver { print(@_); };
if ($outfile) {
    open(OUTFILE, ">".$outfile) || die("Failed to open output file: $1\n");
    *deliver = sub { return print(OUTFILE @_); };
}

# open the input file
open(FILE, $ARGV[0]) || die("Failed to read input file: $!\n");

# split the msa files
my @msas = split(",", $members);

# create a hash of the msa members as the values and their feature counterparts as the keys
my %names = ();
for my $file (@msas) {
    open(MSA, $file) || next;
    # iterate over each line of the input file
    while (my $line = <MSA>) {
        chomp $line;
        # only process description lines
        if (index($line, ">") == -1) { next; };
        #$names{split(/\.([^\.]+)$/, $line)} = $line; # note we're saving the >
        my ($name, $tag) = split(/\.([^\.]+)$/, $line);
        $names{substr($name, 1)} = substr($line, 1); # we remove the > at the last second
    }
    close(MSA);
}

# read the input file one line at a time
while (my $line = <FILE>) {
    chomp $line;
    # iterate over the names
    for my $name (keys(%names)) {
        # find a replace the name
        $line =~ s/\Q$name\E/$names{$name}/g;
        ## if the name is in the line replace it
        #my $index = index($line, $name);
        #if ($index != -1) {
        #    substr($line, $index, length($names{$name}), $names{$name})
        #}
    }
    deliver("$line\n");
}

# close the input file
close(FILE);
close(OUTFILE) if $outfile;

