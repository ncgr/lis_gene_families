#!/bin/bash

for f in `ls ../`; do echo "Converting $f"; gmod_msa_members2trees.pl "../"$f --members "$@" --outfile $f; done
