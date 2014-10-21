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
        "featureprops": {
            "type":"array",
            "items":
                {
                    "type":"object",
                    "properties":{
                        "feature_id": {
                            "type":"number",
                        },
                        "value": {
                            "type":"string",
                        },
                        "name": {
                            "type":"string",
                        }
                    },
                    "required":["feature_id", "value"]
                }
        },
        "gene_orders": {
            "type":"array",
            "items":
                {
                    "type":"object",
                    "properties":{
                        "chromosome_id": {
                            "type":"number",
                        },
                        "feature_id": {
                            "type":"number",
                        },
                        "number": {
                            "type":"number",
                        }
                    },
                    "required":["chromosome_id", "feature_id", "number"]
                }
        }
    }
}
```

Note that the corresponding feature, phylotree, and phylonode entries for the given data will be infered.
The feature_id will be used as a feature's name unless one is explicitly given. 
Features that will be used as the focus gene in a search should have names since the a name required by the search url.
Dummy values for dependent tables, such as organism and dbxref, will be used.

```bash
perl gmod_gene_families.pl
perl gmod_gene_ordering.pl
```
