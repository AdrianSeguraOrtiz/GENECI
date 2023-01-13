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

    > $network_folder/gs_scores/consensus_times.txt
    for func in ${functions[@]}
    do
        echo $func >> $network_folder/gs_scores/consensus_times.txt
        { time python ../geneci/main.py optimize-ensemble $str --gene-names $network_folder/gene_names.txt --time-series $network_folder/$(basename $network_folder).csv --function $func --algorithm GA --plot-evolution --output-dir $network_folder/ea_consensus_$func ; } 2>> $network_folder/gs_scores/consensus_times.txt
    done

done

# Para las redes de tipo benchmark evaluamos la precisión de los ensembles generados 

## DREAM3
for network_folder in ../inferred_networks/*-trajectories_exp/
do
    mkdir -p $network_folder/gs_scores
    > $network_folder/gs_scores/consensus.txt

    id=$(echo $(basename $network_folder) | cut -d "-" -f 2)
    size=$(echo $(basename $network_folder) | cut -d "-" -f 1)
    size=${size#"InSilicoSize"}

    for consensus_list in $network_folder/ea_consensus_*/final_list.csv
    do 
        python ../geneci/main.py evaluate dream-prediction dream-list-of-links --challenge D3C4 --network-id ${size}_${id} --synapse-file ../input_data/DREAM3/EVAL/PDF_InSilicoSize${size}_${id}.mat --synapse-file ../input_data/DREAM3/EVAL/DREAM3GoldStandard_InSilicoSize${size}_${id}.txt --confidence-list $consensus_list >> $network_folder/gs_scores/consensus.txt
    done
done

## DREAM4
for network_folder in ../inferred_networks/dream4*_exp/
do
    mkdir -p $network_folder/gs_scores
    > $network_folder/gs_scores/consensus.txt

    id=$(echo $(basename $network_folder) | cut -d "_" -f 3)
    id=${id#"0"}
    size=$(echo $(basename $network_folder) | cut -d "_" -f 2)
    size=${size#"0"}

    for consensus_list in $network_folder/ea_consensus_*/final_list.csv
    do 
        python ../geneci/main.py evaluate dream-prediction dream-list-of-links --challenge D4C2 --network-id ${size}_${id} --synapse-file ../input_data/DREAM4/EVAL/pdf_size${size}_${id}.mat --confidence-list $consensus_list >> $network_folder/gs_scores/consensus.txt
    done
done

## IRMA
for network_folder in ../inferred_networks/switch-*_exp/
do
    mkdir -p $network_folder/gs_scores
    > $network_folder/gs_scores/consensus.txt

    for consensus_list in $network_folder/ea_consensus_*/final_list.csv
    do 
        python ../geneci/main.py evaluate generic-prediction generic-list-of-links --confidence-list $consensus_list --gs-binary-matrix ./../input_data/IRMA/GS/irma_gs.csv >> $network_folder/gs_scores/consensus.txt
    done
done


# Para las redes de tipo benchmark creamos los excel con los resultados de precisión

## DREAM3
for network_folder in ../inferred_networks/*-trajectories_exp/
do
    id=$(echo $(basename $network_folder) | cut -d "-" -f 2)
    size=$(echo $(basename $network_folder) | cut -d "-" -f 1)
    size=${size#"InSilicoSize"}

    name="D3_${size}_${id}"
    file=$network_folder/gs_scores/${name}-functions_scores.csv.csv
    echo "$name;$name;$name;$name;$name" > $file
    echo "Fitness Function;AUPR;AUROC;Mean;Time" >> $file

    aupr=($(grep -o "AUPR: 0.[0-9]*" $network_folder/gs_scores/consensus.txt | cut -d " " -f 2))
    auroc=($(grep -o "AUROC: 0.[0-9]*" $network_folder/gs_scores/consensus.txt | cut -d " " -f 2))
    times=($(grep -Po "real[^ ]*" $network_folder/gs_scores/consensus_times.txt | cut -d $'\t' -f 2))

    for (( i=0; i<${#functions[@]}; i++ ))
    do
        mean=$(echo "scale=10; x=(${aupr[$i]}+${auroc[$i]})/2; if(x<1) print 0; x" | bc)
        echo "${functions[$i]};${aupr[$i]};${auroc[$i]};$mean;${times[$i]}" >> $file
    done
done

## DREAM4
for network_folder in ../inferred_networks/dream4*_exp/
do
    id=$(echo $(basename $network_folder) | cut -d "_" -f 3)
    id=${id#"0"}
    size=$(echo $(basename $network_folder) | cut -d "_" -f 2)
    size=${size#"0"}

    name="D4_${size}_${id}"
    file=$network_folder/gs_scores/${name}-functions_scores.csv.csv
    echo "$name;$name;$name;$name;$name" > $file
    echo "Fitness Function;AUPR;AUROC;Mean;Time" >> $file

    aupr=($(grep -o "AUPR: 0.[0-9]*" $network_folder/gs_scores/consensus.txt | cut -d " " -f 2))
    auroc=($(grep -o "AUROC: 0.[0-9]*" $network_folder/gs_scores/consensus.txt | cut -d " " -f 2))
    times=($(grep -Po "real[^ ]*" $network_folder/gs_scores/consensus_times.txt | cut -d $'\t' -f 2))

    for (( i=0; i<${#functions[@]}; i++ ))
    do
        mean=$(echo "scale=10; x=(${aupr[$i]}+${auroc[$i]})/2; if(x<1) print 0; x" | bc)
        echo "${functions[$i]};${aupr[$i]};${auroc[$i]};$mean;${times[$i]}" >> $file
    done
done

## IRMA
for network_folder in ../inferred_networks/switch-*_exp/
do
    id=$(basename $network_folder)
    id=${id%"_exp"}

    name="IRMA_${id}"
    file=$network_folder/gs_scores/${name}-functions_scores.csv.csv
    echo "$name;$name;$name;$name;$name" > $file
    echo "Fitness Function;AUPR;AUROC;Mean;Time" >> $file

    aupr=($(grep -o "AUPR: 0.[0-9]*" $network_folder/gs_scores/consensus.txt | cut -d " " -f 2))
    auroc=($(grep -o "AUROC: 0.[0-9]*" $network_folder/gs_scores/consensus.txt | cut -d " " -f 2))
    times=($(grep -Po "real[^ ]*" $network_folder/gs_scores/consensus_times.txt | cut -d $'\t' -f 2))

    for (( i=0; i<${#functions[@]}; i++ ))
    do
        mean=$(echo "scale=10; x=(${aupr[$i]}+${auroc[$i]})/2; if(x<1) print 0; x" | bc)
        echo "${functions[$i]};${aupr[$i]};${auroc[$i]};$mean;${times[$i]}" >> $file
    done
done

# Unimos todos los resultados en una misma tabla
chmod a+x paste.pl
./paste.pl ../inferred_networks/*/gs_scores/*-functions_scores.csv.csv > all_networks_functions_scores.csv

echo -e ";$(cat all_networks_functions_scores.csv)" > all_networks_functions_scores.csv
cols="1"
networks=($(ls ../inferred_networks/))
max=$(( ${#networks[@]}*5+2 ))
for i in `seq 7 5 $max`
do
    cols+=",$i"
done

cut -d ';' -f$cols --complement all_networks_functions_scores.csv > tmp.csv && mv -f tmp.csv all_networks_functions_scores.csv

# Creamos la tabla de AUPR para el test estadístico
max=$(( ${#networks[@]}*4+1 ))
cols="1"
for i in `seq 2 4 $max`
do
    cols+=",$i"
done
cut -d ';' -f$cols all_networks_functions_scores.csv | awk 'NR != 2' | csvtool transpose -t ';' - | tr ';' ',' > AUPR_functions.csv
sed -i '1s/^/Network/' AUPR_functions.csv


# Creamos la tabla de AUROC para el test estadístico
max=$(( ${#networks[@]}*4+1 ))
cols="1"
for i in `seq 3 4 $max`
do
    cols+=",$i"
done
cut -d ';' -f$cols all_networks_functions_scores.csv | awk 'NR != 2' | csvtool transpose -t ';' - | tr ';' ',' > AUROC_functions.csv
sed -i '1s/^/Network/' AUROC_functions.csv

# Creamos una tabla con la media de ambas métricas
max=$(( ${#networks[@]}*4+1 ))
cols="1"
for i in `seq 4 4 $max`
do
    cols+=",$i"
done
cut -d ';' -f$cols all_networks_functions_scores.csv | awk 'NR != 2' | csvtool transpose -t ';' - | tr ';' ',' > Mean_functions.csv
sed -i '1s/^/Network/' Mean_functions.csv

# Ejecutamos los tests de Friedman
cd controlTest && java Friedman.java ../AUPR_functions.csv > ../AUPR_functions.tex && cd ..
cd controlTest && java Friedman.java ../AUROC_functions.csv > ../AUROC_functions.tex && cd ..
cd controlTest && java Friedman.java ../Mean_functions.csv > ../Mean_functions.tex && cd ..

# Creamos tabla de tiempos
max=$(( ${#networks[@]}*4+1 ))
cols="1"
for i in `seq 5 4 $max`
do
    cols+=",$i"
done
cut -d ';' -f$cols all_networks_functions_scores.csv | awk 'NR != 2' | csvtool transpose -t ';' - | tr ';' ',' > Time_functions.csv
sed -i '1s/^/Network/' Time_functions.csv