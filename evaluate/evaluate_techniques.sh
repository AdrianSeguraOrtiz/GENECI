parallel_evaluate() {
	input_file=$1
	gs_file=$2
    Rscript evaluate/evaluate.R $input_file $gs_file
}
export -f parallel_evaluate

inf_net_files=()
gs_files=()

for f in inferred_networks/*/networks/*.csv
do
    inf_net_files+=("$f")
    id=$(basename $(dirname $(dirname $f)))
    id=${id%_exp}
    gs_file=$(find expression_data/*/GS/${id}_gs.csv)
    gs_files+=("$gs_file")
done

parallel --link parallel_evaluate ::: ${inf_net_files[@]} ::: ${gs_files[@]}