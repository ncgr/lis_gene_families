Perl
====
These are the scripts that were used with the scripts bundled with Chado to load LIS data. The following is a discussion of how to use the scripts in the data loading pipeline.

## Data loading pipeline

### Organisms

Before any data can be loaded into the database the organism that data corresponds to must be present. Adding your organism can be achieved in two ways:

1. Add the organism using an SQL query:

    ```
    INSERT INTO organism (abbreviation, genus, species, common_name) VALUES ('G.max', 'Glycine', 'max', 'soybean');
    ```
or
2. Using a GMOD tool:

    ```
    gmod_add_organism.pl --abbreviation G.max --genus Glycine --species max --common_name soybean
    ```

### fasta files

fasta files must be loaded before their analyses so that features can be mapped back to their locations on the sequences.

1. Sometimes fasta files have extra content in their name lines. To remove what's in excess use:

    ```
    gmod_fasta_names.pl --names <identifiers_of_names_to_save> --append _pep --outfile <file_to_write>
    ```
Here the argument to `--names` is a camma seperated list (no spaces) of identifiers that will be used to determine what values in the name line will be kept, i.e. `--names AC,TC,contig`. Note that if nothing in a name line matches an identifier then the line will be left blank. The `--append` flag should only be used if a string of text is to be appended to all the names in the file. In this example "\_pep" has been appeneded onto the names, which should be done with all fasta files representing polypeptides since "\_pep" is used by the LIS to allow mRNAs and their polypeptide features to have the same uniquename values while preserving uniqueness. The argument to `--outfile` is the file the processed fasta contents should be written to. If this flag is not provied then the processed contents will be written to stdout.

2. fasta files must be convert to gff3 format in order to be loaded. This is done with a GMOD tool as follows:

    ```
    gmod_fasta2gff3.pl --type <probably_chromosome_or_polypeptide> --fasta_dir /path/to/your/fastas
    ```
Note that only fastas from the same organism should be in the path given as an argument to the `--fasta_dir` flag. All fasta files at that path will be combined into a single gff file.
3. Once the fasta is converted to a gff then you can load it using the GMOD bulk loader:

    ```
    gmod_bulk_load_gff3.pl --organism <common_name> --gfffile <your_converted_fasta_file_name>
    ```
4. If you loaded polypeptides from a fasta file then refer to the Cleaning up section on how to make sure these are appropriately named.

### gff files

As mentioned previously, gff files must be loaded after their fasta file so their features can be mapped to locations on the fasta sequences.

1. Sometimes scores in gff files are non-numeric values. You can remove these and change the value of the source column using:

    ```
    gmod_gff3_prepreprocessor.pl <your_gff_file> --outfile <output_filename>
    ```
2. The bulk loader is supposedly faster if you break your gff file into smaller pieces. Also, the contents of your gff file must be in parent first order for the GMOD bulk loader to accept it. This can all be achieved using a GMOD tool:

    ```
    gmod_gff3_preprocessor.pl --gfffile <your_prepreprocessed_ggf_file> --splitfile 1
    ```
`--splitfile 1` means you'll split the file based on the contents of column 1 - typically the chromosome.
3. If the previous step failed, as it sometimes does, you must split the file by hand. The following bash script splits your prepreprocessed gff file on column one:

    ```
    #!/bin/bash
    for chr in `cat <your_prepreprocessed_gff_file> | cut -f1 | sort | uniq`
    do
        grep "$chr" <your_prepreprocessed_gff_file> > $chr
    done
    ```
As gff files are normally in parent child order, ordering an unordered gff file when the GMOD tool fails is outside the scope of this discussion.
4. To load a single gff file into the database use the GMOD tool:

    ```
    gmod_bulk_load_gff3.pl --gfffile <your_prepreprocessed_gff_file> --organism <organism_common_name> --analysis --noexon
    ```
Here `--gfffile` takes the path to the gff file you want to load as an argument, `--organism` takes the common name of the organism the file corresponds to in the database, and `--analysis` specifies that the gff file is an analysis so that the appropriate entries in the `analysisfeature` table will be created. The `--noexon` flag should only be used if exons are present in the gff file; as part of the loading prosses gmod\_bulk\_load\_gff3.pl infers the exons from the file and will load them unless the `--noexon` flag is given.
5. If you don't want to run the previous command for each piece of your split gff file then use the bash script:

    ```
    gmod_bulk_load_gffs.sh <organism_common_name>
    ````
This script runs the previous command on all files in the current directory with the extensions .gff3 or .gff3.sorted. Note the only argument is the common name of the organism the gff files correspond to.

### Cleaning up

Unfortunately nothing is perfect; sometimes gmod\_bulk\_load\_gff3.pl will create duplicates of polypeptides. Furthermore, the default `uniquename` field values for mRNAs are typically autogenerated as well as the `name` and `uniquename` fields for polypeptides. Here are the solutions for both these problems, respectively.

1. To remove duplicate polypeptides use the following script:

    ```
    gmod_remove_duplicate_polypeptides.pl --organismid <organism_unique_identifier>
    ```
The `--organismid` flag is optional; it should be used if polypeptides for only a single organism are to be targeted. The argument to the flag is the unique idetifier of the organism (it's primary key) from the `organism` table.

2. The following script removes the autogenerated `uniquename` field values from mRNAs by replacing them with the value from the `name` field. It does the same for polypeptides, unless both the `name` and `uniquename` field values are autogenerated, then they are given the value of the polypeptide's mRNA's `uniquename` field. The script also appends "\_pep" to the end of every polypeptides' `name` and `uniquename` field values so to preserve uniqueness of the `uniquename` field in the `feature` table.

    1. Sometimes the `uniquename` field of polypeptides will store a unique identifier associated with the source that feature's analysis came from, i.e. a PACid from the Phytozome database. If you want to preserve these when overwriting the default `uniquename` field values you'll have to create an entry in the `db` table so the values can be stored as entries in the `dbxref` table. Create the entry as follows:

        ```
        INSERT INTO db ( name, description, urlprefix, url ) VALUES ('<db_name>', '<db_description>', '<db_url_prefix>', '<db_url>');
        ```
    2. To remedy the afformentioned use the following script:

        ```
        gmod_mrna_and_peptide_uniquename2name.pl --organismid <organism_unique_identifier> --dbid <db_unique_identifier>
        ```
    As with `gmod_remove_duplicate_polypeptides.pl` the `--organismid` flag is optional. The `--dbid` flag is also also optional. If you opted to preserve the unique identifiers, as discussed in the previous step, the `<db_unique_identifier>` value will be that of the entry you just created in the `db` table (it's primary key). There are also `--nomrna` and `--nopoly` flags that may be used to prevent the targeting of mRNAs and polypeptides, respectively.

As just discuess, some features have a unique identifier associated with the source that feature's analysis came from. In some cases there will be a unique identifier for that feature in a fasta file that doesn't get represnted in the database. The following script reads these unique identifiers from a fasta file and associates them with their polypeptides in the database by creating entries in the `dbxref` table. The script is used as follows:

```
gmod_peptide_dbxref_from_fasta.pl <fasta_file> --dbid <db_unique_identifier>
```
The argument to the `--dbid` flag is the unique identifier (primary key) of the entry you have created for these polypepties' analysis source in the `db` table, as previously discussed. Note the script currently only works with PACids, though, it may be easily extended to work for others as well.

### Multiple Sequence Alignments

Files representing Multiple Sequence Alignments (MSAs) are only loaded if all the polypeptides in the alignment are represented in the databse. If this is the case then a new feature is created to represent the consensus with the given name and "-consensus" as the value for the `name` and `uniquename` fields. Entries are then created in the `featureloc` table for each polypeptide in the MSA with the consensus feature as their source. MSAs are loaded as follws:

1. It is imperative that the names of the polypeptides in the MSA files match those in the database, excluding the "_pep" at the end. This munging is left as an exercise for the user.

2. Like all features, each consensus feature must have an organism. It is recommended that a consensus organism is created for this purpose:

    ```
    INSERT INTO organism (abbreviation, genus, species, common_name) VALUES ('consensus', 'consensus', 'consensus', 'consensus');
    ```
3. An MSA file can be loaed with the script:

    ```
    gmod_load_msa.pl <msa_file> --errorfile <error_file>
    ```
By default to file name is used as the value for the `name` and `uniquename` fields of the consensus feature, unless a different name is given with the `--name` flag. If some polypeptides in the MSA were not found then a list will be written to gmod_load_msa_errors.txt unless the `--errorfile` flag was uesd.

4. If you don't want to run the previous command on each MSA file then use the bash script:

    ```
    gmod_bulk_load_msas.sh
    ```
This script will try to load all the files in the current directory as MSAs, using the filename as the name of the entry in the `feature` table and the name of the error file with "_errors.txt" appended on.

### Phylogenetic trees

Similar to MSA files, files representing phylogenetic trees are only loaded if all the polypeptides in the tree are represented in the database. If this is the case then a new entry is created in the `phylotree` table and an entry is created in the `phylonode` table for each polypeptide in the tree as well as for interior nodes. Trees are loaded as follows:

1. Again, like MSA files, it is imperative that the names of the polypeptides in the phylogenetic tree files match those in the database, excluding the "_pep" at the end. It is up to the user to make sure this is so.

2. Like polypeptide and mRNA entries in the `feature` table have cvterms for their types, phylonodes need cvterms as well. Since there are no cvterm terms for phylogenetic trees by default they must be created.
    
    1. First a controlled vocabulary must be created - an entry in the `cv` table:

        ```
        INSERT INTO cv ( name ) VALUES ('phylo_tree');
        ```
    2. Next three terms (root, interior, and leaf) must be added to this controlled vocabulary - entries in the `cvterm` table. Since each entry in the `cvterm` table needs a corresponding entry in the `dbxref` table an entry in the `db` table must be created, as described in the Cleaning up section.

    3. Then `dbxref` entries can be created:

    ```
    INSERT INTO dbxref ( db_id, accession ) VALUES (<your_db_id>, 'phylo_root');
    INSERT INTO dbxref ( db_id, accession ) VALUES (<your_db_id>, 'phylo_interior');
    INSERT INTO dbxref ( db_id, accession ) VALUES (<your_db_id>, 'phylo_leaf');
    ```
    4. Finally the three terms in the controlled vocaulary can be created:

    ```
    INSERT INTO cvterm ( cv_id, name, dbxref_id ) VALUES (<your_cv_id>, 'phylo_root', <your_phylo_root_dbxref_id>);
    INSERT INTO cvterm ( cv_id, name, dbxref_id ) VALUES (<your_cv_id>, 'phylo_interior', <your_phylo_interior_dbxref_id>);
    INSERT INTO cvterm ( cv_id, name, dbxref_id ) VALUES (<your_cv_id>, 'phylo_leaf', <your_phylo_leaf_dbxref_id>);
    ```

3. Since each eantry in the `phylotree` table requires a dbxref you need to create an entry in the db table for the dbxrefs to refer to, that is, if you want it to be a different entry than the one you made in the previous step.

4. A phylogenetic tree is loaded as follows:

    ```
    gmod_load_tree.pl <phylogenetic_tree_file> --dbid <your_db_id> --errorfile <error_file>
    ```
By default the file name is used as the value for the `name` field of the entry in the `phylotree` table, unless a different name is given with the `--name` flag. The `--dbid` flag takes the unique identifier (primary key) of the entry in the `db` table discussed in the previous step. If some polypeptides in the phylogenetic tree were not found then a list will be written to gmod_load_tree_errors.txt unless the `--errorfile` flag was given.

5. If you don't want to run the previous command on each phylogenetic tree file then use the bash script:

    ```
    gmod_bulk_load_trees.sh <your_db_id>
    ```
This script will try to load all the files in the current directory as phylogenetic trees, using the filename as the name of the entry in the `phylotree` table and the name of the error file with "_errors.txt" appended on.

6. The values of the `left\_idx` and `right\_idx` fields in the `phylonode` table are not automatically assigned by the loader. This is done with another script:

    ```
    gmod_index_trees.pl --rootid <root_phylonode_unique_identifier>
    ```
`--rootid` is optional but can be used to specify the root node of a single tree to be indexed instead of the default - index all trees in the database.

### feature residues

If you have fasta files with sequences for existing entries in the `feature table`, such as mRNAs or polypeptides, you can load them as follows:

1. Use the GMOD tool:

    ```
    gmod_bulk_load_gff3.pl --fastafile <fasta_file> --organism <organism_common_name>
    ```
Again, this is loading sequence data for existing entries in the `feature` table into their `residues` fields. The `--organism` flag takes the common name of the organism the file corresponds to in the database as an argument.

2. If you don't want to run the previous command on every fasta file you want to load then use the bash script:

    ```
    gmod_bulk_load_fasta.pl <organism_common_name>
    ```
This script will try to load all the files in the current directory as fasta files.


