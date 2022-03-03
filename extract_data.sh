dbs=("DREAM4" "SynTReN" "Rogers" "GeneNetWeaver")
types=("EXP" "GS")

for db in ${dbs[@]}
do
    for type in ${types[@]}
    do
        mkdir -p ./expression_data/$db/$type/
    done

    Rscript $db.R
done

