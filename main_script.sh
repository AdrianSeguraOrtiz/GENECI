# Sort problems
: '
sizes=()
for network_folder in inferred_networks_final_mogeneci/*/
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
    for network_folder in inferred_networks_final_mogeneci/*/
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
'
sorted_networks=(inferred_networks_final_mogeneci/dream4_010_01_exp/)

opt_ensemble_multi_obj() {
    problem_folder=$1

    ref_points=()
    ref_points_labels=("acc_mean" "aupr" "auroc")
    initial_evaluated_front=$problem_folder/measurements/evaluated_front.csv

    rf=$(python3 get_reference_point.py $initial_evaluated_front "Mean Scaled")
    ref_points+=($rf)
    echo "${ref_points_labels[0]};$rf" > $problem_folder/reference_point_${ref_points_labels[0]}.csv

    rf=$(python3 get_reference_point.py $initial_evaluated_front "AUPR")
    ref_points+=($rf)
    echo "${ref_points_labels[1]};$rf" > $problem_folder/reference_point_${ref_points_labels[1]}.csv

    rf=$(python3 get_reference_point.py $initial_evaluated_front "AUROC")
    ref_points+=($rf)
    echo "${ref_points_labels[2]};$rf" > $problem_folder/reference_point_${ref_points_labels[2]}.csv

    str=""
    for confidence_list in $problem_folder/lists/*.csv
    do 
        str+="--confidence-list $confidence_list "
    done

    functions=('quality' 'degreedistribution' 'motifs')
    str_func=""
    for func in ${functions[@]}
    do
        str_func+="--function $func "
    done

    let i=0
    for ref_point in ${ref_points[@]}
    do
        python3 geneci/main.py optimize-ensemble $str $str_func \
            --gene-names $problem_folder/gene_names.txt \
            --crossover-probability 0.9 --num-parents 4 --mutation-probability 0.05 --mutation-strength 0.1 \
            --population-size 300 --num-evaluations 250000 --algorithm NSGAII \
            --plot-fitness-evolution --plot-pareto-front --plot-parallel-coordinates \
            --reference-point $ref_point \
            --threads 8 --output-dir $problem_folder/ea_consensus_mo_q-dd-m_refpoint-${ref_points_labels[$i]}
        let i=$i+1
    done
}
export -f opt_ensemble_multi_obj
parallel --jobs 1 opt_ensemble_multi_obj ::: ${sorted_networks[@]}

# Evaluamos los frentes de pareto generados
pareto_eval() {
    nf=$1

    base=$(basename $nf)
    if [[ $base =~ ^.*-trajectories_exp ]]
    then
        dream=true
        id=$(echo $base | cut -d "-" -f 2)
        size=$(echo $base | cut -d "-" -f 1)
        size=${size#"InSilicoSize"}

        challenge="D3C4"
        network_id="${size}_${id}"
        eval_files_str="--synapse-file input_data/DREAM3/EVAL/PDF_InSilicoSize${size}_${id}.mat --synapse-file input_data/DREAM3/EVAL/DREAM3GoldStandard_InSilicoSize${size}_${id}.txt"

    elif [[ $base =~ ^dream4.*_exp ]]
    then
        dream=true
        id=$(echo $base | cut -d "_" -f 3)
        id=${id#"0"}
        size=$(echo $base | cut -d "_" -f 2)
        size=${size#"0"}

        challenge="D4C2"
        network_id="${size}_${id}"
        eval_files_str="--synapse-file input_data/DREAM4/EVAL/pdf_size${size}_${id}.mat"

    elif [[ $base =~ ^net.*_exp ]]
    then
        dream=true
        id=${base#"net"}
        id=${id%"_exp"}

        challenge="D5C4"
        network_id="$id"
        eval_files_str="--synapse-file input_data/DREAM5/EVAL/DREAM5_NetworkInference_Edges_Network${id}.tsv --synapse-file input_data/DREAM5/EVAL/DREAM5_NetworkInference_GoldStandard_Network${id}.tsv --synapse-file input_data/DREAM5/EVAL/Network${id}_AUPR.mat --synapse-file input_data/DREAM5/EVAL/Network${id}_AUROC.mat"

    elif [[ $base =~ ^switch-.*_exp ]]
    then
        dream=false
        gs="input_data/IRMA/GS/irma_gs.csv"
    else
        dream=false
        name=${base%"_exp"}
        gs=$(ls input_data/*/GS/${name}_gs.csv)
    fi

    if [ "$dream" = true ]
    then
        tag="dream"
        flags="--challenge $challenge --network-id $network_id $eval_files_str"
    else
        tag="generic"
        flags="--gs-binary-matrix $gs"
    fi

    ref_points_labels=("acc_mean" "aupr" "auroc")
    for ref_point_label in ${ref_points_labels[@]}
    do
        mkdir -p $nf/refpoint-measurements-$ref_point_label
        python geneci/main.py evaluate ${tag}-prediction ${tag}-pareto-front $flags \
                    --weights-file $nf/ea_consensus_mo_q-dd-m_refpoint-$ref_point_label/VAR.csv \
                    --fitness-file $nf/ea_consensus_mo_q-dd-m_refpoint-$ref_point_label/FUN.csv \
                    --confidence-folder $nf/lists \
                    --output-dir $nf/refpoint-measurements-$ref_point_label
    done
}
export -f pareto_eval
parallel --jobs 2 pareto_eval ::: ${sorted_networks[@]}

compare_fronts() {
    problem_folder=$1

    mkdir $problem_folder/compared_fronts
    ref_points_labels=("acc_mean" "aupr" "auroc")
    python3 compare_fronts.py \
        --initial-evaluated-front $problem_folder/measurements/evaluated_front.csv \
        --ref-point-evaluated-fronts $problem_folder/refpoint-measurements-${ref_points_labels[0]}/evaluated_front.csv $problem_folder/refpoint-measurements-${ref_points_labels[1]}/evaluated_front.csv $problem_folder/refpoint-measurements-${ref_points_labels[2]}/evaluated_front.csv \
        --ref-points-csv $problem_folder/reference_point_${ref_points_labels[0]}.csv $problem_folder/reference_point_${ref_points_labels[1]}.csv $problem_folder/reference_point_${ref_points_labels[2]}.csv \
        --output-folder $problem_folder/compared_fronts
}
export -f compare_fronts
parallel --jobs 2 compare_fronts ::: ${sorted_networks[@]}