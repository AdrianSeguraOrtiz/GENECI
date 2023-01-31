source ../.venv/bin/activate

mkdir -p ../inferred_networks
cp -r ../template/* ../inferred_networks

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
            "eigenvectordistribution"
            "katzdistribution"
            "pagerankdistribution")
functions=($(for f in ${functions[@]}; do echo $f; done | sort))

# Para cada red y función de fitness ejecutamos GENECI en modo mono-objetivo
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

# Para las redes de tipo benchmark evaluamos la precisión de los ensembles generados 

## DREAM3
for network_folder in ../inferred_networks/*-trajectories_exp/
do
    mkdir -p $network_folder/measurements
    > $network_folder/measurements/consensus.txt

    id=$(echo $(basename $network_folder) | cut -d "-" -f 2)
    size=$(echo $(basename $network_folder) | cut -d "-" -f 1)
    size=${size#"InSilicoSize"}

    for consensus_list in $network_folder/ea_consensus_*/final_list.csv
    do 
        python ../geneci/main.py evaluate dream-prediction dream-list-of-links \
                --challenge D3C4 \
                --network-id ${size}_${id} \
                --synapse-file ../input_data/DREAM3/EVAL/PDF_InSilicoSize${size}_${id}.mat \
                --synapse-file ../input_data/DREAM3/EVAL/DREAM3GoldStandard_InSilicoSize${size}_${id}.txt \
                --confidence-list $consensus_list >> $network_folder/measurements/consensus.txt
    done
done

## DREAM4
for network_folder in ../inferred_networks/dream4*_exp/
do
    mkdir -p $network_folder/measurements
    > $network_folder/measurements/consensus.txt

    id=$(echo $(basename $network_folder) | cut -d "_" -f 3)
    id=${id#"0"}
    size=$(echo $(basename $network_folder) | cut -d "_" -f 2)
    size=${size#"0"}

    for consensus_list in $network_folder/ea_consensus_*/final_list.csv
    do 
        python ../geneci/main.py evaluate dream-prediction dream-list-of-links \
                    --challenge D4C2 \
                    --network-id ${size}_${id} \
                    --synapse-file ../input_data/DREAM4/EVAL/pdf_size${size}_${id}.mat \
                    --confidence-list $consensus_list >> $network_folder/measurements/consensus.txt
    done
done

## DREAM5
for network_folder in ../inferred_networks/net*_exp/
do
    mkdir -p $network_folder/measurements
    > $network_folder/measurements/consensus.txt

    id=$(basename $network_folder)
    id=${id#"net"}
    id=${id%"_exp"}

    for consensus_list in $network_folder/ea_consensus_*/final_list.csv
    do 
        python ../geneci/main.py evaluate dream-prediction dream-list-of-links \
                    --challenge D5C4 \
                    --network-id $id \
                    --synapse-file ../input_data/DREAM5/EVAL/DREAM5_NetworkInference_Edges_Network${id}.tsv \
                    --synapse-file ../input_data/DREAM5/EVAL/DREAM5_NetworkInference_GoldStandard_Network${id}.tsv \
                    --synapse-file ../input_data/DREAM5/EVAL/Network${id}_AUPR.mat \
                    --synapse-file ../input_data/DREAM5/EVAL/Network${id}_AUROC.mat \
                    --confidence-list $consensus_list >> $network_folder/measurements/consensus.txt
    done
done

## IRMA
for network_folder in ../inferred_networks/switch-*_exp/
do
    mkdir -p $network_folder/measurements
    > $network_folder/measurements/consensus.txt

    for consensus_list in $network_folder/ea_consensus_*/final_list.csv
    do 
        python ../geneci/main.py evaluate generic-prediction generic-list-of-links \
                    --gs-binary-matrix ./../input_data/IRMA/GS/irma_gs.csv \
                    --confidence-list $consensus_list >> $network_folder/measurements/consensus.txt
    done
done


# Para las redes de tipo benchmark creamos los excel con los resultados de precisión

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

# Unimos todos los resultados en una misma tabla dividiendo por tamaños
sizes=(0 20 110)
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