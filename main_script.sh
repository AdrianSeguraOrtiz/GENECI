# Sort problems
sizes=()
for network_folder in inferred_networks_rf-mogeneci-mejores-all/*/
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
    for network_folder in inferred_networks_rf-mogeneci-mejores-all/*/
    do
        filename=$(basename $network_folder)
        exp_file="$network_folder/$filename.csv"
        lines=$(wc -l < $exp_file)
        if [ $lines == $size ] && [ ! -d $network_folder/compared_fronts_5 ]
        then
            sorted_networks+=($network_folder)
        fi
    done
done

echo ${sorted_networks[@]} > sorted_networks.txt

opt_ensemble_multi_obj() {
    problem_folder=$1
    i=$2

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

    if [ ! -d $problem_folder/ea_consensus_mo_q-dd-m_0$i ]
    then
        echo "Optimizing ensemble: $problem_folder/ea_consensus_mo_q-dd-m_0$i"
        python3 geneci/main.py optimize-ensemble $str $str_func \
            --gene-names $problem_folder/gene_names.txt \
            --crossover-probability 0.9 --num-parents 4 --mutation-probability 0.05 --mutation-strength 0.1 \
            --population-size 300 --num-evaluations 250000 --algorithm NSGAII \
            --plot-fitness-evolution --plot-pareto-front --plot-parallel-coordinates \
            --threads 10 --output-dir $problem_folder/ea_consensus_mo_q-dd-m_0$i
    fi
}
export -f opt_ensemble_multi_obj
#parallel --jobs 10 opt_ensemble_multi_obj ::: ${sorted_networks[@]} ::: {1..15}

# Unimos todos los frentes de pareto en un solo archivo
: '
for network_folder in ${sorted_networks[@]}
do
    mkdir -p $network_folder/ea_consensus_mo_q-dd-m
    head -n 1 $network_folder/ea_consensus_mo_q-dd-m_01/FUN.csv > $network_folder/ea_consensus_mo_q-dd-m/FUN-All.csv
    tail -n +2 -q $network_folder/ea_consensus_mo_q-dd-m_0*/FUN.csv >> $network_folder/ea_consensus_mo_q-dd-m/FUN-All.csv
    head -n 1 $network_folder/ea_consensus_mo_q-dd-m_01/VAR.csv > $network_folder/ea_consensus_mo_q-dd-m/VAR-All.csv
    tail -n +2 -q $network_folder/ea_consensus_mo_q-dd-m_0*/VAR.csv >> $network_folder/ea_consensus_mo_q-dd-m/VAR-All.csv

    python filter_points.py --fun-file $network_folder/ea_consensus_mo_q-dd-m/FUN-All.csv --var-file $network_folder/ea_consensus_mo_q-dd-m/VAR-All.csv --output-fun $network_folder/ea_consensus_mo_q-dd-m/FUN.csv --output-var $network_folder/ea_consensus_mo_q-dd-m/VAR.csv
done
'

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

    mkdir -p $nf/measurements
    python geneci/main.py evaluate ${tag}-prediction ${tag}-pareto-front $flags \
                --weights-file $nf/ea_consensus_mo_q-dd-m/VAR.csv \
                --fitness-file $nf/ea_consensus_mo_q-dd-m/FUN.csv \
                --confidence-folder $nf/lists \
                --output-dir $nf/measurements
}
export -f pareto_eval
#parallel --jobs 15 pareto_eval ::: ${sorted_networks[@]}


# Set number of points
numpointsvector=(5 10 20)

opt_ensemble_multi_obj_ref() {
    problem_folder=$1
    numpoints=$2
    iteration=$3

    ref_points=()
    ref_points_labels=("aupr-$numpoints" "auroc-$numpoints")
    initial_evaluated_front=$problem_folder/measurements/evaluated_front.csv

    rf=$(python3 get_reference_point.py $initial_evaluated_front "AUPR" $numpoints best)
    ref_points+=($rf)
    echo "${ref_points_labels[0]};$rf" > $problem_folder/reference_point_${ref_points_labels[0]}.csv

    rf=$(python3 get_reference_point.py $initial_evaluated_front "AUROC" $numpoints best)
    ref_points+=($rf)
    echo "${ref_points_labels[1]};$rf" > $problem_folder/reference_point_${ref_points_labels[1]}.csv

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
        if [ ! -d $problem_folder/ea_consensus_mo_q-dd-m_refpoint-${ref_points_labels[$i]}_0$iteration ]
        then
            python3 geneci/main.py optimize-ensemble $str $str_func \
                --gene-names $problem_folder/gene_names.txt \
                --crossover-probability 0.9 --num-parents 4 --mutation-probability 0.05 --mutation-strength 0.1 \
                --population-size 300 --num-evaluations 250000 --algorithm NSGAII \
                --plot-fitness-evolution --plot-pareto-front --plot-parallel-coordinates \
                --reference-point $ref_point \
                --threads 10 --output-dir $problem_folder/ea_consensus_mo_q-dd-m_refpoint-${ref_points_labels[$i]}_0$iteration
        fi
        let i=$i+1
    done
}
export -f opt_ensemble_multi_obj_ref
#parallel --jobs 10 opt_ensemble_multi_obj_ref ::: ${sorted_networks[@]} ::: ${numpointsvector[@]} ::: {1..15}

# Unimos todos los frentes de pareto en un solo archivo
: '
for network_folder in ${sorted_networks[@]}
do
    for numpoints in ${numpointsvector[@]}
    do
        ref_points_labels=("aupr-$numpoints" "auroc-$numpoints")
        for ref_point_label in ${ref_points_labels[@]}
        do
            join_folder=$network_folder/ea_consensus_mo_q-dd-m_refpoint-${ref_point_label}
            mkdir -p $join_folder
            head -n 1 ${join_folder}_01/FUN.csv > $join_folder/FUN-All.csv
            tail -n +2 -q ${join_folder}_0*/FUN.csv >> $join_folder/FUN-All.csv
            head -n 1 ${join_folder}_01/VAR.csv > $join_folder/VAR-All.csv
            tail -n +2 -q ${join_folder}_0*/VAR.csv >> $join_folder/VAR-All.csv

            python filter_points.py --fun-file $join_folder/FUN-All.csv --var-file $join_folder/VAR-All.csv --output-fun $join_folder/FUN.csv --output-var $join_folder/VAR.csv
        
        done
    done
done
'

# Evaluamos los frentes de pareto generados
pareto_eval_ref() {
    nf=$1
    numpoints=$2

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

    ref_points_labels=("aupr-$numpoints" "auroc-$numpoints")
    for ref_point_label in ${ref_points_labels[@]}
    do
        if [ ! -d $nf/refpoint-measurements-${ref_point_label} ]
        then
            mkdir $nf/refpoint-measurements-${ref_point_label}
            python geneci/main.py evaluate ${tag}-prediction ${tag}-pareto-front $flags \
                        --weights-file $nf/ea_consensus_mo_q-dd-m_refpoint-${ref_point_label}/VAR.csv \
                        --fitness-file $nf/ea_consensus_mo_q-dd-m_refpoint-${ref_point_label}/FUN.csv \
                        --confidence-folder $nf/lists \
                        --output-dir $nf/refpoint-measurements-${ref_point_label}
        fi
    done
}
export -f pareto_eval_ref
#parallel --jobs 120 pareto_eval_ref ::: ${sorted_networks[@]} ::: ${numpointsvector[@]}

compare_fronts() {
    problem_folder=$1
    numpoints=$2

    mkdir $problem_folder/compared_fronts_$numpoints
    ref_points_labels=("aupr-$numpoints" "auroc-$numpoints")
    python3 compare_fronts.py \
        --initial-evaluated-front $problem_folder/measurements/evaluated_front.csv \
        --ref-point-evaluated-fronts $problem_folder/refpoint-measurements-${ref_points_labels[0]}/evaluated_front.csv $problem_folder/refpoint-measurements-${ref_points_labels[1]}/evaluated_front.csv \
        --ref-points-csv $problem_folder/reference_point_${ref_points_labels[0]}.csv $problem_folder/reference_point_${ref_points_labels[1]}.csv \
        --output-folder $problem_folder/compared_fronts_$numpoints
}
export -f compare_fronts
#parallel --jobs 15 compare_fronts ::: ${sorted_networks[@]} ::: ${numpointsvector[@]}


# Creamos una carpeta para almacenar todas las comparaciones
: '
mkdir -p ./comparisons
for numpoints in ${numpointsvector[@]}
do
    mkdir -p ./comparisons/numpoints-$numpoints

    # Copiamos los archivos de comparación de frentes de pareto
    for f in inferred_networks_rf-mogeneci-mejores-all/*/compared_fronts_$numpoints/3d_scatter_plot_violin.html
    do
        network=$(basename $(dirname $(dirname $f)))
        cp $f ./comparisons/numpoints-$numpoints/$network.html
    done

    # Concatenamos todos los archivos de AUPR y AUROC en uno solo
    output_file_aupr=./comparisons/numpoints-$numpoints/merge_medians_aupr.csv
    output_file_auroc=./comparisons/numpoints-$numpoints/merge_medians_auroc.csv

    # Encuentra el primer archivo de cada tipo
    first_file_aupr=$(ls inferred_networks_rf-mogeneci-mejores-all/*/compared_fronts_$numpoints/medians_aupr.csv | head -n 1)
    first_file_auroc=$(ls inferred_networks_rf-mogeneci-mejores-all/*/compared_fronts_$numpoints/medians_auroc.csv | head -n 1)

    # Extrae la cabecera y agrega "Network" como la primera columna
    echo "Network,$(head -n 1 "$first_file_aupr")" > "$output_file_aupr"
    echo "Network,$(head -n 1 "$first_file_auroc")" > "$output_file_auroc"

    # Añade los datos de todos los archivos AUPR
    for file in inferred_networks_rf-mogeneci-mejores-all/*/compared_fronts_$numpoints/medians_aupr.csv; do
        network=$(basename $(dirname $(dirname $file)))
        echo "$network,$(tail -n +2 "$file")" >> "$output_file_aupr"
    done

    # Añade los datos de todos los archivos AUROC
    for file in inferred_networks_rf-mogeneci-mejores-all/*/compared_fronts_$numpoints/medians_auroc.csv; do
        network=$(basename $(dirname $(dirname $file)))
        echo "$network,$(tail -n +2 "$file")" >> "$output_file_auroc"
    done
done
'

# Test estadistico de Friedman con pruebas no paramétricas de Holm
: '
auprs=($(ls ./comparisons/numpoints-*/merge_medians_aupr.csv))
paste -d ',' ${auprs[@]} > comparisons/tmp_auprs.csv
cut -d',' -f1-2,$(seq -s, 3 4 $(head -n1 comparisons/tmp_auprs.csv | awk -F',' '{print NF}')) comparisons/tmp_auprs.csv > comparisons/auprs.csv
rm comparisons/tmp_auprs.csv

aurocs=($(ls ./comparisons/numpoints-*/merge_medians_auroc.csv))
paste -d ',' ${aurocs[@]} > comparisons/tmp_aurocs.csv
cut -d',' -f1-2,$(seq -s, 4 4 $(head -n1 comparisons/tmp_aurocs.csv | awk -F',' '{print NF}')) comparisons/tmp_aurocs.csv > comparisons/aurocs.csv
rm comparisons/tmp_aurocs.csv

cd utils/controlTest && java Friedman ../../comparisons/auprs.csv > ../../comparisons/auprs.tex && cd ../..
cd utils/controlTest && java Friedman ../../comparisons/aurocs.csv > ../../comparisons/aurocs.tex && cd ../..
'
