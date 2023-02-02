# 1. Extraemos datos de las redes que queremos estudiar

## Datos de expresión
python ../geneci/main.py extract-data expression-data \
            --database DREAM3 --database DREAM4 --database DREAM5 \
            --database IRMA --database SynTReN --database Rogers \
            --database GeneNetWeaver \
            --username TFM-SynapseAccount \
            --password TFM-SynapsePassword \
            --output-dir ../input_data

## Gold standards
python ../geneci/main.py extract-data gold-standard \
            --database DREAM3 --database DREAM4 --database DREAM5 \
            --database IRMA --database SynTReN --database Rogers \
            --database GeneNetWeaver \
            --username TFM-SynapseAccount \
            --password TFM-SynapsePassword \
            --output-dir ../input_data

## Datos de evaluación 
python ../geneci/main.py extract-data evaluation-data \
            --database DREAM3 --database DREAM4 --database DREAM5 \
            --username TFM-SynapseAccount \
            --password TFM-SynapsePassword \
            --output-dir ../input_data

# 2. Inferimos las redes de regulación génica a partir de todos los datos de expresión empleando 
# todas las técnicas disponibles y copiamos las series temporales a la carpeta de salida

for exp_file in ../input_data/*/EXP/*.csv
do
    techniques=("ARACNE" "BC3NET" "C3NET" "CLR" "GENIE3_RF" "GRNBOOST2" 
                    "GENIE3_ET" "MRNET" "MRNETB" "PCIT" "TIGRESS" "KBOOST"
                    "MEOMI" "JUMP3" "NARROMI" "CMI2NI" "RSNET" "PCACMI"
                    "LOCPCACMI" "PLSNET" "PIDC" "PUC" "GRNVBEM" "LEAP" 
                    "NONLINEARODES" "INFERELATOR")
    lines=$(wc -l < $exp_file)

    # Si la red supera los 20 genes, descartamos JUMP3
    if [ $lines -gt 20 ]
    then
        delete=("JUMP3")
        for del in ${delete[@]}
        do
            techniques=("${techniques[@]/$del}")
        done
    fi

    # Si la red supera los 110 genes, descartamos (además de JUMP3) TIGRESS, CMI2NI, LOCPCACMI, GRNVBEM y NONLINEARODES
    if [ $lines -gt 110 ]
    then
        delete=("TIGRESS" "CMI2NI" "LOCPCACMI" "GRNVBEM" "NONLINEARODES")
        for del in ${delete[@]}
        do
            techniques=("${techniques[@]/$del}")
        done
    fi

    str_tecs=""
    for tec in ${techniques[@]}
    do
        str_tecs+="--technique $tec "
    done

    python ../geneci/main.py infer-network $str_tecs --expression-data $exp_file --output-dir ../template
    cp $exp_file ../template/$(basename $exp_file .csv)/
done

# 3. Para las redes de tipo benchmark evaluamos la precisión de cada una de las técnicas empleadas, así como
# de las redes consenso formadas por la media y mediana de los niveles de confianza

for network_folder in ../template/*/
do
    mkdir -p $network_folder/measurements
    > $network_folder/measurements/techniques.txt

    num_tecs=$(ls $network_folder/lists/*.csv | wc -l)
    weight=$(echo "scale=10; x=1/$num_tecs; if(x<1) print 0; x" | bc)
    summands=""
    files=""

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

    for confidence_list in $network_folder/lists/*.csv
    do 
        python ../geneci/main.py evaluate ${tag}-prediction ${tag}-list-of-links $flags \
                    --confidence-list $confidence_list >> $network_folder/measurements/techniques.txt
        summands+="--weight-file-summand $weight*$confidence_list "
        files+="--file $confidence_list "
    done

    # Media
    python ../geneci/main.py evaluate ${tag}-prediction ${tag}-weight-distribution $flags \
                $summands > $network_folder/measurements/mean.txt
    
    # Mediana
    python median.py $files --output-file "./temporal_list.csv"
    python ../geneci/main.py evaluate ${tag}-prediction ${tag}-list-of-links $flags \
                --confidence-list "./temporal_list.csv" > $network_folder/measurements/median.txt
    rm "./temporal_list.csv"

done
