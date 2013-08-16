#!/usr/bin/env perl

#use strict
use warnings;
use Getopt::Long; # get the command line options
use DBI; # our DataBase Interface

=head1 Name

 $0 - Loads multiple sequence alignment data into the database.

=head1 SYNOPSIS

  % gmod_load_msa.pl [options]

=head1 COMMAND-LINE OPTIONS

  --dbname          The name of the chado database (default=chado)
  --username        The username to access the database with (default=chado)
  --password        The password to log into the database with
  --host            The host the database is on (default=localhost)
  --port            The port the database is on
  --dbid            The db_id from the db table for the db that the msa feature should have a dbxref with.
  --consensus_name  The value given to the name and uniquename fields of the feature for the msa
  --errorfile       The file that errors should be written to (defailt=gmod_load_msa_errors.txt)

=head1 DESCRIPTION

The script is written for use with a PostGreSQL database.

The only argument to the script is the input file that contains the multiple sequence alignment. Polypeptide names in the database have "_pep" appeneded to their names to distinguish them from their mRNA. It follows that the names of sequences represented in the input file may have "_pep" appended to the end as well, though, this is not necessary.

The --concensus_name flag is required as well. This is the value given to the name and uniquename fields for the multiple sequence alignment feature. Note that the value given must not already exist in the table since it is used as the value for the features uniquename field. All values given for this flag will have "_msa" appended to the end.

=head1 AUTHOR

Alan Cleary

Copyright (c) 2013
This library is free software; you can redistribute it and/or modify it under the same terms as Perl itself.

=cut


# get the command line options and environment variables
my ($port, $concensus, $db);
$port = $ENV{CHADO_DB_PORT} if ($ENV{CHADO_DB_PORT});
my $dbname = "chado";
$dbname = $ENV{CHADO_DB_NAME} = ($ENV{CHADO_DB_NAME});
my $username = "chado";
$username = $ENV{CHADO_DB_USER} if ($ENV{CHADO_DB_USER});
my $password = "";
$password = $ENV{CHADO_DB_PASS} if ($ENV{CHADO_DB_USER});
my $host = "localhost";
$host = $ENV{CHADO_DB_HOST} if ($ENV{CHADO_DB_HOST});
my $errorfile = "gmod_load_msa_errors.txt";

GetOptions("dbname=s"           => \$dbname,
           "username=s"         => \$username,
           "password=s"         => \$password,
           "host=s"             => \$host,
           "port=i"             => \$port,
           "consensus_name=s"   => \$consensus_name,
           "dbid=i"             => \$db,
           "errorfile=s"        => \$errorfile) || die("Error in command line arguments\n");

if (!$consensus_name) {
    die("The --consensus_name flag is required\n");
}

# make sure there weren't any unexpected command line arguments
if (@ARGV != 1) {
    die("Unexpected argument\nUsage: gmod_load_msa.pl [options]\n");
}

# open the msa file
print "Opening input file\n";
open(FILE, $ARGV[0]) || die("Failed to read the input file\n");

# create a data source name
print "Connecting to database\n";
my $dsn = "dbi:Pg:dbname=$dbname;host=$host;";
$dsn .= "port=$port;" if $port;

# connect to the database
my $conn = DBI->connect($dsn, $username, $password, {'RaiseError' => 1});

# get the cvterm for polypeptide
print "Retrieving polypeptide cvterm\n";
my $peptide = $conn->selectrow_array("SELECT cvterm_id FROM cvterm WHERE name SIMILAR TO 'polypeptide';");
if (!$peptide) {
    die("Failed to retrieve the polypeptide cvterm from the database\n");
}

# get the cvterm for consensus
print "Retrieving multiple sequence alignment cvterm\n";
my $msa = $conn->selectrow_array("SELECT cvterm_ID FROM cvterm WHERE name SIMILAR TO 'consensus';");
if (!$msa) {
    die("Failed to retrieve the consensus cvterm from the database\n");
}

# get the consensus organism
print "Retreiving consensus organism\n";
my $organism = $conn->selectrow_array("SELECT organism_id FROM organism WHERE genus='consensus' AND species='consensus';");
if (!$organism) {
    die("Failed to retriece the consensus organism from the database\n");
}

# get all the polypeptides from the file
my %peps = ();
while (my $line = <FILE>) {
    chomp $line;
    # skip the line if it's not a description line
    if (index($line, ">") != -1) {
        # trim any whitespace from the end of the string
        $line =~ s/\s*$//;
        $line .= "_pep" if (index($line, "_pep") == -1);
        $peps{substr($line, 1)} = 1; # 1 is a placeholder
    }
}
my $num_peps = scalar(keys(%peps));

# construct the query to get the polypeptide features
my $query_string = "SELECT feature_id, uniquename FROM feature WHERE";
my $i = 0;
for my $key (keys(%peps)) {
    print "key: ", $key, "\n";
    $i++;
    $query_string .= " uniquename='$key'";
    $query_string .= " OR" if ($i != $num_peps);
}
$query_string .= ";";
my $query = $conn->prepare($query_string);
$query->execute();

# see if all the polypeptides are in the databasee
print "rows: ", $query->rows, " peps: ", $num_peps, "\n";
if ($query->rows != $num_peps) {
    # open the error file
    print "Some polypeptides were missing\nOpening the error file\n";
    open(ERRORS, '>'.$errorfile) || die("Failed to open the error file: $!\n");
    print "Writing errors\n";
    print ERRORS "Failed to find polypeptides with uniquename:\n";
    # remove polypeptides that were found from the hash
    while (my @row = $query->fetchrow_array()) {
        my ($feature_id, $uniquename) = @row;
        delete $peps{$uniquename};
    }
    # report polypeptides that weren't found
    for my $key (keys(%peps)) {
        print ERRORS "", substr($key, 0, index($key, "_pep")), "\n";
    }
    # clode file and connection
    print "Closing error file\n";
    close(ERRORS);
    undef($query);
    $conn->disconnect();
    # die
    die("Exiting...\n");
}

# if not copy all their polypeptides respective feature_ids
while (my @row = $query->fetchrow_array()) {
    my($feature_id, $uniquename) = @row;
    $peps{$uniquename} = $feature_id; # no need to look them up twice
}

# create the consensus feature and get it's feature_id
print "Creating feature for consensus\n";

$consensus_name .= "-consensus" if (index($consensus_name, "-consensus") == -1);
if (!$conn->do("INSERT INTO feature (organism_id, name, uniquename, type_id) VALUES ($organism, '$consensus_name', '$consensus_name', $msa);")) {
    die("Failed to isnert consensus feature into the feature table\n");
}
my $consensus = $conn->selectrow_array("SELECT feature_id FROM feature WHERE name='$consensus_name' AND uniquename='$consensus_name';");
if (!$consensus) {
    die("Failed to retrieve consensus feature: $consensus_name\n");
}

# create a variable to hold the current name
print "Creating alignment structure and inserting residues\n";
my $name;
# read the file one line at a time
while (my $line = <FILE>) {
    chomp $line;
    # skip the line if it's a comment line
    if ($line =~ /^\#/) {
        next;
    }
    # if it's a description line then get the name
    elsif (index($line, ">") != -1) {
        $name = substr($line, 1, length($line)-1);
        $name .= "_pep" if (index($name, "_pep") == -1);
    }
    # if we have a name and the current line is not a comment it must be a residue
    elsif ($name) {
        # get the feature if it already exists
        #my $feature = $conn->selectrow_array("SELECT feature_id FROM feature WHERE name='$name' AND uniquename='$name';");
        # if it doesn't create one
        #if (!$feature) {
        #    if ($conn->do("INSERT INTO feature (organism_id, name, uniquename, type_id) VALUES ($organism, '$name', '$name', $peptide);")) {
        #        $feature = $conn->selectrow_array("SELECT feature_id FROM feature WHERE name='$name' AND uniquename='$name';");
        #    }
        #    else {
        #        print "Failed to create feature for polypeptide: $name\n";
        #    }
        #}
        #if($feature) {
        my $fmax = length($line);
        if(!$conn->do("INSERT INTO featureloc (feature_id, srcfeature_id, fmin, fmax, residue_info) VALUES ($peps{$name}, $consensus, 0, $fmax, '$line');")) {
        #if(!$conn->do("INSERT INTO featureloc (feature_id, srcfeature_id, fmin, fmax, residue_info) VALUES ($feature, $consensus, 0, $fmax, '$line');")) {
                print "Failed to create featureloc for feature $peps{$name} with src $consensus\n";
            }
        #}
        else {
            print "Failed to get feature: $name\n";
        }
    }
    # if we haven't encountered a name yet and we seem to have a residue just ignore it...
    else {
        next
    }
}

# close all the open stuff
print "Finishing program\n";
$conn->disconnect();
close(FILE);

