#!/bin/bash

for f in `ls`; do echo "Converting $f"; gmod_msa_members2msas.pl $f --members "$@" --outfile $f"_members"; done
