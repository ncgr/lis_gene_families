#!/usr/bin/env perl

use strict;
use warnings;
use Getopt::Long; # gets command flags


=head1 NAME

$0 - Preprerepares a GFF3 file for bulk loading into a chado database

=head1 SYNOPSIS

  % gmod_gff_prepreprocessor.pl <filename>.gff [options]

=head1 COMMAND-LINE OPTIONS

  --outfile         The name of the output file
  --setsource       Replace the current source (column 2) with the given source
  --appendsource    Append the current source (column 2) with the given source

=head1 DESCRIPTION

If the --outfile flag is not used the output will go to stdout.

=head1 AUTHOR

Alan Cleary

Copyright (c) 2013

This library is free softweare; you can redistribute it and/or modify it under the same terms as Perl itself.

=cut


# get command line options
my ($outfile, $setsource, $appendsource);

GetOptions("outfile=s"      => \$outfile,
           "setsource=s"    => \$setsource,
           "appendsource=s" => \$appendsource) || die("Error in command line arguments\n");

# make sure we have a gff file
if (@ARGV != 1) {
    die("Usage: gmod_gff3_prepreprocessor.pl <filename>.gff [options]\n");
}

# if we have an output file to write to
sub deliver { print(@_); };
if ($outfile) {
    open(OUTFILE, ">".$outfile) || die("Failed to open output file: $!\n");
    *deliver = sub { return print(OUTFILE @_); };
}

# open the gff file
open(FILE, $ARGV[0]) || die("Failed to read input file: $!\n");

# read the file one line at a time
while (my $line = <FILE>) {
    chomp $line;
    # don't process comments, blank lines, and optional repeat of title line
    if ($line =~ /^\#/ || $line =~ /^\s*$/ || $line =~ /^\+/) {
        deliver("$line\n");
        next;
    }
    # split each column from the current line into their respective values
    my ($reference, $source, $type, $start, $end, $score, $strand, $phase, $group) = split(/\t/, $line);
    # use a regex to replace non-number scores with .'s
    $score = "." if not $score=~/^([+-]?)(?=\d|\.\d)\d*(\.+\d*)?([Ee]([+-]?\d+))?$/;
    # if an mRNA doesn't have a parent create one using it's ID
    if ($type =~ "mRNA" && index($group, "Parent") == -1) { # should this be more reobust?
        my @subgroups = split(/;/, $group); # break apart the components of the group
        foreach my $subgroup (@subgroups) { # iterate over them
            my $subub = substr($subgroup, 0, 2);
            if (substr($subgroup, 0, 2) =~ "ID") { # see if the current component is the ID
                my $id = substr($subgroup, 3); # get the id
                $group .= "Parent=$id\_gene;"; # add a parent component to the group
                last; # no need to iterate anymore
            }
        }
    }
    # replace the source of the --setsource flag was set
    $source = $setsource if ($setsource);
    # append to the source if the --appendsource flag was set
    $source .= "_".$appendsource if ($appendsource);
    # print the processed line
    deliver("$reference\t$source\t$type\t$start\t$end\t$score\t$strand\t$phase\t$group\n");
}

# cloas all open files
close(FILE);
close(OUTFILE) if $outfile;

