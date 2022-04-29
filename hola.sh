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

for network_folder in inferred_networks/net*_exp/
do
    id=$(basename $network_folder)
    id=${id#"net"}
    id=${id%"_exp"}

    name="D5_${id}"
    file=$network_folder/gs_scores/${name}-gs_table.csv
    echo "$name;;" > $file
    echo "Technique;AUPR;AUROC" >> $file

    tecs=($(grep -Po "(?<=GRN_).*(?=.csv)" $network_folder/gs_scores/techniques.txt))
    aupr=($(grep -o "AUPR: 0.[0-9]*" $network_folder/gs_scores/techniques.txt | cut -d " " -f 2))
    auroc=($(grep -o "AUROC: 0.[0-9]*" $network_folder/gs_scores/techniques.txt | cut -d " " -f 2))

    for (( i=0; i<${#tecs[@]}; i++ ))
    do
        echo "${tecs[$i]};${aupr[$i]};${auroc[$i]}" >> $file
    done

    cons_aupr=($(grep -o "AUPR: 0.[0-9]*" $network_folder/gs_scores/consensus.txt | cut -d " " -f 2))
    median_aupr=$(python -c "import sys; import statistics; print(statistics.median([float(i) for i in sys.argv[1:]]))" ${cons_aupr[@]})
    cons_auroc=($(grep -o "AUROC: 0.[0-9]*" $network_folder/gs_scores/consensus.txt | cut -d " " -f 2))
    median_auroc=$(python -c "import sys; import statistics; print(statistics.median([float(i) for i in sys.argv[1:]]))" ${cons_auroc[@]})
    echo "Median Consensus;$median_aupr;$median_auroc" >> $file
done