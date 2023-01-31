sizes=(0 20 110)
iters=$(( ${#sizes[@]} - 1 ))
for (( i=0; i<=$iters; i++ ))
do
    name=${sizes[$i]}
    if [ $i != $iters ]
    then
        name+="-${sizes[$(( $i + 1 ))]}"
    fi

    # Unimos las tablas de las funciones con las de las técnicas
    join -t, -a1 -a2 -e '?' <(sort AUPR_${name}_functions.csv) <(sort AUPR_${name}_techniques.csv) > temp_AUPR.csv
    n=$(grep -n 'Network' temp_AUPR.csv | cut -f1 -d:)
    printf '%s\n' "${n}m0" 'w AUPR_${name}.csv' 'q' | ed -s temp_AUPR.csv
    rm temp_AUPR.csv

    join -t, -a1 -a2 -e '?' <(sort AUROC_${name}_functions.csv) <(sort AUROC_${name}_techniques.csv) > temp_AUROC.csv
    n=$(grep -n 'Network' temp_AUROC.csv | cut -f1 -d:)
    printf '%s\n' "${n}m0" 'w AUROC_${name}.csv' 'q' | ed -s temp_AUROC.csv
    rm temp_AUROC.csv

    join -t, -a1 -a2 -e '?' <(sort Mean_${name}_functions.csv) <(sort Mean_${name}_techniques.csv) > temp_Mean.csv
    n=$(grep -n 'Network' temp_Mean.csv | cut -f1 -d:)
    printf '%s\n' "${n}m0" 'w Mean_${name}.csv' 'q' | ed -s temp_Mean.csv
    rm temp_Mean.csv

    # Ejecutamos los tests de Friedman
    cd controlTest && java Friedman.java ../AUPR_${name}.csv > ../AUPR_${name}.tex && cd ..
    cd controlTest && java Friedman.java ../AUROC_${name}.csv > ../AUROC_${name}.tex && cd ..
    cd controlTest && java Friedman.java ../Mean_${name}.csv > ../Mean_${name}.tex && cd ..

done