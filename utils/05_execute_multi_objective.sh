source ../.venv/bin/activate

# Para cada red ejecutamos GENECI en modo multi-objetivo

## Ordenamos las redes por tamaño de menor a mayor
sizes=()
for network_folder in ../inferred_networks/*/
do
    filename=$(basename $network_folder)
    exp_file="$network_folder/$filename.csv"
    lines=$(wc -l < $exp_file)
    sizes+=($lines)
done
sorted_sizes=($(printf '%s\n' "${sizes[@]}" | sort -nu))

sorted_networks=()
for size in ${sorted_sizes[@]}
do
    for network_folder in ../inferred_networks/*/
    do
        filename=$(basename $network_folder)
        exp_file="$network_folder/$filename.csv"
        lines=$(wc -l < $exp_file)
        if [ $lines == $size ]
        then
            sorted_networks+=($network_folder)
        fi
    done
done

## Aplicamos GNU parallel
opt_ensemble_multi_obj() {
    nf=$1

    if [ -d "$nf/ea_consensus_mo_q-dd-m" ]; then
        return 1
    fi

    str=""
    for confidence_list in $nf/lists/*.csv
    do 
        str+="--confidence-list $confidence_list "
    done

    functions=('quality' 'degreedistribution' 'motifs')
    str_func=""
    for func in ${functions[@]}
    do
        str_func+="--function $func "
    done

    { time python ../geneci/main.py optimize-ensemble $str $str_func --gene-names $nf/gene_names.txt \--time-series $nf/$(basename $nf).csv \
                                                    --crossover-probability 0.9 --num-parents 4 --mutation-probability 0.05 --mutation-strength 0.1 \
                                                    --population-size 300 --num-evaluations 250000 --algorithm NSGAII \
                                                    --plot-fitness-evolution --plot-pareto-front --plot-parallel-coordinates \
                                                    --threads 30 --output-dir $nf/ea_consensus_mo_q-dd-m ; } 2>> $nf/measurements/multi-objective_times.txt
    echo "^ q-dd-m" >> $nf/measurements/multi-objective_times.txt
}
export -f opt_ensemble_multi_obj
parallel --jobs 2 opt_ensemble_multi_obj ::: ${sorted_networks[@]}