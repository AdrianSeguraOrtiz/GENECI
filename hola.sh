for network_folder in inferred_networks/*/
do
    str=""
    for confidence_list in $network_folder/lists/*.csv
    do 
        str+="--confidence-list $confidence_list "
    done

    for i in {1..25}
    do
        python EAGRN-Inference.py optimize-ensemble $str --gene-names $network_folder/gene_names.txt --population-size 100 --num-evaluations 100000 --output-dir $network_folder/ea_consensus_$i --f1-weight 0.95 --f2-weight 0.05
    done
done