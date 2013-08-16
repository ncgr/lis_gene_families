#!/usr/bin/env perl

use strict;
use warnings;
use Getopt::Long; # get the command line options


=head1 NAME

  $0 - Combines the unique lines in of the input files into a single file

=head1 SYNOPSIS

  % gmod_compile_unique_lines.pl <filename> <filename> ... [options]

=head1 COMMAND-LINE OPTIONS

  --outfile     The name of the output file

=head1 DESCRIPTION

If the --outfile flag is not used then the output will go to stdo

All arguments given will be considered names of files to be opened.

=head1 AUTHOR

Alan Cleary

Copyright (c) 2013

This library is free software; you can redistribute it and/or modify it under the same terms as Perl itself.

=cut


# get the command line options
my $outfile;

GetOptions("outfile=s"  => \$outfile) || die("Error in command line arguments\n");

# make sure we have the right number of command line arguments
if (@ARGV == 0) {
    die("No files provided!\nUsage: gmod_compile_unique_lines.pl <filename> <filename> ... [options]\n");
}

# if we have an output file to write to
sub deliver { print(@_); };
if ($outfile) {
    open(OUTFILE, ">".$outfile) || die("Failed to open output file: $!\n");
    *deliver = sub { return print(OUTFILE @_); };
}

# iterate over the files given and put them all unique lines into a hash
my %lines = ();
for my $file (@ARGV) {
    print "Reading $file\n";
    open(FILE, $file) || next;
    # read the file one line at a time and hash the unique ones
    while (my $line = <FILE>) {
        chomp $line;
        $lines{$line} = 1 if (!$lines{$line});
    }
    # close the file
    close(FILE);
}

# deliver the lines to the user
for my $line (keys(%lines)) {
    deliver("$line\n");
}

# close the ourfile
close(OUTFILE) if $outfile;

