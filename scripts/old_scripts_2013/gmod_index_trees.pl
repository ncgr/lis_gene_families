#!/usr/bin/env perl


use strict;
use warnings;
use Getopt::Long; # for getting command line options
use Pod::Usage; # so the user knows what's going on
use DBI; # our DataBase Interface


=head1 NAME

gmod_index_trees.pl - Assigns right and left index values to tree nodes based on depth.

=head1 SYNOPSIS

  gmod_index_trees.pl [options]

  --rootid      The phylonode_id of the root node of the tree to be indexed
  --dbname      The name of the chado databse (default=chado)
  --username    The username to access the database with (default=chado)
  --password    The password to log into the database with
  --host        The host the database is on (default=localhost)
  --port        The port the database is on

=head1 DESCRIPTION

The --rootid flag should be provided if the indexes are only to be assigned for the nodes of one tree. If the flag is not provided all node indexes in all trees will be updated.

=head1 AUTHOR

Alan Cleary

Copyright (c) 2013
This library is free software; you can redistribute it and/or modify it under the same terms as Perl itself.

=cut


# see if the user needs help
my $man = 0;
my $help = 0;
GetOptions('help|?' => \$help, man => \$man) or pod2usage(2);
pod2usage(1) if $help;
pod2usage(-exitval => 0, -verbose => 2) if $man;


# get the command line options and environment variables
my ($port, $rootid);
$port = $ENV{CHADO_DB_PORT} if ($ENV{CHADO_DB_PORT});
my $dbname = "chado";
$dbname = $ENV{CHADO_DB_NAME} if ($ENV{CHADO_DB_NAME});
my $username = "chado";
$username = $ENV{CHADO_DB_USER} if ($ENV{CHADO_DB_USER});
my $password = "";
$password = $ENV{CHADO_DB_PASS} if ($ENV{CHADO_DB_USER});
my $host = "localhost";
$host = $ENV{CHADO_DB_HOST} if ($ENV{CHADO_DB_HOST});
my $errorfile = "gmod_load_tree_errors.txt";

GetOptions("rootid=i"           => \$rootid,
           "dbname=s"           => \$dbname,
           "username=s"         => \$username,
           "password=s"         => \$password,
           "host=s"             => \$host,
           "port=i"             => \$port) || die("Error in command line arguments\n");


# make sure we didn't get any additional arguments
if (@ARGV != 0) {
    pod2usage(2);
}


# create a data source name
print "Connecting to the database\n";
my $dsn = "dbi:Pg:dbname=$dbname;host=$host;";
$dsn .= "port=$port;" if $port;


#connect to the databse
my $conn = DBI->connect($dsn, $username, $password, {'RaiseError' => 1});


# get the cvterm for the root of a tree
my $root_type = $conn->selectrow_array("SELECT cvterm_id FROM cvterm WHERE name SIMILAR TO 'phylo_root';");
if (!$root_type) {
    # close the connection
    $conn->disconnect();
    # die
    die("Failed to retrieve phylo_root cvterm\nExiting...\n");
}


# create variables, queries, and subroutines for indexing
my $index = 1;
# the index queries
my $set_left  = $conn->prepare("UPDATE phylonode " .
                               "SET left_idx = ? " .
                               "WHERE phylonode_id = ?");
my $set_right = $conn->prepare("UPDATE phylonode " .
                               "SET right_idx = ? " .
                               "WHERE phylonode_id = ?");
# this is a depth first search of the tree
sub walk_tree {
    # each node has it's own children
    my $children = $conn->prepare("SELECT phylonode_id " .
                                  "FROM phylonode " .
                                  "WHERE parent_phylonode_id = ?");
    # get the phylonode_id from the arguments list
    my $node = shift;
    # update the left_idx value of the phylonode
    $set_left->execute($index++, $node);
    # get the children of the phylonode
    $children->execute($node);
    # recursively call walk_tree on the node's children
    if ($children->rows() > 0) {
        while (my ($node) = $children->fetchrow_array) {
            walk_tree($node);
        }
    }
    # update the right_idx value of the phylonode
    $set_right->execute($index++, $node);
}


# if a root phylonode_id was provided
if ($rootid) {
    print "Indexing tree\n";
    walk_tree($rootid);
}
# if not, update every tree
else {
    # get all the tree roots
    my $roots = $conn->prepare("SELECT phylonode_id FROM phylonode WHERE type_id=$root_type;");
    $roots->execute();
    # use them to assign indexes in their respective trees
    while (my $root = $roots->fetchrow_array()) {
        $index = 1;
        print "Indexing tree with root $root\n";
        walk_tree($root);
    }
    # undefine roots
    undef($roots);
}


# close the connection
print "Exiting\n";
$conn->disconnect();


