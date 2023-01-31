for network_folder in ../template/*/
do
    base=$(basename $network_folder)
    if [[ $base =~ [*-trajectories_exp] ]]
    then
        id=$(echo $base | cut -d "-" -f 2)
        size=$(echo $base | cut -d "-" -f 1)
        size=${size#"InSilicoSize"}
        name="D3_${size}_${id}"

    elif [[ $base =~ [dream4*_exp] ]]
    then
        id=$(echo $base | cut -d "_" -f 3)
        id=${id#"0"}
        size=$(echo $base | cut -d "_" -f 2)
        size=${size#"0"}
        name="D4_${size}_${id}"

    elif [[ $base =~ [net*_exp] ]]
    then
        id=${base#"net"}
        id=${id%"_exp"}
        name="D5_${id}"

    elif [[ $base =~ [switch-*_exp] ]]
    then
        id=${base%"_exp"}
        name="IRMA_${id}"
    else
        name=$base
    fi

    file=$network_folder/gs_scores/${name}-techniques_scores.csv
    echo "$name;$name;$name;$name" > $file
    echo "Technique;AUPR;AUROC;Mean" >> $file

    tecs=($(grep -Po "(?<=GRN_)[^ ]*(?=.csv)" $network_folder/gs_scores/techniques.txt))
    aupr=($(grep -o "AUPR: 0.[0-9]*" $network_folder/gs_scores/techniques.txt | cut -d " " -f 2))
    auroc=($(grep -o "AUROC: 0.[0-9]*" $network_folder/gs_scores/techniques.txt | cut -d " " -f 2))

    for (( i=0; i<${#tecs[@]}; i++ ))
    do
        mean=$(echo "scale=10; x=(${aupr[$i]}+${auroc[$i]})/2; if(x<1) print 0; x" | bc)
        echo "${tecs[$i]};${aupr[$i]};${auroc[$i]};$mean" >> $file
    done
done

# Unimos todos los resultados en una misma tabla dividiendo por tamaños
sizes=(0 20 110)
iters=$(( ${#sizes[@]} - 1 ))
chmod a+x paste.pl
for (( i=0; i<=$iters; i++ ))
do 
    tables=()
    for network_folder in ../template/*/
    do
        base=$(basename $network_folder)
        lines=$(wc -l < $network_folder/$base.csv)
        if [ $i == $iters ] && [ $lines -gt ${sizes[$i]} ] || [ $lines -gt ${sizes[$i]} ] && [ $lines -lt ${sizes[$(( $i + 1 ))]} ]
        then
            tables+=$(ls $network_folder/gs_scores/*-techniques_scores.csv)
        fi
    done

    name=${sizes[$i]}
    if [ $i != $iters ]
    then
        name+="-${sizes[$(( $i + 1 ))]}"
    fi

    ./paste.pl $tables > all_networks_${name}_techniques_scores.csv
    echo -e ";$(cat all_networks_${name}_techniques_scores.csv)" > all_networks_${name}_techniques_scores.csv
    cols="1"
    max=$(( ${#tables[@]}*4+2 ))
    for i in `seq 6 4 $max`
    do
        cols+=",$i"
    done

    cut -d ';' -f$cols --complement all_networks_${name}_techniques_scores.csv > tmp.csv && mv -f tmp.csv all_networks_${name}_techniques_scores.csv

    # Creamos la tabla de AUPR para el test estadístico
    max=$(( ${#tables[@]}*3+1 ))
    cols="1"
    for i in `seq 2 3 $max`
    do
        cols+=",$i"
    done
    cut -d ';' -f$cols all_networks_${name}_techniques_scores.csv | awk 'NR != 2' | csvtool transpose -t ';' - | tr ';' ',' > AUPR_${name}_techniques.csv
    sed -i '1s/^/Network/' AUPR_${name}_techniques.csv


    # Creamos la tabla de AUROC para el test estadístico
    max=$(( ${#tables[@]}*3+1 ))
    cols="1"
    for i in `seq 3 3 $max`
    do
        cols+=",$i"
    done
    cut -d ';' -f$cols all_networks_${name}_techniques_scores.csv | awk 'NR != 2' | csvtool transpose -t ';' - | tr ';' ',' > AUROC_${name}_techniques.csv
    sed -i '1s/^/Network/' AUROC_${name}_techniques.csv

    # Creamos una tabla con la media de ambas métricas
    max=$(( ${#tables[@]}*3+1 ))
    cols="1"
    for i in `seq 4 3 $max`
    do
        cols+=",$i"
    done
    cut -d ';' -f$cols all_networks_${name}_techniques_scores.csv | awk 'NR != 2' | csvtool transpose -t ';' - | tr ';' ',' > Mean_${name}_techniques.csv
    sed -i '1s/^/Network/' Mean_${name}_techniques.csv

    # Ejecutamos los tests de Friedman
    cd controlTest && java Friedman.java ../AUPR_${name}_techniques.csv > ../AUPR_${name}_techniques.tex && cd ..
    cd controlTest && java Friedman.java ../AUROC_${name}_techniques.csv > ../AUROC_${name}_techniques.tex && cd ..
    cd controlTest && java Friedman.java ../Mean_${name}_techniques.csv > ../Mean_${name}_techniques.tex && cd ..
done