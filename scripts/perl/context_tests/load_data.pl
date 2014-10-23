#!/usr/bin/env perl


use strict;
use warnings;
use Getopt::Long; # get the command line options
use Pod::Usage; # so the user knows what's going on
use DBI; # our DataBase Interface
use lib qw(..); # for json parsing
use JSON qw( );


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
my ($help, $port);
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
GetOptions("help|?"             => \$help,
           "dbname=s"           => \$dbname,
           "username=s"         => \$username,
           "password=s"         => \$password,
           "host=s"             => \$host,
           "port=i"             => \$port) || Retreat("Error in command line arguments\n");

# does the user need help?
if( $help || @ARGV != 1 ) {
    pod2usage(2);
}
my $filename = $ARGV[0];

# create a data source name
print "Connecting to the database\n";
my $dsn = "dbi:Pg:dbname=$dbname;host=$host;";
$dsn .= "port=$port;" if $port;

# connect to the database
my $conn = DBI->connect($dsn, $username, $password, {AutoCommit => 0, RaiseError => 1});
my $query;

# a subroutine to call when things get ugly
sub Retreat {
    print "Something went wrong.\nRolling back changes\n";
    eval{ $conn->rollback() } or print "Failed to rollback changes\n";
    Disconnect();
    die( $_[0] );
}

# close the connection
sub Disconnect {
    undef($query);
    $conn->disconnect();
}

print "Fetching preliminaries\n";

# cv helper function
sub get_cv {
    return $conn->selectrow_array("SELECT cv_id FROM cv WHERE name='fake';");
}
# get the fake cv
my $cv_id = get_cv();
if( !$cv_id ) {
    if( !$conn->do("INSERT INTO cv (cv_id, name, definition) VALUES(1, 'fake', 'there''s a high probability this cv was not entered by a GMOD tool.');") ) {
        Retreat("Failed to insert 'fake' cv\n");
    }
    $cv_id = get_cv();
}

# db helper function
sub get_db {
    return $conn->selectrow_array("SELECT db_id FROM db WHERE name='fake';");
}
# get the fake db
my $db_id = get_db();
if( !$db_id ) {
    if( !$conn->do("INSERT INTO db (db_id, name, description, urlprefix, url) VALUES(1, 'fake', 'there''s a high probability this db was not entered by a GMOD tool.', '', '');") ) {
        Retreat("Failed to insert 'fake' db\n");
    }
    $db_id = get_db();

}

# dbxref helper function
sub get_dbxref {
    return $conn->selectrow_array("SELECT dbxref_id FROM dbxref WHERE description='fake';");
}
sub insert_dbxref {
    return $conn->do("INSERT INTO dbxref (dbxref_id, db_id, accession, version, description) VALUES(1, $db_id, 'a', 'a', 'fake');");
}

# cvterm helper functions
sub get_cvterm {
    my $name = $_[0];
    return $conn->selectrow_array("SELECT cvterm_id FROM cvterm WHERE name='$name';");
}
sub insert_cvterm {
    my $id = $_[0];
    my $name = $_[1];
    if( !$conn->do("INSERT INTO dbxref (dbxref_id, db_id, accession, version, description) VALUES($id, $db_id, 'a', 'a', 'fake');") ) {
        Retreat("Failed to insert 'fake' dbxref for cvterm\n");
    }
    return $conn->do("INSERT INTO cvterm (cvterm_id, cv_id, name, definition, dbxref_id, is_obsolete, is_relationshiptype) VALUES($id, $cv_id, '$name', 'there''s a high probability this db was not entered by a GMOD tool.', $id, 0, 0);");
}
# get the chromsome cvterm
my $chromosome_id = get_cvterm('chromosome');
if( !$chromosome_id ) {
    if( !insert_cvterm(1, 'chromosome') ) {
        Retreat("Failed to insert the chromosome cvterm\n");
    }
    $chromosome_id = get_cvterm('chromosome');
}
# get the gene cvterm
my $gene_id = get_cvterm('gene');
if( !$gene_id ) {
    if( !insert_cvterm(2, 'gene') ) {
        Retreat("Failed to retrieve the gene cvterm entry\n");
    }
    $gene_id = get_cvterm('gene');
}
my $family_id = get_cvterm('gene family');
if( !$gene_family ) {
    if( !insert_cvterm(3, 'gene family') ) {
        Retreat("Failed to insert the gene family cvterm\n");
    }
    $family_id = get_cvterm('gene family');
}

# organism helper function
sub get_organism {
    return $conn->selectrow_array("SELECT organism_id FROM organism WHERE common_name='fake';");
}
my $organism_id = get_organism();
if( !$organism_id ) {
    if( !$conn->do("INSERT INTO organism (organism_id, abbreviation, genus, species, common_name, comment) VALUES('fake', 'fake', 'fake', 'fake', 'there''s a high probability this organism was not entered by a GMOD tool.');") ) {
        Retreat("Failed to insert 'fake' organism\n");
    }
    $organism_id = get_organism();
}

# parse the json file
my $json_text = do {
    open( my $json_fh, "<:encoding(UTF-8)", $filename ) or die("Can't open \$filename\": $!\n");
    local $/;
    <$json_fh>
};
my $json = JSON->new;
my $data = $json->decode($json_text);

# feature helper function
sub get_feature {
    my $feature_id = $_[0];
    my $name = $_[1];
    return $conn->selectrow_array("SELECT feature_id FROM feature WHERE feature_id=$feature_id OR uniquename='$name';");
}
sub insert_feature {
    my $feature_id = $_[0];
    my $name = $_[1];
    my $type_id = $[2];
    return $conn->do("INSERT INTO feature (feature_id, organism_id, name, unique_name, residues, md5checksum, type_id, is_analysis, is_obsolete, timeaccessioned, timelastmodified) VALUES($feature_id, $organism_id, '$name', '$name', '', '', $type_id, 0, 0, '1865-01-01 00:00:00.000000', '1943-01-01 00:00:00.000000');")
}

# iterate the featureprops
for( @{$data->{featureprops}} ) {
    # check that all the required fields are present
    my $feature_id = $_->{feature_id};
    my $value = $_->{value};
    my $name = $_->{name} ? $_->{name} : $feature_id;
    if( !$feature_id || !$value ) {
        print "Skipping featureprop with feature_id: $feature_id, value: $value, name: $name\n";
        next;
    }
    # check if the feature exists, if not, create it
    my $genes = get_feature($feature_id, $name);
    if( $genes->rows == 2 ) {
        print "Found multiple features for feature_id: $feature_id, name: $name\n";
        next;
    } elsif( $genes->rows == 0 ) {
        if( !insert_feature($feature_id, $name, $gene_id) ) {
            Retreat("Failed to insert feature for feature_id: $feature_id, name: $name");
        }
    }
    # check if the phylotree/msa exists, if not, create it
    # create the featureprop entry
}

# iterate the gene_orders
for( @{$data->{gene_orders}} ) {
    # check that all the required fields are present
    my $feature_id = $_->{feature_id};
    my $chromosome_id = $_->{chromosome_id};
    my $number = $_->{number};
    if( !$feature_id || !$chromosome_id || !$number ) {
        print "Skipping gene_order with feature_id: $feature_id, chromosome_id: $chromosome_id, number: $number\n";
    }
    # check if the feature exists, if not, create it
    # check if the chromosome exists, if not, create it
    my $genes = get_feature($feature_id, $feature_id);
    if( $genes->rows == 2 ) {
        print "Found multiple features for feature_id: $feature_id\n";
        next;
    }
    my $chromosomes = get_feature($chromosome_id, $chromosome_id);
    if( $chromosomes->rows == 2 ) {
        print "Found multiple features for feature_id: $feature_id\n";
        next;
    }
    if( $features->rows == 0 ) {
        if( !insert_feature($feature_id, $feature_id, $gene_id) ) {
            Retreat("Failed to insert feature for feature_id: $feature_id, name: $name");
        }
    }
    if( $features->rows == 2 ) {
        print "Found multiple features for feature_id: $feature_id, name: $name\n";
    } elsif( $features->rows == 0 ) {
        if( !insert_feature($feature_id, $feature_id, $chromosome_id) ) {
            Retreat("Failed to insert feature for feature_id: $feature_id, name: $name");
        }
    }
    # create the gene_order entry
}


# boot strap
# ----------
#
# db
# dbxref
# cv
# cvterm
#   - chromosome
#   - supercontig
#   - gene
#   - gene family

# manual
# ------
#
# featureprop
# gene_order

# inferred
# --------
#
# feature
# -feature_relationship
# phylotree/consensus?
# -phylonode

# dummy
# -----
#
# featureloc
#   - fmin
#   - fmax
#   - strand
# organism

print "Committing changes\n";
#eval{ $conn->commit() } or Retreat("The commit failed\n");
Disconnect();

