#!/usr/bin/env perl


use strict;
use warnings;
use Getopt::Long; # get the command line options
use Pod::Usage; # so the user knows what's going on
use DBI; # our DataBase Interface
use Bio::TreeIO; # for reading our trees
use IO::String; # for loading our file contents into TreeIO as a string
use Cwd 'abs_path'; # for executing the indexing script


=head1 NAME

gmod_load_tree.pl - Loads a phylogentic tree into a chado database from a file.

=head1 SYNOPSIS

  gmod_load_tree.pl <filename>

  --dbid        The db_id of the db dbxref for the trees should be create with
  --name        The name given to the phylotree entry in the database (default=<filename>)
  --dbname      The name of the chado database (default=chado)
  --username    The username to access the database with (default=chado)
  --password    The password to log into the database with
  --host        The host the database is on (default=localhost)
  --port        The port the database is on
  --errorfile   The file that errors should be written to (default=gmod_load_tree_errors.txt)

=head1 DESCRIPTION

The --dbid flag is required.

This script WILL NOT load a tree into the database unless all the polypeptides in the tree are represented as features in the database. Polypeptides that are not in the database will be written to the errorfile, as specified by the --errorfile flag.

When trees are first added to the database their nodes' left_idx and right_idx fields are given unique, with respect to the tree, negative values that DO NOT reflect the tree structure. The proper positive values can be assigned using the gmod_index_trees.pl script.

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
my ($port, $dbid, $name);
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

GetOptions("dbid=i"             => \$dbid,
           "name=s"             => \$name,
           "dbname=s"           => \$dbname,
           "username=s"         => \$username,
           "password=s"         => \$password,
           "host=s"             => \$host,
           "port=i"             => \$port,
           "errorfile=s"        => \$errorfile) || die("Error in command line arguments\n");

if (!$dbid) {
    die("The --dbid flag is required\n");
}


# make sure we have our tree file
if (@ARGV != 1) {
    pod2usage(2);
}
$name = $ARGV[0] if (!$name);


# open the tree file and assign the name
print "Opening the input file\n";
open(FILE, $ARGV[0]) || die("Failed to read the input file\n");


# create a data source name
print "Connecting to the database\n";
my $dsn = "dbi:Pg:dbname=$dbname;host=$host;";
$dsn .= "port=$port;" if $port;


# connect to the database
my $conn = DBI->connect($dsn, $username, $password, {'RaiseError' => 1});


# read each line of the file into a string
print "Reading tree file\n";
my $newick = "";
while (my $line = <FILE>) {
    chomp $line;
    $newick .= $line
}


# close the file
close(FILE);


# let the user know how many nodes we have
print "Inspecting trees\n";
my $io = IO::String->new($newick);
my $treeio = Bio::TreeIO->new(-fh => $io, -format => 'newick');
while( my $tree = $treeio->next_tree ) {
    # get a tree
    print "",scalar $tree->get_nodes, " nodes found\n";
}


# get all the ids
$io = IO::String->new($newick);
$treeio = Bio::TreeIO->new(-fh => $io, -format => 'newick');
# it seems our trees' internal nodes are ids, not bootstrap values, so we're going to treat them like ids
my %leafs = ();
my %nodes = ();
while( my $tree = $treeio->next_tree ) {
    for my $node ( $tree->get_nodes ) {
        my $branch_length = $node->branch_length;
        my $parent = $node->ancestor;
        # hash the node, give it a value of it's unique phylonode database identifier later
        $nodes{$node->internal_id} = 1; # 1 is a placeholder
        # hash the leaf nodes, given them values of their unique feature database identifiers later
        if ($node->is_Leaf) {
            my $leaf = $node->id;
            $leaf .= "_pep" if (index($leaf, "_pep") == -1);
            $leafs{$leaf} = 1;
        }
    }
}


# let the user know how many nodes are leafs and that we're checking the database for them
my $num_leafs = scalar(keys(%leafs));
print "$num_leafs nodes are leafs\nSearching database for leafs\n";


# get all the tree features in the db
my $query_string = "SELECT feature_id, uniquename FROM feature WHERE";
my $i = 0;
for my $key (keys(%leafs)) {
    $i++;
    $query_string .= " uniquename='$key'";
    $query_string .= " OR" if ($i != $num_leafs);
}
$query_string .= ";";
my $query = $conn->prepare($query_string);
$query->execute();
my $num_found = $query->rows();
print "$num_found present in databse\n";


# see if all the tree polypeptide features were found
if ($num_found != $num_leafs) {
    # open the error file
    print "Some polypeptides were missing\nOpening the error file\n";
    open(ERRORS, '>'.$errorfile) || die("Failed to open the error file: $!\n");
    print "Writing errors\n";
    print ERRORS "Failed to find polypeptides with uniquename:\n";
    # remove polypeptides that were found from the hash
    while (my @row = $query->fetchrow_array()) {
        my ($feature, $uniquename) = @row;
        delete $leafs{$uniquename};
    }
    # report polypeptides that weren't found
    for my $key (keys(%leafs)) {
        print ERRORS "", substr($key, 0, index($key, "_pep")), "\n";
    }
    # close file and connetion
    print "Closing error file\n";
    close(ERRORS);
    undef($query);
    $conn->disconnect();
    # die
    die("Exiting...\n");
}


# notify the user that we're creating a tree
print "All polypeptides found!\nCreating tree\n";


# associate feature_ids with their respective hashes
while (my @row = $query->fetchrow_array()) {
    my ($feature, $uniquename) = @row;
    $leafs{$uniquename} = $feature;
}


# get the phylo_root, phylo_interior, and phylo_leaf cvterms from the cvterm table
my $root_id = $conn->selectrow_array("SELECT cvterm_id FROM cvterm WHERE name SIMILAR TO 'phylo_root';");
my $interior_id = $conn->selectrow_array("SELECT cvterm_id FROM cvterm WHERE name SIMILAR TO 'phylo_interior';");
my $leaf_id = $conn->selectrow_array("SELECT cvterm_id FROM cvterm WHERE name SIMILAR TO 'phylo_leaf';");
# throw an error if one or more doesn't exist
if (!$root_id || ! $interior_id || !$leaf_id) {
    # close the connection
    undef($query);
    $conn->disconnect();
    # die
    die("Failed to retrieve phylo_root, phylo_interior, and phylo_leaf cvterms from database\nExiting...\n");
}


# create a new dbxref for a phylotree
if (!$conn->do("INSERT INTO dbxref (db_id, accession) VALUES ($dbid, '$name');")) {
    # close the connection
    undef($query);
    $conn->disconnect();
    # die
    die("Failed to create a dbxref entry with db_id $dbid\n");
}
my $dbxref = $conn->selectrow_array("SELECT dbxref_id FROM dbxref ORDER BY dbxref_id DESC LIMIT 1;");


# create a new phylotree with our new dbxref
if(!$conn->do("INSERT INTO phylotree (name, dbxref_id, comment) VALUES ('$name', $dbxref, '$newick');")) {
    # close the connection
    undef($query);
    $conn->disconnect();
    # die
    die("Failed to create phylotree entry with name $name and dbxref $dbxref\n");
}
my $phylotree = $conn->selectrow_array("SELECT phylotree_id FROM phylotree ORDER BY phylotree_id DESC LIMIT 1;");
print "Created tree with id $phylotree\n";


# insert the tree nodes into the phylonode table
$io = IO::String->new($newick);
$treeio = Bio::TreeIO->new(-fh => $io, -format => 'newick');

while( my $tree = $treeio->next_tree ) {
    my $root_phylonode;
    my $lindex = 0;
    my $rindex = 0;
    for my $node ( $tree->get_nodes ) {
        # get the node's parent
        my $parent = $node->ancestor;
        # construct the insert commands
        $lindex = $rindex-1;
        $rindex = $lindex-1;
        my $fields = "(phylotree_id,left_idx,right_idx,distance,type_id";
        my $values = "($phylotree,$lindex,$rindex,".$node->branch_length;
        # if a node has a parent
        if ($parent) {
            # and it's a leaf
            if ($node->is_Leaf) {
                # then it gets a label, feature, and type leaf
                $values .= ",".$leaf_id;
                $fields .= ",label,feature_id";
                my $id = $node->id;
                $values .= ",'".$id;
                $values .= "',".$leafs{$id."_pep"};
            }
            # and is not a leaf
            else {
                # it gets type interior
                $values .= ",".$interior_id;
            }
            $fields .= ",parent_phylonode_id";
            $values .= ",".$nodes{$parent->internal_id};
        }
        # it's the root
        else {
            $values .= ",".$root_id;
        }
        $fields .= ")";
        $values .= ")";
        # create the entry in the phylonode table
        if (!$conn->do("INSERT INTO phylonode ".$fields." VALUES ".$values.";")) {
            # close the connection
            undef($query);
            $conn->disconnect();
            # die
            die("Failed to create entry in phylonode with fields $fields and values $values\n");
        }
        # get the id for the entry and hash it
        $nodes{$node->internal_id} = $conn->selectrow_array("SELECT phylonode_id FROM phylonode ORDER BY phylonode_id DESC LIMIT 1;");
        # here we're assuming the first phylonode to be created is the root, which should always be true ;)
        $root_phylonode = $nodes{$node->internal_id} if (!$root_phylonode);
    }
}


# close connection
undef($query);
$conn->disconnect();


