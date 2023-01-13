source ../.venv/bin/activate

functions=('qualitymeanaboveaverage' '0.5*globalclusteringmeasure+0.5*binarizeddegreedistribution' 'consistencywithtimeseriesprogressivecurrentimpact')

# Para cada red ejecutamos GENECI en modo multi-objetivo
for network_folder in ../inferred_networks/*/
do
    str=""
    for confidence_list in $network_folder/lists/*.csv
    do 
        str+="--confidence-list $confidence_list "
    done

    str_func=""
    for func in ${functions[@]}
    do
        str_func+="--function $func "
    done

    python ../geneci/main.py optimize-ensemble $str $str_func \
        --gene-names $network_folder/gene_names.txt \
        --time-series $network_folder/$(basename $network_folder).csv \
        --algorithm SMPSO \
        --plot-evolution \
        --output-dir $network_folder/ea_consensus
done

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