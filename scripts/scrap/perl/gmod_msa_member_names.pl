#!/usr/bin/env perl

use strict;
use warnings;
use Getopt::Long; # get the command line options


=head1 NAME

$0 - Removes all junk from the description line of a fasta file that contains msa members.

=head1 SYNOPSIS

  % gmod_msa_member_names.pl <filename> [options]

=head1 COMMAND-LINE OPTIONS

  --outfile     The name of the output file

=head1 DESCRIPTION

If the --outfile flag is not used then the output will go to stdout.

=head1 AUTHOR

Alan Cleary

Copyright (c) 2013

This library is free software; you can redistribute it and/or modify it under the same terms as Perl itself.

=cut


# get the command line options
my $outfile;

GetOptions("outfile=s"  => \$outfile) || die("Error in command line arguments\n");

# make sure we have a file
if (@ARGV != 1) {
    die("Usage: gmod_msa_member_names.pl <filename> [options]\n");
}

# if we have an output file to write to
sub deliver { print(@_); };
if ($outfile) {
    open(OUTFILE, ">".$outfile) || die("Failed to open output file: $!\n");
    *deliver = sub { return print(OUTFILE @_); };
}

# open the input file
open(FILE, $ARGV[0]) || die("Failed to read input file: $!\n");

# read the file one line at a time
while (my $line = <FILE>) {
    chomp $line;
    # only process description lines
    if (index($line, ">") == -1) {
        deliver("$line\n");
        next;
    }
    # process the line without regexes because they're slow!
    my @pieces = split(":", $line);
    my @more_pieces = split(" ", $pieces[1]);
    deliver(">$more_pieces[0]\n");
}

# close all open files
close(FILE);
close(OUTFILE) if $outfile;

