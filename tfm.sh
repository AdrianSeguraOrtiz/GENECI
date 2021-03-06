# 1. Descargamos todas las imágenes necesarias
make pull-images

# 2. Extraemos datos de las redes que queremos estudiar

## Datos de expresión
geneci extract-data expression-data --database DREAM3 --database DREAM4 --database DREAM5 --database IRMA --username TFM-SynapseAccount --password TFM-SynapsePassword

## Gold standards
geneci extract-data gold-standard --database DREAM3 --database DREAM4 --database DREAM5 --database IRMA --username TFM-SynapseAccount --password TFM-SynapsePassword

## Datos de evaluación 
geneci extract-data evaluation-data --database DREAM3 --database DREAM4 --database DREAM5 --username TFM-SynapseAccount --password TFM-SynapsePassword

# 3. Inferimos las redes de regulación génica a partir de todos los datos de expresión empleando todas las técnicas disponibles

for exp_file in input_data/*/EXP/*.csv
do
    geneci infer-network --expression-data $exp_file --technique aracne --technique bc3net --technique c3net --technique clr --technique genie3_rf --technique genie3_gbm --technique genie3_et --technique mrnet --technique mrnetb --technique pcit --technique tigress --technique kboost
done

# 4. Para las redes de tipo benchmark evaluamos la precisión de cada una de las técnicas empleadas

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
        geneci evaluate dream-prediction --challenge D3C4 --network-id ${size}_${id} --synapse-file input_data/DREAM3/EVAL/PDF_InSilicoSize${size}_${id}.mat --synapse-file input_data/DREAM3/EVAL/DREAM3GoldStandard_InSilicoSize${size}_${id}.txt --confidence-list $consensus_list >> $network_folder/gs_scores/techniques.txt
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
        geneci evaluate dream-prediction --challenge D4C2 --network-id ${size}_${id} --synapse-file input_data/DREAM4/EVAL/pdf_size${size}_${id}.mat --confidence-list $confidence_list >> $network_folder/gs_scores/techniques.txt
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
        geneci evaluate dream-prediction --challenge D5C4 --network-id $id --synapse-file input_data/DREAM5/EVAL/DREAM5_NetworkInference_Edges_Network${id}.tsv --synapse-file input_data/DREAM5/EVAL/DREAM5_NetworkInference_GoldStandard_Network${id}.tsv --synapse-file input_data/DREAM5/EVAL/Network${id}_AUPR.mat --synapse-file input_data/DREAM5/EVAL/Network${id}_AUROC.mat --confidence-list $confidence_list >> $network_folder/gs_scores/techniques.txt
    done
done

## IRMA
for network_folder in inferred_networks/switch-*_exp/
do
    mkdir $network_folder/gs_scores
    > $network_folder/gs_scores/techniques.txt

    for confidence_list in $network_folder/lists/*.csv
    do 
        geneci apply-cut --confidence-list $confidence_list --gene-names $network_folder/gene_names.txt --cut-off-criteria MinConfidence --cut-off-value 0.4
        geneci evaluate generic-prediction --inferred-binary-matrix $network_folder/networks/$(basename $confidence_list) --gs-binary-matrix ./input_data/IRMA/GS/irma_gs.csv >> $network_folder/gs_scores/techniques.txt
    done
done

# 5. Optimizamos el ensemble de las listas de confianza resultantes del paso anterior mediante 25 ejecuciones independientes de cada una de ellas

for network_folder in inferred_networks/*/
do
    str=""
    for confidence_list in $network_folder/lists/*.csv
    do 
        str+="--confidence-list $confidence_list "
    done

    for i in {1..25}
    do
        geneci optimize-ensemble $str --gene-names $network_folder/gene_names.txt --population-size 100 --num-evaluations 50000 --output-dir $network_folder/ea_consensus_$i
    done
done

# 6. Representamos las listas de confianza junto con uno de los consensuados obtenidos

for network_folder in inferred_networks/*/
do
    str="--confidence-list $network_folder/ea_consensus_1/final_list.csv "
    for confidence_list in $network_folder/lists/*.csv
    do 
        str+="--confidence-list $confidence_list "
    done
    geneci draw-network $str
done

# 7. Para las redes de tipo benchmark evaluamos la precisión de los ensembles generados 

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
        geneci evaluate dream-prediction --challenge D3C4 --network-id ${size}_${id} --synapse-file input_data/DREAM3/EVAL/PDF_InSilicoSize${size}_${id}.mat --synapse-file input_data/DREAM3/EVAL/DREAM3GoldStandard_InSilicoSize${size}_${id}.txt --confidence-list $consensus_list >> $network_folder/gs_scores/consensus.txt
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
        geneci evaluate dream-prediction --challenge D4C2 --network-id ${size}_${id} --synapse-file input_data/DREAM4/EVAL/pdf_size${size}_${id}.mat --confidence-list $consensus_list >> $network_folder/gs_scores/consensus.txt
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
        geneci evaluate dream-prediction --challenge D5C4 --network-id $id --synapse-file input_data/DREAM5/EVAL/DREAM5_NetworkInference_Edges_Network${id}.tsv --synapse-file input_data/DREAM5/EVAL/DREAM5_NetworkInference_GoldStandard_Network${id}.tsv --synapse-file input_data/DREAM5/EVAL/Network${id}_AUPR.mat --synapse-file input_data/DREAM5/EVAL/Network${id}_AUROC.mat --confidence-list $consensus_list >> $network_folder/gs_scores/consensus.txt
    done
done

## IRMA
for network_folder in inferred_networks/switch-*_exp/
do
    mkdir $network_folder/gs_scores
    > $network_folder/gs_scores/consensus.txt

    for consensus_list in $network_folder/ea_consensus_*/final_list.csv
    do 
        geneci apply-cut --confidence-list $consensus_list --gene-names $network_folder/gene_names.txt --cut-off-criteria MinConfidence --cut-off-value 0.4
        geneci evaluate generic-prediction --inferred-binary-matrix $network_folder/networks/$(basename $consensus_list) --gs-binary-matrix ./input_data/IRMA/GS/irma_gs.csv >> $network_folder/gs_scores/consensus.txt
    done
done

# 8. Para las redes de tipo benchmark creamos los excel con los resultados de precisión

## DREAM3
for network_folder in inferred_networks/*-trajectories_exp/
do
    id=$(echo $(basename $network_folder) | cut -d "-" -f 2)
    size=$(echo $(basename $network_folder) | cut -d "-" -f 1)
    size=${size#"InSilicoSize"}

    name="D3_${size}_${id}"
    file=$network_folder/gs_scores/${name}-gs_table.csv
    echo "$name;;" > $file
    echo "Technique;AUPR;AUROC" >> $file

    tecs=($(grep -Po "(?<=GRN_)[^ ]*(?=.csv)" $network_folder/gs_scores/techniques.txt))
    aupr=($(grep -o "AUPR: 0.[0-9]*" $network_folder/gs_scores/techniques.txt | cut -d " " -f 2))
    auroc=($(grep -o "AUROC: 0.[0-9]*" $network_folder/gs_scores/techniques.txt | cut -d " " -f 2))

    for (( i=0; i<${#tecs[@]}; i++ ))
    do
        echo "${tecs[$i]};${aupr[$i]};${auroc[$i]}" >> $file
    done

    cons_aupr=($(grep -o "AUPR: 0.[0-9]*" $network_folder/gs_scores/consensus.txt | cut -d " " -f 2))
    median_aupr=$(python -c "import sys; import statistics; print(statistics.median([float(i) for i in sys.argv[1:]]))" ${cons_aupr[@]})
    max_aupr=$(python -c "import sys; print(max([float(i) for i in sys.argv[1:]]))" ${cons_aupr[@]})
    cons_auroc=($(grep -o "AUROC: 0.[0-9]*" $network_folder/gs_scores/consensus.txt | cut -d " " -f 2))
    median_auroc=$(python -c "import sys; import statistics; print(statistics.median([float(i) for i in sys.argv[1:]]))" ${cons_auroc[@]})
    max_auroc=$(python -c "import sys; print(max([float(i) for i in sys.argv[1:]]))" ${cons_auroc[@]})
    echo "Median GENECI;$median_aupr;$median_auroc" >> $file
    echo "Best GENECI;$max_aupr;$max_auroc" >> $file
done

## DREAM4
for network_folder in inferred_networks/dream4*_exp/
do
    id=$(echo $(basename $network_folder) | cut -d "_" -f 3)
    id=${id#"0"}
    size=$(echo $(basename $network_folder) | cut -d "_" -f 2)
    size=${size#"0"}

    name="D4_${size}_${id}"
    file=$network_folder/gs_scores/${name}-gs_table.csv
    echo "$name;;" > $file
    echo "Technique;AUPR;AUROC" >> $file

    tecs=($(grep -Po "(?<=GRN_)[^ ]*(?=.csv)" $network_folder/gs_scores/techniques.txt))
    aupr=($(grep -o "AUPR: 0.[0-9]*" $network_folder/gs_scores/techniques.txt | cut -d " " -f 2))
    auroc=($(grep -o "AUROC: 0.[0-9]*" $network_folder/gs_scores/techniques.txt | cut -d " " -f 2))

    for (( i=0; i<${#tecs[@]}; i++ ))
    do
        echo "${tecs[$i]};${aupr[$i]};${auroc[$i]}" >> $file
    done

    cons_aupr=($(grep -o "AUPR: 0.[0-9]*" $network_folder/gs_scores/consensus.txt | cut -d " " -f 2))
    median_aupr=$(python -c "import sys; import statistics; print(statistics.median([float(i) for i in sys.argv[1:]]))" ${cons_aupr[@]})
    max_aupr=$(python -c "import sys; print(max([float(i) for i in sys.argv[1:]]))" ${cons_aupr[@]})
    cons_auroc=($(grep -o "AUROC: 0.[0-9]*" $network_folder/gs_scores/consensus.txt | cut -d " " -f 2))
    median_auroc=$(python -c "import sys; import statistics; print(statistics.median([float(i) for i in sys.argv[1:]]))" ${cons_auroc[@]})
    max_auroc=$(python -c "import sys; print(max([float(i) for i in sys.argv[1:]]))" ${cons_auroc[@]})
    echo "Median GENECI;$median_aupr;$median_auroc" >> $file
    echo "Best GENECI;$max_aupr;$max_auroc" >> $file
done

## DREAM5
for network_folder in inferred_networks/net*_exp/
do
    id=$(basename $network_folder)
    id=${id#"net"}
    id=${id%"_exp"}

    name="D5_${id}"
    file=$network_folder/gs_scores/${name}-gs_table.csv
    echo "$name;;" > $file
    echo "Technique;AUPR;AUROC" >> $file

    tecs=($(grep -Po "(?<=GRN_)[^ ]*(?=.csv)" $network_folder/gs_scores/techniques.txt))
    aupr=($(grep -o "AUPR: 0.[0-9]*" $network_folder/gs_scores/techniques.txt | cut -d " " -f 2))
    auroc=($(grep -o "AUROC: 0.[0-9]*" $network_folder/gs_scores/techniques.txt | cut -d " " -f 2))

    for (( i=0; i<${#tecs[@]}; i++ ))
    do
        echo "${tecs[$i]};${aupr[$i]};${auroc[$i]}" >> $file
    done

    cons_aupr=($(grep -o "AUPR: 0.[0-9]*" $network_folder/gs_scores/consensus.txt | cut -d " " -f 2))
    median_aupr=$(python -c "import sys; import statistics; print(statistics.median([float(i) for i in sys.argv[1:]]))" ${cons_aupr[@]})
    max_aupr=$(python -c "import sys; print(max([float(i) for i in sys.argv[1:]]))" ${cons_aupr[@]})
    cons_auroc=($(grep -o "AUROC: 0.[0-9]*" $network_folder/gs_scores/consensus.txt | cut -d " " -f 2))
    median_auroc=$(python -c "import sys; import statistics; print(statistics.median([float(i) for i in sys.argv[1:]]))" ${cons_auroc[@]})
    max_auroc=$(python -c "import sys; print(max([float(i) for i in sys.argv[1:]]))" ${cons_auroc[@]})
    echo "Median GENECI;$median_aupr;$median_auroc" >> $file
    echo "Best GENECI;$max_aupr;$max_auroc" >> $file
done

## IRMA
for network_folder in inferred_networks/switch-*_exp/
do
    id=$(basename $network_folder)
    id=${id%"_exp"}

    name="IRMA_${id}"
    file=$network_folder/gs_scores/${name}-gs_table.csv
    echo "$name;;" > $file
    echo "Technique;AUPR;AUROC" >> $file

    tecs=($(grep -Po "(?<=GRN_)[^ ]*(?=.csv)" $network_folder/gs_scores/techniques.txt))
    aupr=($(grep -o "AUPR: 0.[0-9]*" $network_folder/gs_scores/techniques.txt | cut -d " " -f 2))
    auroc=($(grep -o "AUROC: 0.[0-9]*" $network_folder/gs_scores/techniques.txt | cut -d " " -f 2))

    for (( i=0; i<${#tecs[@]}; i++ ))
    do
        echo "${tecs[$i]};${aupr[$i]};${auroc[$i]}" >> $file
    done

    cons_aupr=($(grep -o "AUPR: 0.[0-9]*" $network_folder/gs_scores/consensus.txt | cut -d " " -f 2))
    median_aupr=$(python -c "import sys; import statistics; print(statistics.median([float(i) for i in sys.argv[1:]]))" ${cons_aupr[@]})
    max_aupr=$(python -c "import sys; print(max([float(i) for i in sys.argv[1:]]))" ${cons_aupr[@]})
    cons_auroc=($(grep -o "AUROC: 0.[0-9]*" $network_folder/gs_scores/consensus.txt | cut -d " " -f 2))
    median_auroc=$(python -c "import sys; import statistics; print(statistics.median([float(i) for i in sys.argv[1:]]))" ${cons_auroc[@]})
    max_auroc=$(python -c "import sys; print(max([float(i) for i in sys.argv[1:]]))" ${cons_auroc[@]})
    echo "Median GENECI;$median_aupr;$median_auroc" >> $file
    echo "Best GENECI;$max_aupr;$max_auroc" >> $file
done

## 9. Genero las tablas para su exposición en latex
# DREAM 3
python csvs2latex.py --csv-table inferred_networks/InSilicoSize10-Ecoli1-trajectories_exp/gs_scores/D3_10_Ecoli1-gs_table.csv --csv-table inferred_networks/InSilicoSize10-Ecoli2-trajectories_exp/gs_scores/D3_10_Ecoli2-gs_table.csv --csv-table inferred_networks/InSilicoSize10-Yeast1-trajectories_exp/gs_scores/D3_10_Yeast1-gs_table.csv --csv-table inferred_networks/InSilicoSize10-Yeast2-trajectories_exp/gs_scores/D3_10_Yeast2-gs_table.csv --csv-table inferred_networks/InSilicoSize10-Yeast3-trajectories_exp/gs_scores/D3_10_Yeast3-gs_table.csv

python csvs2latex.py --csv-table inferred_networks/InSilicoSize50-Ecoli1-trajectories_exp/gs_scores/D3_50_Ecoli1-gs_table.csv --csv-table inferred_networks/InSilicoSize50-Ecoli2-trajectories_exp/gs_scores/D3_50_Ecoli2-gs_table.csv --csv-table inferred_networks/InSilicoSize50-Yeast1-trajectories_exp/gs_scores/D3_50_Yeast1-gs_table.csv --csv-table inferred_networks/InSilicoSize50-Yeast2-trajectories_exp/gs_scores/D3_50_Yeast2-gs_table.csv --csv-table inferred_networks/InSilicoSize50-Yeast3-trajectories_exp/gs_scores/D3_50_Yeast3-gs_table.csv

python csvs2latex.py --csv-table inferred_networks/InSilicoSize100-Ecoli1-trajectories_exp/gs_scores/D3_100_Ecoli1-gs_table.csv --csv-table inferred_networks/InSilicoSize100-Ecoli2-trajectories_exp/gs_scores/D3_100_Ecoli2-gs_table.csv --csv-table inferred_networks/InSilicoSize100-Yeast1-trajectories_exp/gs_scores/D3_100_Yeast1-gs_table.csv --csv-table inferred_networks/InSilicoSize100-Yeast2-trajectories_exp/gs_scores/D3_100_Yeast2-gs_table.csv --csv-table inferred_networks/InSilicoSize100-Yeast3-trajectories_exp/gs_scores/D3_100_Yeast3-gs_table.csv

# DREAM 4
python csvs2latex.py --csv-table inferred_networks/dream4_010_01_exp/gs_scores/D4_10_1-gs_table.csv --csv-table inferred_networks/dream4_010_02_exp/gs_scores/D4_10_2-gs_table.csv --csv-table inferred_networks/dream4_010_03_exp/gs_scores/D4_10_3-gs_table.csv --csv-table inferred_networks/dream4_010_04_exp/gs_scores/D4_10_4-gs_table.csv --csv-table inferred_networks/dream4_010_05_exp/gs_scores/D4_10_5-gs_table.csv

python csvs2latex.py --csv-table inferred_networks/dream4_100_01_exp/gs_scores/D4_100_1-gs_table.csv --csv-table inferred_networks/dream4_100_02_exp/gs_scores/D4_100_2-gs_table.csv --csv-table inferred_networks/dream4_100_03_exp/gs_scores/D4_100_3-gs_table.csv --csv-table inferred_networks/dream4_100_04_exp/gs_scores/D4_100_4-gs_table.csv --csv-table inferred_networks/dream4_100_05_exp/gs_scores/D4_100_5-gs_table.csv

# DREAM 5
python csvs2latex.py --csv-table inferred_networks/net1_exp/gs_scores/D5_1-gs_table.csv --csv-table inferred_networks/net3_exp/gs_scores/D5_3-gs_table.csv --csv-table inferred_networks/net4_exp/gs_scores/D5_4-gs_table.csv

# IRMA
python csvs2latex.py --csv-table inferred_networks/switch-off_exp/gs_scores/IRMA_switch-off-gs_table.csv --csv-table inferred_networks/switch-on_exp/gs_scores/IRMA_switch-on-gs_table.csv