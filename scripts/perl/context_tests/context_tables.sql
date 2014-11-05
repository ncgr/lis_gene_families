BEGIN;
CREATE TABLE "db" (
    "db_id" integer NOT NULL SERIAL PRIMARY KEY,
    "name" varchar(255) NOT NULL UNIQUE,
    "description" varchar(255) NOT NULL,
    "urlprefix" varchar(255) NOT NULL,
    "url" varchar(255) NOT NULL
)
;
CREATE TABLE "dbxref" (
    "dbxref_id" integer NOT NULL SERIAL PRIMARY KEY,
    "db_id" integer NOT NULL REFERENCES "db" ("db_id") DEFERRABLE INITIALLY DEFERRED,
    "accession" varchar(255) NOT NULL,
    "version" varchar(255) NOT NULL,
    "description" text NOT NULL
)
;
CREATE TABLE "cv" (
    "cv_id" integer NOT NULL SERIAL PRIMARY KEY,
    "name" varchar(255) NOT NULL UNIQUE,
    "definition" text NOT NULL
)
;
CREATE TABLE "featureloc" (
    "featureloc_id" integer NOT NULL SERIAL PRIMARY KEY,
    "feature_id" integer NOT NULL,
    "srcfeature_id" integer,
    "fmin" integer,
    "is_fmin_partial" boolean NOT NULL,
    "fmax" integer,
    "is_fmax_partial" boolean NOT NULL,
    "strand" smallint,
    "phase" integer,
    "residue_info" text NOT NULL,
    "locgroup" integer NOT NULL,
    "rank" integer NOT NULL
)
;
CREATE TABLE "organism" (
    "organism_id" integer NOT NULL SERIAL PRIMARY KEY,
    "abbreviation" varchar(255) NOT NULL,
    "genus" varchar(255) NOT NULL,
    "species" varchar(255) NOT NULL,
    "common_name" varchar(255) NOT NULL,
    "comment" text NOT NULL
)
;
CREATE TABLE "featureprop" (
    "featureprop_id" integer NOT NULL SERIAL PRIMARY KEY,
    "feature_id" integer NOT NULL,
    "type_id" integer NOT NULL,
    "value" text NOT NULL,
    "rank" integer NOT NULL
)
;
/*
CREATE TABLE "feature_relationship" (
    "feature_relationship_id" integer NOT NULL PRIMARY KEY,
    "subject_id" integer NOT NULL,
    "object_id" integer NOT NULL,
    "type_id" integer NOT NULL,
    "value" text NOT NULL,
    "rank" integer NOT NULL
)
;
*/
CREATE TABLE "feature" (
    "feature_id" integer NOT NULL SERIAL PRIMARY KEY,
    "dbxref_id" integer REFERENCES "dbxref" ("dbxref_id") DEFERRABLE INITIALLY DEFERRED,
    "organism_id" integer NOT NULL REFERENCES "organism" ("organism_id") DEFERRABLE INITIALLY DEFERRED,
    "name" varchar(255) NOT NULL,
    "uniquename" text NOT NULL,
    "residues" text NOT NULL,
    "seqlen" integer,
    "md5checksum" varchar(32) NOT NULL,
    "type_id" integer NOT NULL,
    "is_analysis" boolean NOT NULL,
    "is_obsolete" boolean NOT NULL,
    "timeaccessioned" timestamp with time zone NOT NULL,
    "timelastmodified" timestamp with time zone NOT NULL
)
;
ALTER TABLE "featureloc" ADD CONSTRAINT "feature_id_refs_feature_id_3614c62d" FOREIGN KEY ("feature_id") REFERENCES "feature" ("feature_id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "featureloc" ADD CONSTRAINT "srcfeature_id_refs_feature_id_3614c62d" FOREIGN KEY ("srcfeature_id") REFERENCES "feature" ("feature_id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "featureprop" ADD CONSTRAINT "feature_id_refs_feature_id_107cbe6f" FOREIGN KEY ("feature_id") REFERENCES "feature" ("feature_id") DEFERRABLE INITIALLY DEFERRED;
/*
ALTER TABLE "feature_relationship" ADD CONSTRAINT "subject_id_refs_feature_id_61bbb3c3" FOREIGN KEY ("subject_id") REFERENCES "feature" ("feature_id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "feature_relationship" ADD CONSTRAINT "object_id_refs_feature_id_61bbb3c3" FOREIGN KEY ("object_id") REFERENCES "feature" ("feature_id") DEFERRABLE INITIALLY DEFERRED;
CREATE TABLE "analysis" (
    "analysis_id" integer NOT NULL PRIMARY KEY,
    "name" varchar(255) NOT NULL,
    "description" text NOT NULL,
    "program" varchar(255) NOT NULL,
    "programversion" varchar(255) NOT NULL,
    "algorithm" varchar(255) NOT NULL,
    "sourcename" varchar(255) NOT NULL,
    "sourceversion" varchar(255) NOT NULL,
    "sourceuri" text NOT NULL,
    "timeexecuted" timestamp with time zone NOT NULL
)
;
*/
CREATE TABLE "cvterm" (
    "cvterm_id" integer NOT NULL SERIAL PRIMARY KEY,
    "cv_id" integer NOT NULL REFERENCES "cv" ("cv_id") DEFERRABLE INITIALLY DEFERRED,
    "name" varchar(1024) NOT NULL,
    "definition" text NOT NULL,
    "dbxref_id" integer NOT NULL UNIQUE REFERENCES "dbxref" ("dbxref_id") DEFERRABLE INITIALLY DEFERRED,
    "is_obsolete" integer NOT NULL,
    "is_relationshiptype" integer NOT NULL
)
;
ALTER TABLE "featureprop" ADD CONSTRAINT "type_id_refs_cvterm_id_8381b794" FOREIGN KEY ("type_id") REFERENCES "cvterm" ("cvterm_id") DEFERRABLE INITIALLY DEFERRED;
/*
ALTER TABLE "feature_relationship" ADD CONSTRAINT "type_id_refs_cvterm_id_84dbd372" FOREIGN KEY ("type_id") REFERENCES "cvterm" ("cvterm_id") DEFERRABLE INITIALLY DEFERRED;
*/
ALTER TABLE "feature" ADD CONSTRAINT "type_id_refs_cvterm_id_0158f16d" FOREIGN KEY ("type_id") REFERENCES "cvterm" ("cvterm_id") DEFERRABLE INITIALLY DEFERRED;
/*
CREATE TABLE "phylonode" (
    "phylonode_id" integer NOT NULL PRIMARY KEY,
    "phylotree_id" integer NOT NULL,
    "parent_phylonode_id" integer,
    "left_idx" integer NOT NULL,
    "right_idx" integer NOT NULL,
    "type_id" integer REFERENCES "cvterm" ("cvterm_id") DEFERRABLE INITIALLY DEFERRED,
    "feature_id" integer REFERENCES "feature" ("feature_id") DEFERRABLE INITIALLY DEFERRED,
    "label" varchar(255) NOT NULL,
    "distance" double precision
)
;
ALTER TABLE "phylonode" ADD CONSTRAINT "parent_phylonode_id_refs_phylonode_id_51f18df4" FOREIGN KEY ("parent_phylonode_id") REFERENCES "phylonode" ("phylonode_id") DEFERRABLE INITIALLY DEFERRED;
CREATE TABLE "phylotree" (
    "phylotree_id" integer NOT NULL PRIMARY KEY,
    "dbxref_id" integer NOT NULL REFERENCES "dbxref" ("dbxref_id") DEFERRABLE INITIALLY DEFERRED,
    "name" varchar(255) NOT NULL,
    "type_id" integer REFERENCES "cvterm" ("cvterm_id") DEFERRABLE INITIALLY DEFERRED,
    "analysis_id" integer REFERENCES "analysis" ("analysis_id") DEFERRABLE INITIALLY DEFERRED,
    "comment" text NOT NULL
)
;
ALTER TABLE "phylonode" ADD CONSTRAINT "phylotree_id_refs_phylotree_id_36a0bc6e" FOREIGN KEY ("phylotree_id") REFERENCES "phylotree" ("phylotree_id") DEFERRABLE INITIALLY DEFERRED;
*/
CREATE TABLE "gene_order" (
    "gene_order_id" integer NOT NULL SERIAL PRIMARY KEY,
    "chromosome_id" integer NOT NULL REFERENCES "feature" ("feature_id") DEFERRABLE INITIALLY DEFERRED,
    "gene_id" integer NOT NULL REFERENCES "feature" ("feature_id") DEFERRABLE INITIALLY DEFERRED,
    "number" integer
)
;

COMMIT;
