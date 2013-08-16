Perl
====
These are the scripts that were used with the scripts bundled with Chado to load LIS data. The following is a description of the scripts in the context of the data loading pipeline.

## Data loading pipeline

### Load an organism

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

1. fasta files must be convert to gff3 format in order to be loaded. This is done with a GMOD tool as follows:
```
gmod_fasta2gff3.pl --type <probably_chromosome_or_polypeptide> --fasta_dir /path/to/your/fastas
```
2. Once the fasta is converted to a gff then you can load it using the GMOD bulk loader:
```
gmod_bulk_load_gff3.pl --organism <common_name> --gfffile <your_converted_fasta_file_name>
```

### gff files

1. Sometimes scores in gff files are non-numeric values. Remove these, and change the value of the source column using:
```
gmod_gff3_prepreprocessor.pl <your_gff_file> --outfile <output_filename>
```
2. The bulk loader is supposedly faster if you break your gff file into smaller pieces. Also, the contents of your gff file must be in parent first order in order for the GMOD bulk loader to accept it. This can all be achieved using a GMOD tool:
```
gmod_gff3_preprocessor.pl --gfffile <your_prepreprocessed_ggf_file> --splitfile 1
```
--splitfile 1 means you'll split the file based on the contents of column 1 - the chromosome.
3. If the previous step failed, as it sometimes does, you must split the file by hand, like so:

```
#!/bin/bash

for chr in `cat <your_prepreprocessed_gff_file> | cut -f1 | sort | uniq`
do
    grep "$chr" <your_prepreprocessed_gff_file> > $chr
done
```

4. Profit!
