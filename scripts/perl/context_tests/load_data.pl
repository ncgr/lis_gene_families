#!/usr/bin/env perl


use strict;
use warnings;
use Getopt::Long; # get the command line options
use Pod::Usage; # so the user knows what's going on
use DBI; # our DataBase Interface
use Cwd 'abs_path'; # for executing the indexing script


=head1 NAME

gmod_gene_ordering.pl - Orders all the genes in the database by their order on their respective chromosomes in the featureprop table.

=head1 SYNOPSIS

  gmod_gene_ordering.pl [options]

  --dbname      The name of the chado database (default=chado)
  --username    The username to access the database with (default=chado)
  --password    The password to log into the database with
  --host        The host the database is on (default=localhost)
  --port        The port the database is on

=head1 DESCRIPTION

Loads the data from the given json file into the context test database. Note, the gene order and gene family scripts should be used in conjunction with this one.

=head1 AUTHOR

Alan Cleary

Copyright (c) 2014
This library is free software; you can redistribute it and/or modify it under the same terms as Perl itself.

=cut


# read variables (if any) from the environment
my ($port);
$port = $ENV{CHADO_DB_PORT} if ($ENV{CHADO_DB_PORT});
my $dbname = "chado";
$dbname = $ENV{CHADO_DB_NAME} if ($ENV{CHADO_DB_NAME});
my $username = "chado";
$username = $ENV{CHADO_DB_USER} if ($ENV{CHADO_DB_USER});
my $password = ""; 
$password = $ENV{CHADO_DB_PASS} if ($ENV{CHADO_DB_USER});
my $host = "localhost";
$host = $ENV{CHADO_DB_HOST} if ($ENV{CHADO_DB_HOST});

# get the command line options and environment variables
GetOptions("nuke|?"             => \$nuke,
           "dbname=s"           => \$dbname,
           "username=s"         => \$username,
           "password=s"         => \$password,
           "host=s"             => \$host,
           "port=i"             => \$port) || Retreat("Error in command line arguments\n");

# create a data source name
print "Connecting to the database\n";
my $dsn = "dbi:Pg:dbname=$dbname;host=$host;";
$dsn .= "port=$port;" if $port;

# connect to the database
my $conn = DBI->connect($dsn, $username, $password, {AutoCommit => 0, RaiseError => 1});
my $query;

# boot strap
# ----------
#
# db
# dbxref
# cv
# cvterm

# manual
# ------
#
# featureprop
# gene_order

# inferred
# --------
#
# feature
# feature_relationship
# phylotree
# phylonode

# dummy
# -----
#
# featureloc
# organism

