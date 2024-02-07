# Optimizamos el ensemble de las listas de confianza resultantes del paso anterior mediante 25 ejecuciones independientes de cada una de ellas

execute() {
    network_folder=inferred_networks_memegeneci/$1
    distance=$2
    probability=$3
    i=$4

    if [ -d $network_folder/ea_consensus_d-${distance}_p-${probability}_$i ]; then
        exit
    fi

    # Nombre del archivo CSV de entrada y salida
    INPUT_FILE=$(ls $network_folder/*_gs.csv)
    OUTPUT_FILE="$network_folder/tmp_known_interactions.csv"

    # Leer los encabezados de las columnas y almacenarlos en un array
    IFS=',' read -r -a headers < $INPUT_FILE

    # Eliminar las comillas de los encabezados
    headers=("${headers[@]//\"/}")

    # Leer el archivo y obtener todas las interacciones (líneas que contienen "1")
    mapfile -t interactions < <(awk -F, -v OFS=',' 'NR > 1 {for (i=2; i<=NF; i++) if ($i == 1) print NR, i}' $INPUT_FILE)

    # Calcular el 5% del total de interacciones, redondeado hacia arriba
    total_interactions=${#interactions[@]}
    subset_size=$(( (total_interactions * 5 + 99) / 100 )) # Redondeo hacia arriba

    # Seleccionar un subconjunto aleatorio de interacciones
    selected_interactions=$(shuf -n $subset_size -e "${interactions[@]}")

    # Crear o limpiar el archivo de salida
    > $OUTPUT_FILE

    # Procesar las interacciones seleccionadas y escribirlas en el archivo de salida
    for interaction in $selected_interactions; do
        row=$(echo $interaction | cut -d, -f1)
        col=$(echo $interaction | cut -d, -f2)
        from=${headers[$((row-1))]}
        to=${headers[$((col-1))]}
        echo "$from,$to,1" >> $OUTPUT_FILE
    done

    str=""
    for confidence_list in $network_folder/lists/*.csv
    do 
        str+="--confidence-list $confidence_list "
    done

    python geneci/main.py optimize-ensemble $str --gene-names $network_folder/gene_names.txt \
        --known-interactions $OUTPUT_FILE --memetic-distance-type $distance --population-size 100 \
        --num-evaluations 50000 --output-dir $network_folder/ea_consensus_d-${distance}_p-${probability}_$i \
        --memetic-probability $probability --threads 10
}
export -f execute

network_folders=$(ls inferred_networks_memegeneci)
distances=("all" "some" "one")
probabilities=("0.1" "0.25" "0.4" "0.55")
iterations=( $(seq 1 15) )
parallel --jobs 6 execute ::: ${network_folders[@]} ::: ${distances[@]} ::: ${probabilities[@]} ::: ${iterations[@]}


# Para las redes de tipo benchmark evaluamos la precisión de los ensembles generados 

## DREAM3
for network_folder in inferred_networks_memegeneci/*-trajectories_exp/
do
    mkdir $network_folder/gs_scores

    id=$(echo $(basename $network_folder) | cut -d "-" -f 2)
    size=$(echo $(basename $network_folder) | cut -d "-" -f 1)
    size=${size#"InSilicoSize"}

    for distance in ${distances[@]}
    do
        for probability in ${probabilities[@]}
        do
            > $network_folder/gs_scores/consensus_d-${distance}_p-${probability}.txt
            for consensus_list in $network_folder/ea_consensus_d-${distance}_p-${probability}_*/final_list.csv
            do 
                python geneci/main.py evaluate dream-prediction --challenge D3C4 --network-id ${size}_${id} \
                        --synapse-file input_data/DREAM3/EVAL/PDF_InSilicoSize${size}_${id}.mat \
                        --synapse-file input_data/DREAM3/EVAL/DREAM3GoldStandard_InSilicoSize${size}_${id}.txt \
                        --confidence-list $consensus_list >> $network_folder/gs_scores/consensus_d-${distance}_p-${probability}.txt
            done
        done
    done
done

## DREAM4
for network_folder in inferred_networks_memegeneci/dream4*_exp/
do
    mkdir $network_folder/gs_scores

    id=$(echo $(basename $network_folder) | cut -d "_" -f 3)
    id=${id#"0"}
    size=$(echo $(basename $network_folder) | cut -d "_" -f 2)
    size=${size#"0"}

    for distance in ${distances[@]}
    do
        for probability in ${probabilities[@]}
        do
            > $network_folder/gs_scores/consensus_d-${distance}_p-${probability}.txt
            for consensus_list in $network_folder/ea_consensus_d-${distance}_p-${probability}_*/final_list.csv
            do 
                python geneci/main.py evaluate dream-prediction --challenge D4C2 --network-id ${size}_${id} \
                        --synapse-file input_data/DREAM4/EVAL/pdf_size${size}_${id}.mat \
                        --confidence-list $consensus_list >> $network_folder/gs_scores/consensus_d-${distance}_p-${probability}.txt
            done
        done
    done
done

## IRMA
for network_folder in inferred_networks_memegeneci/switch-*_exp/
do
    mkdir $network_folder/gs_scores

    for distance in ${distances[@]}
    do
        for probability in ${probabilities[@]}
        do
            > $network_folder/gs_scores/consensus_d-${distance}_p-${probability}.txt
            for consensus_list in $network_folder/ea_consensus_d-${distance}_p-${probability}_*/final_list.csv
            do 
                python geneci/main.py apply-cut --confidence-list $consensus_list --gene-names $network_folder/gene_names.txt --cut-off-criteria MinConfidence --cut-off-value 0.4
                python geneci/main.py evaluate generic-prediction --inferred-binary-matrix $network_folder/networks/$(basename $consensus_list) \
                        --gs-binary-matrix ./input_data/IRMA/GS/irma_gs.csv >> $network_folder/gs_scores/consensus_d-${distance}_p-${probability}.txt
            done
        done
    done

done

# Para las redes de tipo benchmark creamos los excel con los resultados de precisión

## DREAM3
for network_folder in inferred_networks_memegeneci/*-trajectories_exp/
do
    id=$(echo $(basename $network_folder) | cut -d "-" -f 2)
    size=$(echo $(basename $network_folder) | cut -d "-" -f 1)
    size=${size#"InSilicoSize"}

    name="D3_${size}_${id}"
    file=$network_folder/gs_scores/${name}-gs_table.csv
    echo "$name;$name;$name" > $file
    echo "Technique;AUPR;AUROC" >> $file

    for distance in ${distances[@]}
    do
        for probability in ${probabilities[@]}
        do
            cons_aupr=($(grep -o "AUPR: 0.[0-9]*" $network_folder/gs_scores/consensus_d-${distance}_p-${probability}.txt | cut -d " " -f 2))
            median_aupr=$(python -c "import sys; import statistics; print(statistics.median([float(i) for i in sys.argv[1:]]))" ${cons_aupr[@]})
            cons_auroc=($(grep -o "AUROC: 0.[0-9]*" $network_folder/gs_scores/consensus_d-${distance}_p-${probability}.txt | cut -d " " -f 2))
            median_auroc=$(python -c "import sys; import statistics; print(statistics.median([float(i) for i in sys.argv[1:]]))" ${cons_auroc[@]})
            echo "Median GENECI D-${distance} P-${probability};$median_aupr;$median_auroc" >> $file
        done
    done  
done

## DREAM4
for network_folder in inferred_networks_memegeneci/dream4*_exp/
do
    id=$(echo $(basename $network_folder) | cut -d "_" -f 3)
    id=${id#"0"}
    size=$(echo $(basename $network_folder) | cut -d "_" -f 2)
    size=${size#"0"}

    name="D4_${size}_${id}"
    file=$network_folder/gs_scores/${name}-gs_table.csv
    echo "$name;$name;$name" > $file
    echo "Technique;AUPR;AUROC" >> $file

    for distance in ${distances[@]}
    do
        for probability in ${probabilities[@]}
        do
            cons_aupr=($(grep -o "AUPR: 0.[0-9]*" $network_folder/gs_scores/consensus_d-${distance}_p-${probability}.txt | cut -d " " -f 2))
            median_aupr=$(python -c "import sys; import statistics; print(statistics.median([float(i) for i in sys.argv[1:]]))" ${cons_aupr[@]})
            cons_auroc=($(grep -o "AUROC: 0.[0-9]*" $network_folder/gs_scores/consensus_d-${distance}_p-${probability}.txt | cut -d " " -f 2))
            median_auroc=$(python -c "import sys; import statistics; print(statistics.median([float(i) for i in sys.argv[1:]]))" ${cons_auroc[@]})
            echo "Median GENECI D-${distance} P-${probability};$median_aupr;$median_auroc" >> $file
        done
    done  
done

## IRMA
for network_folder in inferred_networks_memegeneci/switch-*_exp/
do
    id=$(basename $network_folder)
    id=${id%"_exp"}

    name="IRMA_${id}"
    file=$network_folder/gs_scores/${name}-gs_table.csv
    echo "$name;$name;$name" > $file
    echo "Technique;AUPR;AUROC" >> $file

    for distance in ${distances[@]}
    do
        for probability in ${probabilities[@]}
        do
            cons_aupr=($(grep -o "AUPR: 0.[0-9]*" $network_folder/gs_scores/consensus_d-${distance}_p-${probability}.txt | cut -d " " -f 2))
            median_aupr=$(python -c "import sys; import statistics; print(statistics.median([float(i) for i in sys.argv[1:]]))" ${cons_aupr[@]})
            cons_auroc=($(grep -o "AUROC: 0.[0-9]*" $network_folder/gs_scores/consensus_d-${distance}_p-${probability}.txt | cut -d " " -f 2))
            median_auroc=$(python -c "import sys; import statistics; print(statistics.median([float(i) for i in sys.argv[1:]]))" ${cons_auroc[@]})
            echo "Median GENECI D-${distance} P-${probability};$median_aupr;$median_auroc" >> $file
        done
    done  
done

# Comparamos todas las funciones de fitness. Para cuantificar su rendimiento usamos el ranking 
# estadístico de Friedman sobre cada uno de los scores: AUPR, AUROC, Media((AUPR+AUROC) / 2)

chmod a+x paste.pl
mkdir -p parameters_comparison

tables=()
for network_folder in inferred_networks_memegeneci/*/
do
    tables+=($(ls $network_folder/gs_scores/*-gs_table.csv))
done

./paste.pl ${tables[@]} > parameters_comparison/all_networks_parameters_scores.csv
cols="1"
max=$(( ${#tables[@]}*3+2 ))
for j in `seq 5 3 $max`
do
    cols+=",$j"
done
cut -d ';' -f$cols --complement parameters_comparison/all_networks_parameters_scores.csv > tmp.csv && mv -f tmp.csv parameters_comparison/all_networks_parameters_scores.csv
max=$(( ${#tables[@]}*2+2 ))

# Creamos la tabla de AUPR para el test estadístico
cols="1"
for j in `seq 2 2 $max`
do
    cols+=",$j"
done
cut -d ';' -f$cols parameters_comparison/all_networks_parameters_scores.csv | awk 'NR != 2' | csvtool transpose -t ';' - | tr ';' ',' > parameters_comparison/AUPR_parameters.csv

# Creamos la tabla de AUROC para el test estadístico
cols="1"
for j in `seq 3 2 $max`
do
    cols+=",$j"
done
cut -d ';' -f$cols parameters_comparison/all_networks_parameters_scores.csv | awk 'NR != 2' | csvtool transpose -t ';' - | tr ';' ',' > parameters_comparison/AUROC_parameters.csv

# Ejecutamos los tests de Friedman
cd controlTest && java Friedman ../parameters_comparison/AUPR_parameters.csv > ../parameters_comparison/AUPR_parameters.tex && cd ..
cd controlTest && java Friedman ../parameters_comparison/AUROC_parameters.csv > ../parameters_comparison/AUROC_parameters.tex && cd ..