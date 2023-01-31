# 1. Extraemos datos de las redes que queremos estudiar

## Datos de expresión
python ../geneci/main.py extract-data expression-data \
            --database DREAM3 --database DREAM4 --database DREAM5 --database IRMA \
            --username TFM-SynapseAccount \
            --password TFM-SynapsePassword \
            --output-dir ../input_data

## Gold standards
python ../geneci/main.py extract-data gold-standard \
            --database DREAM3 --database DREAM4 --database DREAM5 --database IRMA \
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

    if [ $lines -gt 20 ]
    then
        delete=("JUMP3")
        for del in ${delete[@]}
        do
            techniques=("${techniques[@]/$del}")
        done
    fi

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

## DREAM3
for network_folder in ../template/*-trajectories_exp/
do
    mkdir -p $network_folder/gs_scores
    > $network_folder/gs_scores/techniques.txt

    id=$(echo $(basename $network_folder) | cut -d "-" -f 2)
    size=$(echo $(basename $network_folder) | cut -d "-" -f 1)
    size=${size#"InSilicoSize"}

    num_tecs=$(ls $network_folder/lists/*.csv | wc -l)
    weight=$(echo "scale=10; x=1/$num_tecs; if(x<1) print 0; x" | bc)
    summands=""
    files=""

    for confidence_list in $network_folder/lists/*.csv
    do 
        python ../geneci/main.py evaluate dream-prediction dream-list-of-links \
                    --challenge D3C4 \
                    --network-id ${size}_${id} \
                    --synapse-file ../input_data/DREAM3/EVAL/PDF_InSilicoSize${size}_${id}.mat \
                    --synapse-file ../input_data/DREAM3/EVAL/DREAM3GoldStandard_InSilicoSize${size}_${id}.txt \
                    --confidence-list $confidence_list >> $network_folder/gs_scores/techniques.txt
        summands+="--weight-file-summand $weight*$confidence_list "
        files+="--file $confidence_list "
    done

    # Media
    python ../geneci/main.py evaluate dream-prediction dream-weight-distribution \
                --challenge D3C4 \
                --network-id ${size}_${id} \
                --synapse-file ../input_data/DREAM3/EVAL/PDF_InSilicoSize${size}_${id}.mat \
                --synapse-file ../input_data/DREAM3/EVAL/DREAM3GoldStandard_InSilicoSize${size}_${id}.txt \
                $summands > $network_folder/gs_scores/mean.txt
    
    # Mediana
    python median.py $files --output-file "./temporal_list.csv"
    python ../geneci/main.py evaluate dream-prediction dream-list-of-links \
                --challenge D3C4 \
                --network-id ${size}_${id} \
                --synapse-file ../input_data/DREAM3/EVAL/PDF_InSilicoSize${size}_${id}.mat \
                --synapse-file ../input_data/DREAM3/EVAL/DREAM3GoldStandard_InSilicoSize${size}_${id}.txt \
                --confidence-list "./temporal_list.csv" > $network_folder/gs_scores/median.txt
    rm "./temporal_list.csv"
done

## DREAM4
for network_folder in ../template/dream4*_exp/
do
    mkdir -p $network_folder/gs_scores
    > $network_folder/gs_scores/techniques.txt

    id=$(echo $(basename $network_folder) | cut -d "_" -f 3)
    id=${id#"0"}
    size=$(echo $(basename $network_folder) | cut -d "_" -f 2)
    size=${size#"0"}

    num_tecs=$(ls $network_folder/lists/*.csv | wc -l)
    weight=$(echo "scale=10; x=1/$num_tecs; if(x<1) print 0; x" | bc)
    summands=""
    files=""

    for confidence_list in $network_folder/lists/*.csv
    do 
        python ../geneci/main.py evaluate dream-prediction dream-list-of-links \
                    --challenge D4C2 \
                    --network-id ${size}_${id} \
                    --synapse-file ../input_data/DREAM4/EVAL/pdf_size${size}_${id}.mat \
                    --confidence-list $confidence_list >> $network_folder/gs_scores/techniques.txt
        summands+="--weight-file-summand $weight*$confidence_list "
        files+="--file $confidence_list "
    done

    # Media
    python ../geneci/main.py evaluate dream-prediction dream-weight-distribution \
                --challenge D4C2 \
                --network-id ${size}_${id} \
                --synapse-file ../input_data/DREAM4/EVAL/pdf_size${size}_${id}.mat \
                $summands > $network_folder/gs_scores/mean.txt
    
    # Mediana
    python median.py $files --output-file "./temporal_list.csv"
    python ../geneci/main.py evaluate dream-prediction dream-list-of-links \
                --challenge D4C2 \
                --network-id ${size}_${id} \
                --synapse-file ../input_data/DREAM4/EVAL/pdf_size${size}_${id}.mat \
                --confidence-list "./temporal_list.csv" > $network_folder/gs_scores/median.txt
    rm "./temporal_list.csv"
done

## DREAM5
for network_folder in ../template/net*_exp/
do
    mkdir -p $network_folder/gs_scores
    > $network_folder/gs_scores/techniques.txt

    id=$(basename $network_folder)
    id=${id#"net"}
    id=${id%"_exp"}

    num_tecs=$(ls $network_folder/lists/*.csv | wc -l)
    weight=$(echo "scale=10; x=1/$num_tecs; if(x<1) print 0; x" | bc)
    summands=""
    files=""

    for confidence_list in $network_folder/lists/*.csv
    do 
        python ../geneci/main.py evaluate dream-prediction dream-list-of-links \
                    --challenge D5C4 \
                    --network-id $id \
                    --synapse-file ../input_data/DREAM5/EVAL/DREAM5_NetworkInference_Edges_Network${id}.tsv \
                    --synapse-file ../input_data/DREAM5/EVAL/DREAM5_NetworkInference_GoldStandard_Network${id}.tsv \
                    --synapse-file ../input_data/DREAM5/EVAL/Network${id}_AUPR.mat \
                    --synapse-file ../input_data/DREAM5/EVAL/Network${id}_AUROC.mat \
                    --confidence-list $confidence_list >> $network_folder/gs_scores/techniques.txt
        summands+="--weight-file-summand $weight*$confidence_list "
        files+="--file $confidence_list "
    done

    # Media
    python ../geneci/main.py evaluate dream-prediction dream-weight-distribution \
                --challenge D5C4 \
                --network-id $id \
                --synapse-file ../input_data/DREAM5/EVAL/DREAM5_NetworkInference_Edges_Network${id}.tsv \
                --synapse-file ../input_data/DREAM5/EVAL/DREAM5_NetworkInference_GoldStandard_Network${id}.tsv \
                --synapse-file ../input_data/DREAM5/EVAL/Network${id}_AUPR.mat \
                --synapse-file ../input_data/DREAM5/EVAL/Network${id}_AUROC.mat \
                $summands > $network_folder/gs_scores/mean.txt
    
    # Mediana
    python median.py $files --output-file "./temporal_list.csv"
    python ../geneci/main.py evaluate dream-prediction dream-list-of-links \
                --challenge D5C4 \
                --network-id $id \
                --synapse-file ../input_data/DREAM5/EVAL/DREAM5_NetworkInference_Edges_Network${id}.tsv \
                --synapse-file ../input_data/DREAM5/EVAL/DREAM5_NetworkInference_GoldStandard_Network${id}.tsv \
                --synapse-file ../input_data/DREAM5/EVAL/Network${id}_AUPR.mat \
                --synapse-file ../input_data/DREAM5/EVAL/Network${id}_AUROC.mat \
                --confidence-list "./temporal_list.csv" > $network_folder/gs_scores/median.txt
    rm "./temporal_list.csv"
done

## IRMA
for network_folder in ../template/switch-*_exp/
do
    mkdir -p $network_folder/gs_scores
    > $network_folder/gs_scores/techniques.txt

    num_tecs=$(ls $network_folder/lists/*.csv | wc -l)
    weight=$(echo "scale=10; x=1/$num_tecs; if(x<1) print 0; x" | bc)
    summands=""
    files=""

    for confidence_list in $network_folder/lists/*.csv
    do 
        python ../geneci/main.py evaluate generic-prediction generic-list-of-links \
                    --gs-binary-matrix ./../input_data/IRMA/GS/irma_gs.csv \
                    --confidence-list $confidence_list >> $network_folder/gs_scores/techniques.txt
        summands+="--weight-file-summand $weight*$confidence_list "
        files+="--file $confidence_list "
    done

    # Media
    python ../geneci/main.py evaluate generic-prediction generic-weight-distribution \
                --gs-binary-matrix ./../input_data/IRMA/GS/irma_gs.csv \
                $summands > $network_folder/gs_scores/mean.txt
    
    # Mediana
    python median.py $files --output-file "./temporal_list.csv"
    python ../geneci/main.py evaluate generic-prediction generic-list-of-links \
                --gs-binary-matrix ./../input_data/IRMA/GS/irma_gs.csv \
                --confidence-list "./temporal_list.csv" > $network_folder/gs_scores/median.txt
    rm "./temporal_list.csv"
done
