#!/bin/bash

for ft in ../inferred_networks/*/measurements/functions_times.txt
do
    declare -A algorithm_times

    while read line; do
    if [[ $line =~ \^ ]]; then
        algorithm=${line#"^ "}
        paragraph=$(tail -n 4 <<< "$(grep -B 4 -E "\^ $algorithm" $ft)")
        algorithm_times[$algorithm]=$paragraph
    fi
    done < $ft

    echo "" > temp
    for paragraph in "${algorithm_times[@]}"; do
    echo -e "$paragraph \n" >> temp
    done
    mv temp $ft

    unset algorithm_times
done