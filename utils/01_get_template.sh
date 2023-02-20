# 1. Extraemos datos de las redes que queremos estudiar

## 1.A. Benchmarks
### Datos de expresión
python ../geneci/main.py extract-data expression-data \
            --database DREAM3 --database DREAM4 --database DREAM5 \
            --database IRMA --database SynTReN --database Rogers \
            --database GeneNetWeaver \
            --username TFM-SynapseAccount \
            --password TFM-SynapsePassword \
            --output-dir ../input_data

### Gold standards
python ../geneci/main.py extract-data gold-standard \
            --database DREAM3 --database DREAM4 --database DREAM5 \
            --database IRMA --database SynTReN --database Rogers \
            --database GeneNetWeaver \
            --username TFM-SynapseAccount \
            --password TFM-SynapsePassword \
            --output-dir ../input_data

### Datos de evaluación 
python ../geneci/main.py extract-data evaluation-data \
            --database DREAM3 --database DREAM4 --database DREAM5 \
            --username TFM-SynapseAccount \
            --password TFM-SynapsePassword \
            --output-dir ../input_data

## 1.B. Simulated
### From scratch
sizes=(20 50 100 200)
topologies=("scale-free" "eipo-modular")
perturbations=("knockout" "knockdown" "overexpression")
for size in ${sizes[@]}
do
    for topology in ${topologies[@]}
    do
        for perturbation in ${perturbations[@]}
        do
            python ../geneci/main.py generate-data generate-from-scratch \
                        --topology $topology \
                        --network-size $size \
                        --perturbation $perturbation \
                        --output-dir ../input_data
        done
    done
done

### From real
databases=("TFLink" "TRRUST" "RegulonDB" "RegNetwork" "BioGrid" "GRNdb")
for db in ${databases[@]}
do
    str=$(python ../geneci/main.py generate-data download-real-network --database $db --id . | grep -zo "following: \[.*\]")
    str=${str#"following: ['"}
    str=${str%"']"}
    while IFS="', '" read -ra ids
    do
        for id in ${ids[@]}
        do
            python ../geneci/main.py generate-data download-real-network \
                        --database $db \
                        --id $id \
                        --output-dir ../input_data
        done
    done <<< "$str"
done

for real_network in ../input_data/simulated_based_on_real/RAW/*.tsv
do
    python ../geneci/main.py generate-data generate-from-real-network \
            --real-list-of-links $real_network \
            --perturbation mixed \
            --output-dir ../input_data
done

# 2. Inferimos las redes de regulación génica a partir de todos los datos de expresión empleando 
# todas las técnicas disponibles y copiamos las series temporales a la carpeta de salida

infer_network_from_exp_file () {
    exp_file=$1
    str_threads=$2
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

    # Si la red supera los 250 genes, descartamos (además de los anteriores) PCACMI, PLSNET, INFERELATOR, GENIE3_RF, GENIE3_ET y GRNBOOST2
    if [ $lines -gt 250 ]
    then
        delete=("PCACMI" "PLSNET" "INFERELATOR" "GENIE3_RF" "GENIE3_ET" "GRNBOOST2")
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

    python ../geneci/main.py infer-network $str_tecs --expression-data $exp_file --output-dir ../template --str-threads $str_threads
    cp $exp_file ../template/$(basename $exp_file .csv)/
}
export -f infer_network_from_exp_file

## GNU parallel
exp_files=($(ls ../input_data/*/EXP/*.csv))
n_cores=$(nproc --all)
n_files_parallel=$(echo "scale=0; x=$n_cores/32; if(x<1) x=1; x" | bc)
n_cores_each_file=$(( $n_cores/$n_files_parallel ))
n_iters=$(echo "scale=0; (${#exp_files[@]} + $n_files_parallel - 1)/$n_files_parallel" | bc)
for ((x=0; x<$n_iters; x++))
do
    parallel_files=(${exp_files[@]:$(( $x * $n_files_parallel )):$n_files_parallel})
    str_threads_list=($(echo $(seq 0 $(( $n_cores - 1 ))) | xargs -n $n_cores_each_file | tr ' ' ,))
    parallel --link infer_network_from_exp_file ::: ${parallel_files[@]} ::: ${str_threads_list[@]}
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
