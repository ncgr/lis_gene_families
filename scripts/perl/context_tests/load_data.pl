#!/usr/bin/env perl


use strict;
use warnings;
use Getopt::Long; # get the command line options
use Pod::Usage; # so the user knows what's going on
use DBI; # our DataBase Interface
use lib qw(..); # for json parsing
use JSON qw( );


=head1 NAME

load_data.pl - Orders all the genes in the database by their order on their respective chromosomes in the featureprop table.

=head1 SYNOPSIS

  load_data.pl <input file> [options]

  --dbname      The name of the chado database (default=chado)
  --username    The username to access the database with (default=chado)
  --password    The password to log into the database with
  --host        The host the database is on (default=localhost)
  --port        The port the database is on

=head1 DESCRIPTION

Loads the data from the given json file into the context test database. The json file should contain gene_order and featureprop information as specified in the json schema. Other database entries such as organism and featureloc will be inferred from the information provided. Unless otherwise specified by the flags, the database information will be read from the GMOD Chado environment variables.

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
    if( !$conn->do("INSERT INTO cv (name, definition) VALUES('fake', 'there''s a high probability this cv was not entered by a GMOD tool.');") ) {
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
    if( !$conn->do("INSERT INTO db (name, description, urlprefix, url) VALUES('fake', 'there''s a high probability this db was not entered by a GMOD tool.', '', '');") ) {
        Retreat("Failed to insert 'fake' db\n");
    }
    $db_id = get_db();

}

# dbxref helper function
sub get_dbxref {
    return $conn->selectrow_array("SELECT dbxref_id FROM dbxref WHERE description='fake';");
}
sub insert_dbxref {
    return $conn->do("INSERT INTO dbxref (db_id, accession, version, description) VALUES($db_id, 'a', 'a', 'fake');");
}

# cvterm helper functions
sub get_cvterm {
    my $get_cvterm_name = $_[0];
    return $conn->selectrow_array("SELECT cvterm_id FROM cvterm WHERE name='$get_cvterm_name';");
}
sub insert_cvterm {
    my $insert_cvterm_name = $_[0];
    if( !$conn->do("INSERT INTO dbxref (db_id, accession, version, description) VALUES($db_id, 'a', 'a', 'fake');") ) {
        Retreat("Failed to insert 'fake' dbxref for cvterm\n");
    }
    my $insert_cvterm_dbxref_id = $conn->selectrow_array("SELECT dbxref_id FROM dbxref ORDER BY dbxref_id DESC LIMIT 1;");
    # CREATE A DBXREF FOR EACH CVTERM
    return $conn->do("INSERT INTO cvterm (cv_id, name, definition, dbxref_id, is_obsolete, is_relationshiptype) VALUES($cv_id, '$insert_cvterm_name', 'there''s a high probability this db was not entered by a GMOD tool.', $insert_cvterm_dbxref_id, 0, 0);");
}
# get the chromsome cvterm
my $chromosome_id = get_cvterm('chromosome');
if( !$chromosome_id ) {
    if( !insert_cvterm('chromosome') ) {
        Retreat("Failed to insert the chromosome cvterm\n");
    }
    $chromosome_id = get_cvterm('chromosome');
}
# get the gene cvterm
my $gene_id = get_cvterm('gene');
if( !$gene_id ) {
    if( !insert_cvterm('gene') ) {
        Retreat("Failed to retrieve the gene cvterm entry\n");
    }
    $gene_id = get_cvterm('gene');
}
# get the family cvterm
my $family_id = get_cvterm('gene family');
if( !$family_id ) {
    if( !insert_cvterm('gene family') ) {
        Retreat("Failed to insert the gene family cvterm\n");
    }
    $family_id = get_cvterm('gene family');
}
# get the msa cvterm
my $msa_id = get_cvterm('consensus_region');
if( !$msa_id ) {
    if( !insert_cvterm('consensus_region') ) {
        Retreat("Failed to insert the consensus region cvterm\n");
    }
    $msa_id = get_cvterm('consensus_region');
}

# organism helper function
sub get_organism {
    return $conn->selectrow_array("SELECT organism_id FROM organism WHERE common_name='fake';");
}
my $organism_id = get_organism();
if( !$organism_id ) {
    if( !$conn->do("INSERT INTO organism (abbreviation, genus, species, common_name, comment) VALUES('fake', 'fake', 'fake', 'fake', 'there''s a high probability this organism was not entered by a GMOD tool.');") ) {
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
    my $get_feature_name = $_[0];
    my $get_feature_result = $conn->selectrow_array("SELECT feature_id FROM feature WHERE uniquename='$get_feature_name';");
    print $get_feature_result;
    return $get_feature_result;
}
sub insert_feature {
    my $insert_feature_type_id = $_[0];
    my $insert_feature_name = $_[1];
    return $conn->do("INSERT INTO feature (organism_id, name, unique_name, residues, md5checksum, type_id, is_analysis, is_obsolete, timeaccessioned, timelastmodified) VALUES($organism_id, '$insert_feature_name', '$insert_feature_name', '', '', $insert_feature_type_id, 0, 0, '1865-01-01 00:00:00.000000', '1943-01-01 00:00:00.000000');")
}

# featureprop helper function
sub get_featureprop {
    my $get_featureprop_feature_id = $_[0];
    my $get_featureprop_value = $_[1];
    return $conn->selectrow_array("SELECT featureprop_id FROM featureprop WHERE feature_id=$get_featureprop_feature_id AND value='$get_featureprop_value' AND type_id=$family_id;");
}
sub insert_featureprop {
    my $insert_featureprop_feature_id = $_[0];
    my $insert_featureprop_value = $_[1];
    return $conn->do("INSERT INTO featureprop (feature_id, type_id, value, rank) VALUES($insert_featureprop_feature_id, $family_id, '$insert_featureprop_value', 0);")
}

# iterate the featureprops
for( @{$data->{featureprops}} ) {
    # check that all the required fields are present
    my $family_value = $_->{family_value};
    my $gene_name = $_->{gene_name};
    if( !$family_value || !$gene_name ) {
        print "Skipping featureprop with family_value: $family_value, gene_name: $gene_name\n";
        next;
    }
    # check if the feature exists, if not, create it
    my $genes = get_feature($gene_name);
    if( $genes->rows == 2 ) {
        print "Found multiple features for family_value: $family_value, gene_name: $gene_name\n";
        next;
    } elsif( $genes->rows == 0 ) {
        if( !insert_feature($gene_id, $gene_name) ) {
            Retreat("Failed to insert feature for gene_name: $gene_name");
        }
        $genes = get_feature($gene_name);
    }
    # check if the msa exists, if not, create it
    my $msa = get_feature($family_value);
    if( $msa->rows == 0 ) {
        if( !insert_feature($msa_id, $family_value) ) {
            Retreat("Failed to insert msa for family_value: $family_value");
        }
        #$msa = get_feature(undef, $value);
    }
    # check if the featureprop entry already exists, it not, create it
    my $feature_prop = get_featureprop($genes, $family_value);
    if( $feature_prop->rows == 1 ) {
        Retreat("Featureprop already exists for family_value: $family_value, gene_name: $gene_name");
    } else {
        if( !insert_featureprop($genes, $family_value) ) {
            Retreat("Failed to insert featureprop for family_value: $family_value, gene_name: $gene_name");
        }
    }
    # these entries will use msa consensus feature names for values (these should be the uniquenames from the feature table)
}

# gene_order helper functions
sub get_gene_order {
    my $get_gene_order_feature_id = $_[0];
    my $get_gene_order_chromosome_id = $_[1];
    return $conn->selectrow_array("SELECT gene_order_id FROM gene_order WHERE feature_id=$get_gene_order_feature_id AND chromosome_id=$get_gene_order_chromosome_id;");
}
sub insert_gene_order {
    my $insert_gene_order_feature_id = $_[0];
    my $insert_gene_order_chromosome_id = $_[1];
    my $insert_gene_order_number = $_[2];
    return $conn->do("INSERT INTO gene_order (feature_id, chromosome_id, number) VALUES($insert_gene_order_feature_id, $insert_gene_order_chromosome_id, $insert_gene_order_number);")
}
# featureloc helper functions
sub get_featureloc {
    my $get_featureloc_gene_id = $_[0];
    my $get_featureloc_chromosome_id = $_[1];
    return $conn->selectrow_array("SELECT featureloc_id FROM featureloc WHERE feature_id=$get_featureloc_gene_id AND srcfeature_id=$get_featureloc_chromosome_id;");
}
sub insert_featureloc {
    my $insert_featureloc_feature_id = $_[0];
    my $insert_featureloc_chromosome_id = $_[1];
    my $insert_featureloc_fmin = $_[2];
    my $insert_featureloc_fmax = $_[3];
    return $conn->do("INSERT INTO featureloc (feature_id, srcfeature_id, fmin, is_fmin_partial, fmax, is fmax_partial, strand, locgroup, rank) VALUES($insert_featureloc_feature_id, $insert_featureloc_chromosome_id, $insert_featureloc_fmin, false, $insert_featureloc_fmax, false, 1, 0, 0);")
}

# iterate the gene_orders
my %chromosome_fs = ();
for( @{$data->{gene_orders}} ) {
    # check that all the required fields are present
    my $gene_name = $_->{gene_name};
    my $chromosome_name = $_->{chromosome_name};
    my $gene_number = $_->{gene_number};
    if( !$gene_name || !$chromosome_name || !$gene_number ) {
        print "Skipping gene_order with gne_name: $gene_name, chromosome_name: $chromosome_name, gene_number: $gene_number\n";
        next;
    }
    # check if the feature exists, if not, create it
    my $genes = get_feature($gene_name);
    if( $genes->rows == 2 ) {
        print "Found multiple genes for gene_name: $gene_name\n";
        next;
    } elsif( $genes->rows == 0 ) {
        if( !insert_feature($gene_name) ) {
            Retreat("Failed to insert feature for gene_name: $gene_name");
        }
        $genes = get_feature($gene_name);
    }
    # check if the chromosome exists, if not, create it
    my $chromosomes = get_feature($chromosome_name);
    if( $chromosomes->rows == 2 ) {
        print "Found multiple chromosomes for chromosome_name: $chromosome_name\n";
        next;
    } elsif( $chromosomes->rows == 0 ) {
        if( !insert_feature($chromosome_name) ) {
            Retreat("Failed to insert chromosome for chromosome_name: $chromosome_name");
        }
        $chromosomes = get_feature($chromosome_name);
    }
    if( !exists $chromosome_fs{$chromosomes} ) {
        $chromosome_fs{$chromosomes} = 1;
    }
    # check if a gene order entry already exists, if not, create one
    my $gene_orders = get_gene_order($genes, $chromosomes);
    if( $gene_orders->rows != 0 ) {
        print "Gene_order entry already exists for chromosome_name: $chromosome_name, gene_name: $gene_name, gene_number: $gene_number\n";
        next;
    } else {
        if( !insert_gene_order($genes, $chromosomes) ) {
            Retreat("Failed to insert gene_order for chromosome_name: $chromosome_name, gene_name: $gene_name, gene_number: $gene_number");
        }
    }
    # check if a featureloc already exists for the gene and chromosome, if not, create one
    my $featurelocs = get_featureloc($genes, $chromosomes);
    if( $featurelocs->rows != 0 ) {
        print "featureloc entry already exists for chromosome_name: $chromosome_name, gene_name: $gene_name\n";
        next;
    } else {
        if( !insert_featureloc($genes, $chromosomes, $chromosome_fs{$chromosomes}, $chromosome_fs{$chromosomes}+1) ) {
            Retreat("Failed to insert featureloc for chromosome_name: $chromosome_name, gene_name: $gene_name");
        }
    }
    $chromosome_fs{$chromosomes} += 2;
    # each gene's order number should be provided
    # if there are any collisons, throw an error
}

print "Committing changes\n";
#eval{ $conn->commit() } or Retreat("The commit failed\n");
Disconnect();

