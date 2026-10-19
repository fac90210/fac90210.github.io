#!/bin/bash
cd /tmp/claude-0/proj
printf "e01 E01\ne02 E02\ne03 E03\ne04 E04\ne05 E05\ne06 E06\ne07 E07\ne08 E08\ne09 E09\ne10 E10\ne11 E11\ne12 E12\ne13 E13\n" | xargs -P4 -L1 bash -c './run.sh $0 $1 > log_hd_$1.txt 2>&1'
echo ALLDONE > hd_done.txt
