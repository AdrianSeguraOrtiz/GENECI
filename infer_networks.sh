cut_off_criteria=$1
cut_off_value=$2

parallel_inference() {
	technique=$1
	exp_file=$2
    data_id=$(basename ${exp_file%.*})

    out_id="./inferred_networks/$data_id/lists/GRN_$(basename ${technique%.*})"
    Rscript $technique $exp_file $out_file $out_id
}
export -f parallel_inference

parallel_get_network() {
    links_file=$1
    gene_names_file=$2
    output_file=$3
    cut_off_criteria=$4
    cut_off_value=$5
    java -cp ./EAGRN-JMetal/target/AEGRN-1.0-SNAPSHOT-jar-with-dependencies.jar eagrn.SingleNetworkRunner $links_file $gene_names_file $output_file $cut_off_criteria $cut_off_value
}
export -f parallel_get_network

techniques=$(ls techniques/*.R)
exp_files=$(ls ./expression_data/*/EXP/*.csv)
parallel parallel_inference ::: ${techniques[@]} ::: ${exp_files[@]}

for f in ${exp_files[@]}
do
    data_id=$(basename ${f%.*})
    mkdir -p ../inferred_networks/$data_id/lists
    gene_names=$(cut -f1 -d',' $f | tr -d '"')
    echo ${gene_names[@]} > ../inferred_networks/$data_id/gene_names.txt
done

links_files=$(ls ./inferred_networks/*/lists/*.csv)
gene_names_files=()
output_files=()

for f in ${links_files[@]}
do
    main_folder=$(dirname $(dirname $f))
    filename=$(basename $f)
    gene_names_files+=("$main_folder/gene_names.txt")
    output_files+=("$main_folder/networks/$filename")
done

parallel --link parallel_get_network ::: ${links_files[@]} ::: ${gene_names_files[@]} ::: ${output_files[@]} ::: $cut_off_criteria ::: $cut_off_value

