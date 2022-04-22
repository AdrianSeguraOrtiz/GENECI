# 1. Actualizamos jar del proyecto JMetal por si acaso
cd EAGRN-JMetal
mvn clean compile assembly:single
cd ..

# 2. Generamos todas las imágenes necesarias

## Extracción de datos
docker build -t eagrn-inference/extract_data/dream3 -f components/extract_data/DREAM3/Dockerfile .
docker build -t eagrn-inference/extract_data/dream4/expgs -f components/extract_data/DREAM4/EXPGS/Dockerfile .
docker build -t eagrn-inference/extract_data/dream4/eval -f components/extract_data/DREAM4/EVAL/Dockerfile .
docker build -t eagrn-inference/extract_data/dream5 -f components/extract_data/DREAM5/Dockerfile .
docker build -t eagrn-inference/extract_data/grndata -f components/extract_data/GRNDATA/Dockerfile .
docker build -t eagrn-inference/extract_data/irma -f components/extract_data/IRMA/Dockerfile .

## Inferencia de redes
docker build -t eagrn-inference/infer_network/aracne -f components/infer_network/ARACNE/Dockerfile .
docker build -t eagrn-inference/infer_network/bc3net -f components/infer_network/BC3NET/Dockerfile .
docker build -t eagrn-inference/infer_network/c3net -f components/infer_network/C3NET/Dockerfile .
docker build -t eagrn-inference/infer_network/clr -f components/infer_network/CLR/Dockerfile .
docker build -t eagrn-inference/infer_network/genie3 -f components/infer_network/GENIE3/Dockerfile .
docker build -t eagrn-inference/infer_network/mrnet -f components/infer_network/MRNET/Dockerfile .
docker build -t eagrn-inference/infer_network/mrnetb -f components/infer_network/MRNETB/Dockerfile .
docker build -t eagrn-inference/infer_network/pcit -f components/infer_network/PCIT/Dockerfile .
docker build -t eagrn-inference/infer_network/tigress -f components/infer_network/TIGRESS/Dockerfile .
docker build -t eagrn-inference/infer_network/kboost -f components/infer_network/KBOOST/Dockerfile .

## Optimización de ensemble
docker build -t eagrn-inference/optimize_ensemble -f components/optimize_ensemble/Dockerfile .

## Aplicación de criterio de corte (lista de confianzas -> red binaria)
docker build -t eagrn-inference/apply_cut -f components/apply_cut/Dockerfile .

## Evaluación de redes inferidas correspondientes a los restos de DREAM
docker build -t eagrn-inference/evaluate/dream_prediction -f components/evaluate/dream_prediction/Dockerfile .

# 3. Extraemos datos de las redes que queremos estudiar

## Datos de expresión
python EAGRN-Inference.py extract-data expression-data --database DREAM3 --database DREAM4 --database DREAM5 --database IRMA --username TFM-SynapseAccount --password TFM-SynapsePassword

## Gold standards
python EAGRN-Inference.py extract-data gold-standard --database DREAM3 --database DREAM4 --database DREAM5 --database IRMA --username TFM-SynapseAccount --password TFM-SynapsePassword

## Datos de evaluación 
python EAGRN-Inference.py extract-data evaluation-data --database DREAM3 --database DREAM4 --database DREAM5 --username TFM-SynapseAccount --password TFM-SynapsePassword

# 4. Inferimos las redes de regulación génica a partir de todos los datos de expresión empleando todas las técnicas disponibles

for exp_file in input_data/*/EXP/*.csv
do
    python EAGRN-Inference.py infer-network --expression-data $exp_file --technique aracne --technique bc3net --technique c3net --technique clr --technique genie3_rf --technique genie3_gbm --technique genie3_et --technique mrnet --technique mrnetb --technique pcit --technique tigress --technique kboost
done

# 5. Para las redes procedentes de DREAM evaluamos la precisión de cada una de las técnicas empleadas

## DREAM3
for network_folder in inferred_networks/*-trajectories_exp/
do
    mkdir $network_folder/gs_scores
    > $network_folder/gs_scores/techniques.txt

    id=$(echo $(basename $network_folder) | cut -d "-" -f 2)
    size=$(echo $(basename $network_folder) | cut -d "-" -f 1)
    size=${size#"InSilicoSize"}

    for consensus_list in $network_folder/lists/*.csv
    do 
        python EAGRN-Inference.py evaluate dream-prediction --challenge D3C4 --network-id ${size}_${id} --synapse-file input_data/DREAM3/EVAL/PDF_InSilicoSize${size}_${id}.mat --synapse-file input_data/DREAM3/EVAL/DREAM3GoldStandard_InSilicoSize${size}_${id}.txt --confidence-list $consensus_list >> $network_folder/gs_scores/techniques.txt
    done
done

## DREAM4
for network_folder in inferred_networks/dream4*_exp/
do
    mkdir $network_folder/gs_scores
    > $network_folder/gs_scores/techniques.txt

    id=$(echo $(basename $network_folder) | cut -d "_" -f 3)
    id=${id#"0"}
    size=$(echo $(basename $network_folder) | cut -d "_" -f 2)
    size=${size#"0"}

    for confidence_list in $network_folder/lists/*.csv
    do 
        python EAGRN-Inference.py evaluate dream-prediction --challenge D4C2 --network-id ${size}_${id} --synapse-file input_data/DREAM4/EVAL/pdf_size${size}_${id}.mat --confidence-list $confidence_list >> $network_folder/gs_scores/techniques.txt
    done
done

## DREAM5
for network_folder in inferred_networks/net*_exp/
do
    mkdir $network_folder/gs_scores
    > $network_folder/gs_scores/techniques.txt

    id=$(basename $network_folder)
    id=${id#"net"}
    id=${id%"_exp"}

    for confidence_list in $network_folder/lists/*.csv
    do 
        python EAGRN-Inference.py evaluate dream-prediction --challenge D5C4 --network-id $id --synapse-file input_data/DREAM5/EVAL/DREAM5_NetworkInference_Edges_Network${id}.tsv --synapse-file input_data/DREAM5/EVAL/DREAM5_NetworkInference_GoldStandard_Network${id}.tsv --synapse-file input_data/DREAM5/EVAL/Network${id}_AUPR.mat --synapse-file input_data/DREAM5/EVAL/Network${id}_AUROC.mat --confidence-list $confidence_list >> $network_folder/gs_scores/techniques.txt
    done
done

# 6. Optimizamos el ensemble de las listas de confianza resultantes del paso anterior mediante 25 ejecuciones independientes de cada una de ellas

for network_folder in inferred_networks/*/
do
    str=""
    for confidence_list in $network_folder/lists/*.csv
    do 
        str+="--confidence-list $confidence_list "
    done

    for i in {1..25}
    do
        python EAGRN-Inference.py optimize-ensemble $str --gene-names $network_folder/gene_names.txt --population-size 100 --num-evaluations 100000 --output-dir $network_folder/ea_consensus_$i
    done
done

# 7. Para las redes procedentes de DREAM evaluamos la precisión de los ensembles generados 

## DREAM3
for network_folder in inferred_networks/*-trajectories_exp/
do
    mkdir $network_folder/gs_scores
    > $network_folder/gs_scores/consensus.txt

    id=$(echo $(basename $network_folder) | cut -d "-" -f 2)
    size=$(echo $(basename $network_folder) | cut -d "-" -f 1)
    size=${size#"InSilicoSize"}

    for consensus_list in $network_folder/ea_consensus_*/final_list.csv
    do 
        python EAGRN-Inference.py evaluate dream-prediction --challenge D3C4 --network-id ${size}_${id} --synapse-file input_data/DREAM3/EVAL/PDF_InSilicoSize${size}_${id}.mat --synapse-file input_data/DREAM3/EVAL/DREAM3GoldStandard_InSilicoSize${size}_${id}.txt --confidence-list $consensus_list >> $network_folder/gs_scores/consensus.txt
    done
done

## DREAM4
for network_folder in inferred_networks/dream4*_exp/
do
    mkdir $network_folder/gs_scores
    > $network_folder/gs_scores/consensus.txt

    id=$(echo $(basename $network_folder) | cut -d "_" -f 3)
    id=${id#"0"}
    size=$(echo $(basename $network_folder) | cut -d "_" -f 2)
    size=${size#"0"}

    for consensus_list in $network_folder/ea_consensus_*/final_list.csv
    do 
        python EAGRN-Inference.py evaluate dream-prediction --challenge D4C2 --network-id ${size}_${id} --synapse-file input_data/DREAM4/EVAL/pdf_size${size}_${id}.mat --confidence-list $consensus_list >> $network_folder/gs_scores/consensus.txt
    done
done

## DREAM5
for network_folder in inferred_networks/net*_exp/
do
    mkdir $network_folder/gs_scores
    > $network_folder/gs_scores/consensus.txt

    id=$(basename $network_folder)
    id=${id#"net"}
    id=${id%"_exp"}

    for consensus_list in $network_folder/ea_consensus_*/final_list.csv
    do 
        python EAGRN-Inference.py evaluate dream-prediction --challenge D5C4 --network-id $id --synapse-file input_data/DREAM5/EVAL/DREAM5_NetworkInference_Edges_Network${id}.tsv --synapse-file input_data/DREAM5/EVAL/DREAM5_NetworkInference_GoldStandard_Network${id}.tsv --synapse-file input_data/DREAM5/EVAL/Network${id}_AUPR.mat --synapse-file input_data/DREAM5/EVAL/Network${id}_AUROC.mat --confidence-list $consensus_list >> $network_folder/gs_scores/consensus.txt
    done
done