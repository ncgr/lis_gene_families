#!/usr/bin/env perl

use strict;
use warnings;
use Getopt::Long; # get the command line options
use DBI; # our DataBase Interface


=head1 NAME

  $0 - Removes "_members" from the name and uniquename fields of concensus features in a chado database.

=head1 SYSNOPSIS

  % gmod_msa_remove_members.pl

=head1 COMMAND-LINE OPTIONS

  --dbname      The name of the chado database (default=chado)
  --username    The username to access the database with (default=chado)
  --password    The password to log into the database with
  --host        The host the database is on (default=localhost)
  --port        The port the database is on

=head1 DESCRIPTION

Simply run the script and it will fix up the concensus features of the msas in the database.

=head1 AUTHOR

Alan Cleary

Copyright (c) 2013
This library is free software; you can redistribute it and/or modify it under the same terms as Perl itself.

=cut


# get the command line options and environment variables
my $port;
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
           "port=i"             => \$port) || die("Error in command line arguments\n");

# make sure we didn't get any unexpected arguments
if (@ARGV != 0) {
    die("Unexpected argument\nUsage: gmod_msa_remove_member.pl [options]\n");
}

# create a data source name
print "Connecting to database\n";
my $dsn = "dbi:Pg:dbname=$dbname;host=$host;";
$dsn .= "port=$port;" if $port;

# connect to the database
my $conn = DBI->connect($dsn, $username, $password, {'RaiseError' => 1});

# get the cvterm for consensus
print "Retrieving consensus cvterm\n";
my $consensus = $conn->selectrow_array("SELECT cvterm_id FROM cvterm WHERE name SIMILAR TO 'consensus';");
if (!$consensus) {
    $conn->disconnect();
    die("Failed to retieve the consensus cvterm from the database\n");
}

# get all the consensus features whose names need to be fixed
print "Retrieving consensus features\n";
my $query = $conn->prepare("SELECT feature_id, name FROM feature WHERE type_id=$consensus;");
$query->execute();

# update the features
print "Updating features\n";
while (my @row = $query->fetchrow_array()) {
    my ($feature_id, $name) = @row;
    print "feature: $feature_id, name: $name";
    #$name =~ s/_members//;
    my $index = index($name, "_members");
    if ($index != -1) {
        $name = substr($name, 0, $index).substr($name, $index+8);
    }
    print ", new name: $name\n";
    if (!$conn->do("UPDATE feature SET name='$name', uniquename='$name' WHERE feature_id=$feature_id;")) {
        print "Failed to update feature: $feature_id\n";
    }
}

# close the connection
undef($query);
$conn->disconnect();

