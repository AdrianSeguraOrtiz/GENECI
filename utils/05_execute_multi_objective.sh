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

    { time python ../geneci/main.py optimize-ensemble $str $str_func --gene-names $nf/gene_names.txt --time-series $nf/$(basename $nf).csv --num-evaluations 100000 --population-size 100 --algorithm NSGAII --plot-fitness-evolution --plot-pareto-front --plot-parallel-coordinates --threads 60 --output-dir $nf/ea_consensus_mo_q-dd-m ; } 2>> $nf/measurements/multi-objective_times.txt
    echo "^ q-dd-m" >> $nf/measurements/multi-objective_times.txt
}
export -f opt_ensemble_multi_obj
parallel --jobs 2 opt_ensemble_multi_obj ::: ${sorted_networks[@]}

# Evaluamos el frente obtenido para cada red
## DREAM3
for network_folder in ../inferred_networks/*-trajectories_exp/
do
    id=$(echo $(basename $network_folder) | cut -d "-" -f 2)
    size=$(echo $(basename $network_folder) | cut -d "-" -f 1)
    size=${size#"InSilicoSize"}

    str=""
    for confidence_list in $network_folder/lists/*.csv
    do 
        str+="--confidence-list $confidence_list "
    done

    python ../geneci/main.py evaluate dream-prediction dream-pareto-front $str \
        --challenge D3C4 \
        --network-id ${size}_${id} \
        --synapse-file ../input_data/DREAM3/EVAL/PDF_InSilicoSize${size}_${id}.mat \
        --synapse-file ../input_data/DREAM3/EVAL/DREAM3GoldStandard_InSilicoSize${size}_${id}.txt \
        --weights-file $network_folder/ea_consensus/VAR.csv \
        --fitness-file $network_folder/ea_consensus/FUN.csv
done

## DREAM4
for network_folder in ../inferred_networks/dream4*_exp/
do
    id=$(echo $(basename $network_folder) | cut -d "_" -f 3)
    id=${id#"0"}
    size=$(echo $(basename $network_folder) | cut -d "_" -f 2)
    size=${size#"0"}

    str=""
    for confidence_list in $network_folder/lists/*.csv
    do 
        str+="--confidence-list $confidence_list "
    done

    python ../geneci/main.py evaluate dream-prediction dream-pareto-front $str \
        --challenge D4C2 \
        --network-id ${size}_${id} \
        --synapse-file ../input_data/DREAM4/EVAL/pdf_size${size}_${id}.mat \
        --weights-file $network_folder/ea_consensus/VAR.csv \
        --fitness-file $network_folder/ea_consensus/FUN.csv
done

## DREAM5
for network_folder in ../inferred_networks/net*_exp/
do
    id=$(basename $network_folder)
    id=${id#"net"}
    id=${id%"_exp"}

    str=""
    for confidence_list in $network_folder/lists/*.csv
    do 
        str+="--confidence-list $confidence_list "
    done

    python ../geneci/main.py evaluate dream-prediction dream-pareto-front $str \
        --challenge D5C4 \
        --network-id $id \
        --synapse-file ../input_data/DREAM5/EVAL/DREAM5_NetworkInference_Edges_Network${id}.tsv \
        --synapse-file ../input_data/DREAM5/EVAL/DREAM5_NetworkInference_GoldStandard_Network${id}.tsv \
        --synapse-file ../input_data/DREAM5/EVAL/Network${id}_AUPR.mat --synapse-file ../input_data/DREAM5/EVAL/Network${id}_AUROC.mat \
        --weights-file $network_folder/ea_consensus/VAR.csv \
        --fitness-file $network_folder/ea_consensus/FUN.csv
done

## IRMA
for network_folder in ../inferred_networks/switch-*_exp/
do
    str=""
    for confidence_list in $network_folder/lists/*.csv
    do 
        str+="--confidence-list $confidence_list "
    done

    python ../geneci/main.py evaluate generic-prediction generic-pareto-front $str \
        --weights-file $network_folder/ea_consensus/VAR.csv \
        --fitness-file $network_folder/ea_consensus/FUN.csv \
        --gs-binary-matrix ./../input_data/IRMA/GS/irma_gs.csv
done