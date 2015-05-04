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
                        "family_value": {
                            "type":"string",
                        },
                        "gene_name": {
                            "type":"string",
                        }
                    },
                    "required":["name", "value"]
                }
        },
        "gene_orders": {
            "type":"array",
            "items":
                {
                    "type":"object",
                    "properties":{
                        "chromosome_name": {
                            "type":"string",
                        },
                        "gene_name": {
                            "type":"string",
                        },
                        "gene_number": {
                            "type":"number",
                        }
                    },
                    "required":["chromosome_name", "gene_name", "gene_number"]
                }
        }
    }
}
```

Note that the corresponding featureloc entries for the given data will be infered.
Dummy values for dependent tables, such as organism and dbxref, will be used.

