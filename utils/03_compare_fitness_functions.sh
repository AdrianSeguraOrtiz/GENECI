# 1. Copiamos la plantilla generada anteriormente a una nueva carpeta. El objetivo es 
# que la plantilla no se vea afectada por la ejecución y pueda volver a ser usada para 
# otros experimentos.

mkdir -p ../inferred_networks
cp -r ../template/* ../inferred_networks

# 2. Definimos la lista de funciones de fitness que queremos ejecutar y las ordenamos alfabeticamente.

functions=("loyaltyprogressivecurrentimpact"
            "loyaltyprogressivenextimpact"
            "loyaltyprogressivenextnextimpact"
            "loyaltyfinal"
            "qualitymean"
            "qualitymedian"
            "qualitymeanaboveaverage"
            "qualitymedianaboveaverage"
            "qualitymeanabovecutoff"
            "qualitymedianabovecutoff"
            "qualitymeanaboveaveragewithcontrast"
            "qualitymedianaboveaveragewithcontrast"
            "averagelocalclusteringmeasure"
            "globalclusteringmeasure"
            "binarizeddegreedistribution"
            "weighteddegreedistribution"
            "betweennessdistribution"
            "closenessdistribution"
            "edgebetweennessdistribution"
            "edgebetweennessreducenonessentialsinteractions"
            "eigenvectordistribution"
            "katzdistribution"
            "pagerankdistribution")
functions=($(for f in ${functions[@]}; do echo $f; done | sort))

# 3. Para cada red y función de fitness ejecutamos GENECI en modo mono-objetivo.

for network_folder in ../inferred_networks/*/
do
    str=""
    for confidence_list in $network_folder/lists/*.csv
    do 
        str+="--confidence-list $confidence_list "
    done

    > $network_folder/measurements/functions_times.txt
    for func in ${functions[@]}
    do
        echo $func >> $network_folder/measurements/functions_times.txt
        { time python ../geneci/main.py optimize-ensemble $str --gene-names $network_folder/gene_names.txt --time-series $network_folder/$(basename $network_folder).csv --function $func --num-evaluations 500000 --population-size 200 --algorithm GA --plot-evolution --output-dir $network_folder/ea_consensus_$func ; } 2>> $network_folder/measurements/functions_times.txt
    done

done

# 4. Para las redes de tipo benchmark evaluamos la precisión de los ensembles generados 

for network_folder in ../inferred_networks/*/
do
    mkdir -p $network_folder/measurements
    > $network_folder/measurements/consensus.txt

    base=$(basename $network_folder)
    if [[ $base =~ [*-trajectories_exp] ]]
    then
        dream=true
        id=$(echo $base | cut -d "-" -f 2)
        size=$(echo $base | cut -d "-" -f 1)
        size=${size#"InSilicoSize"}

        challenge="D3C4"
        network_id="${size}_${id}"
        eval_files_str="--synapse-file ../input_data/DREAM3/EVAL/PDF_InSilicoSize${size}_${id}.mat --synapse-file ../input_data/DREAM3/EVAL/DREAM3GoldStandard_InSilicoSize${size}_${id}.txt"

    elif [[ $base =~ [dream4*_exp] ]]
    then
        dream=true
        id=$(echo $base | cut -d "_" -f 3)
        id=${id#"0"}
        size=$(echo $base | cut -d "_" -f 2)
        size=${size#"0"}

        challenge="D4C2"
        network_id="${size}_${id}"
        eval_files_str="--synapse-file ../input_data/DREAM4/EVAL/pdf_size${size}_${id}.mat"

    elif [[ $base =~ [net*_exp] ]]
    then
        dream=true
        id=${base#"net"}
        id=${id%"_exp"}

        challenge="D5C4"
        network_id="$id"
        eval_files_str="--synapse-file ../input_data/DREAM5/EVAL/DREAM5_NetworkInference_Edges_Network${id}.tsv --synapse-file ../input_data/DREAM5/EVAL/DREAM5_NetworkInference_GoldStandard_Network${id}.tsv --synapse-file ../input_data/DREAM5/EVAL/Network${id}_AUPR.mat --synapse-file ../input_data/DREAM5/EVAL/Network${id}_AUROC.mat"

    elif [[ $base =~ [switch-*_exp] ]]
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

    for consensus_list in $network_folder/ea_consensus_*/final_list.csv
    do 
        python ../geneci/main.py evaluate ${tag}-prediction ${tag}-list-of-links $flags \
                    --confidence-list $consensus_list >> $network_folder/measurements/consensus.txt
    done
done

# 5. Para cada red génica consensuada, creamos una tabla resumen con los resultados de todas las funciones.
# En cada fila se recoge: Función de fitness, AUPR, AUROC, Media((AUPR+AUROC) / 2) y Tiempo de ejecución.

for network_folder in ../inferred_networks/*/
do
    base=$(basename $network_folder)
    if [[ $base =~ [*-trajectories_exp] ]]
    then
        id=$(echo $base | cut -d "-" -f 2)
        size=$(echo $base | cut -d "-" -f 1)
        size=${size#"InSilicoSize"}
        name="D3_${size}_${id}"

    elif [[ $base =~ [dream4*_exp] ]]
    then
        id=$(echo $base | cut -d "_" -f 3)
        id=${id#"0"}
        size=$(echo $base | cut -d "_" -f 2)
        size=${size#"0"}
        name="D4_${size}_${id}"

    elif [[ $base =~ [net*_exp] ]]
    then
        id=${base#"net"}
        id=${id%"_exp"}
        name="D5_${id}"

    elif [[ $base =~ [switch-*_exp] ]]
    then
        id=${base%"_exp"}
        name="IRMA_${id}"
    else
        name=$base
    fi

    file=$network_folder/measurements/${name}-functions_scores.csv.csv
    echo "$name;$name;$name;$name;$name" > $file
    echo "Fitness Function;AUPR;AUROC;Mean;Time" >> $file

    aupr=($(grep -o "AUPR: 0.[0-9]*" $network_folder/measurements/consensus.txt | cut -d " " -f 2))
    auroc=($(grep -o "AUROC: 0.[0-9]*" $network_folder/measurements/consensus.txt | cut -d " " -f 2))
    times=($(grep -Po "real[^ ]*" $network_folder/measurements/functions_times.txt | cut -d $'\t' -f 2))

    for (( i=0; i<${#functions[@]}; i++ ))
    do
        mean=$(echo "scale=10; x=(${aupr[$i]}+${auroc[$i]})/2; if(x<1) print 0; x" | bc)
        echo "${functions[$i]};${aupr[$i]};${auroc[$i]};$mean;${times[$i]}" >> $file
    done
done

# 6. Para cada grupo de tamaños unimos sus tablas en una sola. De esta forma compararemos 
# el rendimiento de las funciones de fitness para diferentes tamaños de redes. Para 
# cuantificar su rendimiento usamos el ranking estadístico de Friedman sobre cada uno de 
# los scores: AUPR, AUROC, Media((AUPR+AUROC) / 2)

sizes=(0 20 110 250)
iters=$(( ${#sizes[@]} - 1 ))
chmod a+x paste.pl
for (( i=0; i<=$iters; i++ ))
do 
    tables=()
    for network_folder in ../inferred_networks/*/
    do
        base=$(basename $network_folder)
        lines=$(wc -l < $network_folder/$base.csv)
        if [ $i == $iters ] && [ $lines -gt ${sizes[$i]} ] || [ $lines -gt ${sizes[$i]} ] && [ $lines -lt ${sizes[$(( $i + 1 ))]} ]
        then
            tables+=($(ls $network_folder/measurements/*-functions_scores.csv))
        fi
    done

    name=${sizes[$i]}
    if [ $i != $iters ]
    then
        name+="-${sizes[$(( $i + 1 ))]}"
    fi

    ./paste.pl $tables > all_networks_${name}_functions_scores.csv
    echo -e ";$(cat all_networks_${name}_functions_scores.csv)" > all_networks_${name}_functions_scores.csv
    cols="1"
    max=$(( ${#tables[@]}*5+2 ))
    for i in `seq 7 5 $max`
    do
        cols+=",$i"
    done

    cut -d ';' -f$cols --complement all_networks_${name}_functions_scores.csv > tmp.csv && mv -f tmp.csv all_networks_${name}_functions_scores.csv

    # Creamos la tabla de AUPR para el test estadístico
    max=$(( ${#tables[@]}*4+1 ))
    cols="1"
    for i in `seq 2 4 $max`
    do
        cols+=",$i"
    done
    cut -d ';' -f$cols all_networks_${name}_functions_scores.csv | awk 'NR != 2' | csvtool transpose -t ';' - | tr ';' ',' > AUPR_${name}_functions.csv
    sed -i '1s/^/Network/' AUPR_${name}_functions.csv


    # Creamos la tabla de AUROC para el test estadístico
    max=$(( ${#tables[@]}*4+1 ))
    cols="1"
    for i in `seq 3 4 $max`
    do
        cols+=",$i"
    done
    cut -d ';' -f$cols all_networks_${name}_functions_scores.csv | awk 'NR != 2' | csvtool transpose -t ';' - | tr ';' ',' > AUROC_${name}_functions.csv
    sed -i '1s/^/Network/' AUROC_${name}_functions.csv

    # Creamos una tabla con la media de ambas métricas
    max=$(( ${#tables[@]}*4+1 ))
    cols="1"
    for i in `seq 4 4 $max`
    do
        cols+=",$i"
    done
    cut -d ';' -f$cols all_networks_${name}_functions_scores.csv | awk 'NR != 2' | csvtool transpose -t ';' - | tr ';' ',' > Mean_${name}_functions.csv
    sed -i '1s/^/Network/' Mean_${name}_functions.csv

    # Ejecutamos los tests de Friedman
    cd controlTest && java Friedman.java ../AUPR_${name}_functions.csv > ../AUPR_${name}_functions.tex && cd ..
    cd controlTest && java Friedman.java ../AUROC_${name}_functions.csv > ../AUROC_${name}_functions.tex && cd ..
    cd controlTest && java Friedman.java ../Mean_${name}_functions.csv > ../Mean_${name}_functions.tex && cd ..

    # Creamos tabla de tiempos
    max=$(( ${#tables[@]}*4+1 ))
    cols="1"
    for i in `seq 5 4 $max`
    do
        cols+=",$i"
    done
    cut -d ';' -f$cols all_networks_${name}_functions_scores.csv | awk 'NR != 2' | csvtool transpose -t ';' - | tr ';' ',' > Time_${name}_functions.csv
    sed -i '1s/^/Network/' Time_${name}_functions.csv
done