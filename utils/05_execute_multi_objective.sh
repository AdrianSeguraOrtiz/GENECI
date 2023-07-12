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

echo ${sorted_networks[@]}

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
                                                    --threads 50 --output-dir $nf/ea_consensus_mo_q-dd-m ; } 2>> $nf/measurements/multi-objective_times.txt
    echo "^ q-dd-m" >> $nf/measurements/multi-objective_times.txt
}
export -f opt_ensemble_multi_obj
parallel --jobs 1 opt_ensemble_multi_obj ::: ${sorted_networks[@]}

# Evaluamos los frentes de pareto generados

pareto_eval() {
    nf=$1

    mkdir -p $nf/measurements

    base=$(basename $nf)
    if [[ $base =~ ^.*-trajectories_exp ]]
    then
        dream=true
        id=$(echo $base | cut -d "-" -f 2)
        size=$(echo $base | cut -d "-" -f 1)
        size=${size#"InSilicoSize"}

        challenge="D3C4"
        network_id="${size}_${id}"
        eval_files_str="--synapse-file ../input_data/DREAM3/EVAL/PDF_InSilicoSize${size}_${id}.mat --synapse-file ../input_data/DREAM3/EVAL/DREAM3GoldStandard_InSilicoSize${size}_${id}.txt"

    elif [[ $base =~ ^dream4.*_exp ]]
    then
        dream=true
        id=$(echo $base | cut -d "_" -f 3)
        id=${id#"0"}
        size=$(echo $base | cut -d "_" -f 2)
        size=${size#"0"}

        challenge="D4C2"
        network_id="${size}_${id}"
        eval_files_str="--synapse-file ../input_data/DREAM4/EVAL/pdf_size${size}_${id}.mat"

    elif [[ $base =~ ^net.*_exp ]]
    then
        dream=true
        id=${base#"net"}
        id=${id%"_exp"}

        challenge="D5C4"
        network_id="$id"
        eval_files_str="--synapse-file ../input_data/DREAM5/EVAL/DREAM5_NetworkInference_Edges_Network${id}.tsv --synapse-file ../input_data/DREAM5/EVAL/DREAM5_NetworkInference_GoldStandard_Network${id}.tsv --synapse-file ../input_data/DREAM5/EVAL/Network${id}_AUPR.mat --synapse-file ../input_data/DREAM5/EVAL/Network${id}_AUROC.mat"

    elif [[ $base =~ ^switch-.*_exp ]]
    then
        dream=false
        gs="../input_data/IRMA/GS/irma_gs.csv"
    else
        dream=false
        name=${base%"_exp"}
        gs=$(ls ../input_data/*/GS/${name}_gs.csv)
    fi

    if [ "$dream" = true ]
    then
        tag="dream"
        flags="--challenge $challenge --network-id $network_id $eval_files_str"
    else
        tag="generic"
        flags="--gs-binary-matrix $gs"
    fi

    python ../geneci/main.py evaluate ${tag}-prediction ${tag}-pareto-front $flags \
                --weights-file $nf/ea_consensus_mo_q-dd-m/VAR.csv \
                --fitness-file $nf/ea_consensus_mo_q-dd-m/FUN.csv \
                --confidence-folder $nf/lists \
                --output-dir $nf/measurements
}
export -f pareto_eval
parallel --jobs 10 pareto_eval ::: ${sorted_networks[@]}

# Juntamos los valores de precisión de las técnicas con los de geneci
for network_folder in ${sorted_networks[@]}
do
    tecs_file=$(ls $network_folder/measurements/*-techniques_scores.csv)
    python join_scores.py --tecs-file $tecs_file \
                                --geneci-file $network_folder/measurements/evaluated_front.csv \
                                --mean-file $network_folder/measurements/mean.txt \
                                --median-file $network_folder/measurements/median.txt \
                                --output-file $network_folder/measurements/scores.csv
done