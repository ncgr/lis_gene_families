#!/bin/bash

ls=`ls *_errors.txt`;
echo "Compiling files";
gmod_compile_unique_lines.pl $ls | sort > "$@";
