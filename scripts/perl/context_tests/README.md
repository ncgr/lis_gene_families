Context Tests
=============

This directory contains the tools necessary to test the context viewer, currently implemented in the chado django app.
In order for the tools to work, there first must be a database to load the data into.
Testing is done via a bootstrapped database in order to be data and framework independent.

Create a test database as follows

```bash
createdb context_test
```

The tables can then be constructed

```bash
psql context_test < context_tables.sql
```

From here data can be loaded from JSON files

```bash
perl load_data.pl data.json
```

The JSON uses the following schema

```json
{
    "type":"object",
    "$schema": "http://json-schema.org/draft-03/schema",
    "properties":{
        "Phylonodes": {
            "type":"array",
            "items":
                {
                    "type":"object",
                    "properties":{
                        "distance": {
                            "type":"number",
                        },
                        "feature_id": {
                            "type":"number",
                        },
                        "label": {
                            "type":"string",
                        },
                        "left_idx": {
                            "type":"number",
                        },
                        "parent_phylonode_id": {
                            "type":"number",
                        },
                        "phylonode_id": {
                            "type":"number",
                        },
                        "phylotree_id": {
                            "type":"number",
                        },
                        "right_idx": {
                            "type":"number",
                        },
                        "type_id": {
                            "type":"number",
                        }
                    },
                    "required":["phylonode_id", "phylotree_id", "left_idx", "right_idx"]
                }
        },
        "feature_relationships": {
            "type":"array",
            "items":
                {
                    "type":"object",
                    "properties":{
                        "feature_relationship_id": {
                            "type":"number",
                        },
                        "object_id": {
                            "type":"number",
                        },
                        "rank": {
                            "type":"number",
                        },
                        "subject_id": {
                            "type":"number",
                        },
                        "type_id": {
                            "type":"number",
                        },
                        "value": {
                            "type":"string",
                        }
                    },
                    "required":["feature_relationship_id", "subject_id", "object_id", "type_id"]
                }
        },
        "featurelocs": {
            "type":"array",
            "items":
                {
                    "type":"object",
                    "properties":{
                        "feature_id": {
                            "type":"number",
                        },
                        "featureloc_id": {
                            "type":"number",
                        },
                        "fmax": {
                            "type":"number",
                        },
                        "fmin": {
                            "type":"number",
                        },
                        "is_fmax_partial": {
                            "type":"string",
                        },
                        "is_fmin_partial": {
                            "type":"string",
                        },
                        "locgroup": {
                            "type":"number",
                        },
                        "phase": {
                            "type":"number",
                        },
                        "rank": {
                            "type":"number",
                        },
                        "residue_info": {
                            "type":"string",
                        },
                        "srcfeature_id": {
                            "type":"number",
                        },
                        "strand": {
                            "type":"number",
                        }
                    },
                    "required":["featureloc_id", "feature_id"]
                }
        },
        "features": {
            "type":"array",
            "items":
                {
                    "type":"object",
                    "properties":{
                        "dbxref_id": {
                            "type":"number",
                        },
                        "feature_id": {
                            "type":"number",
                        },
                        "is_analysis": {
                            "type":"string",
                        },
                        "is_obsolete": {
                            "type":"string",
                        },
                        "name": {
                            "type":"string",
                        },
                        "organism_id": {
                            "type":"number",
                        },
                        "residues": {
                            "type":"string",
                        },
                        "seqlen": {
                            "type":"number",
                        },
                        "type_id": {
                            "type":"number",
                        },
                        "uniquename": {
                            "type":"string",
                        }
                    },
                    "required":["feature_id", "organism_id", "uniquename", "type_id"]
                }
            

        },
        "organisms": {
            "type":"array",
            "items":
                {
                    "type":"object",
                    "properties":{
                        "abbreviation": {
                            "type":"string",
                        },
                        "comment": {
                            "type":"string",
                        },
                        "common_name": {
                            "type":"string",
                        },
                        "genus": {
                            "type":"string",
                        },
                        "organism_id": {
                            "type":"number",
                        },
                        "species": {
                            "type":"string",
                        }
                    },
                    "required":["organism_id", "genus", "species"]
                }
        },
        "phylotrees": {
            "type":"array",
            "items":
                {
                    "type":"object",
                    "properties":{
                        "analysis_id": {
                            "type":"number",
                        },
                        "comment": {
                            "type":"string",
                        },
                        "dbxref_id": {
                            "type":"number",
                        },
                        "name": {
                            "type":"string",
                        },
                        "phylotree_id": {
                            "type":"number",
                        },
                        "type_id": {
                            "type":"number",
                        }
                    },
                    "required":["phylotree_id", "dbxref_id"]
                }
        }
    }
}
```

Note that the loading script doesn't populate the feature_prop table with gene-family relationships nor does it populate the gene_order table.
This can be done by running the respective scripts for these tasks

```bash
perl gmod_gene_families.pl
perl gmod_gene_ordering.pl
```
