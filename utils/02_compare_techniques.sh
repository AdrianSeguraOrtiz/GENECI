# 1. Para cada red génica inferida, creamos una tabla resumen con los resultados de todas las técnicas.
# En cada fila se recoge: Tecnica, AUPR, AUROC, Media((AUPR+AUROC) / 2) y Tiempo de ejecución.

for network_folder in ../template/*/
do
    base=$(basename $network_folder)
    if [[ $base =~ ^.*-trajectories_exp ]]
    then
        id=$(echo $base | cut -d "-" -f 2)
        size=$(echo $base | cut -d "-" -f 1)
        size=${size#"InSilicoSize"}
        name="D3_${size}_${id}"

    elif [[ $base =~ ^dream4.*_exp ]]
    then
        id=$(echo $base | cut -d "_" -f 3)
        id=${id#"0"}
        size=$(echo $base | cut -d "_" -f 2)
        size=${size#"0"}
        name="D4_${size}_${id}"

    elif [[ $base =~ ^net.*_exp ]]
    then
        id=${base#"net"}
        id=${id%"_exp"}
        name="D5_${id}"

    elif [[ $base =~ ^switch-.*_exp ]]
    then
        id=${base%"_exp"}
        name="IRMA_${id}"
    else
        name=$base
    fi

    file=$network_folder/measurements/${name}-techniques_scores.csv
    echo "$name;$name;$name;$name;$name" > $file
    echo "Technique;AUPR;AUROC;Mean;Time" >> $file

    tecs=($(awk '/GRN_/,/.csv/ {printf "%s", $0}' $network_folder/measurements/techniques.txt | sed -r 's/\.\.\// /g' | grep -Po "(?<=GRN_)[^ ]*(?=.csv)"))
    aupr=($(grep -o "AUPR: 1\|AUPR: 0.[0-9]*" $network_folder/measurements/techniques.txt | cut -d " " -f 2))
    auroc=($(grep -o "AUROC: 1\|AUPR: 0.[0-9]*" $network_folder/measurements/techniques.txt | cut -d " " -f 2))
    times=()
    for tec in ${tecs[@]}
    do
        times+=("$(grep -P " $tec:\t[.]*" $network_folder/measurements/techniques_times.txt | cut -d $'\t' -f 3)")
    done

    for (( i=0; i<${#tecs[@]}; i++ ))
    do
        mean=$(echo "scale=10; x=(${aupr[$i]}+${auroc[$i]})/2; if(x<1) print 0; x" | bc)
        echo "${tecs[$i]};${aupr[$i]};${auroc[$i]};$mean;${times[$i]}" >> $file
    done
done

# 2. Para cada grupo de tamaños unimos sus tablas en una sola. De esta forma compararemos 
# el rendimiento de las técnicas para diferentes tamaños de redes, permitiendo la ausencia 
# de ciertas técnicas en algunos grupos. Para cuantificar su rendimiento usamos el ranking 
# estadístico de Friedman sobre cada uno de los scores: AUPR, AUROC, Media((AUPR+AUROC) / 2)

sizes=(0 25 110 250 2000)
iters=$(( ${#sizes[@]} - 1 ))
chmod a+x paste.pl
mkdir -p techniques_comparison
for (( i=0; i<=$iters; i++ ))
do 
    tables=()
    for network_folder in ../template/*/
    do
        base=$(basename $network_folder)
        lines=$(wc -l < $network_folder/$base.csv)
        if [ $i == $iters ] && [ $lines -gt ${sizes[$i]} ]
        then
            tables+=($(ls $network_folder/measurements/*-techniques_scores.csv))
        elif [ $lines -gt ${sizes[$i]} ] && [ $lines -lt ${sizes[$(( $i + 1 ))]} ]
        then
            tables+=($(ls $network_folder/measurements/*-techniques_scores.csv))
        fi
    done

    name=${sizes[$i]}
    if [ $i != $iters ]
    then
        name+="-${sizes[$(( $i + 1 ))]}"
    fi

    ./paste.pl ${tables[@]} > techniques_comparison/all_networks_${name}_techniques_scores.csv
    cols="1"
    max=$(( ${#tables[@]}*5+2 ))
    for j in `seq 7 5 $max`
    do
        cols+=",$j"
    done
    cut -d ';' -f$cols --complement techniques_comparison/all_networks_${name}_techniques_scores.csv > tmp.csv && mv -f tmp.csv techniques_comparison/all_networks_${name}_techniques_scores.csv
    max=$(( ${#tables[@]}*4+2 ))

    # Creamos la tabla de AUPR para el test estadístico
    cols="1"
    for j in `seq 2 4 $max`
    do
        cols+=",$j"
    done
    cut -d ';' -f$cols techniques_comparison/all_networks_${name}_techniques_scores.csv | awk 'NR != 2' | csvtool transpose -t ';' - | tr ';' ',' > techniques_comparison/AUPR_${name}_techniques.csv

    # Creamos la tabla de AUROC para el test estadístico
    cols="1"
    for j in `seq 3 4 $max`
    do
        cols+=",$j"
    done
    cut -d ';' -f$cols techniques_comparison/all_networks_${name}_techniques_scores.csv | awk 'NR != 2' | csvtool transpose -t ';' - | tr ';' ',' > techniques_comparison/AUROC_${name}_techniques.csv

    # Creamos una tabla con la media de ambas métricas
    cols="1"
    for j in `seq 4 4 $max`
    do
        cols+=",$j"
    done
    cut -d ';' -f$cols techniques_comparison/all_networks_${name}_techniques_scores.csv | awk 'NR != 2' | csvtool transpose -t ';' - | tr ';' ',' > techniques_comparison/Mean_${name}_techniques.csv

    # Ejecutamos los tests de Friedman
    cd controlTest && java Friedman ../techniques_comparison/AUPR_${name}_techniques.csv > ../techniques_comparison/AUPR_${name}_techniques.tex && cd ..
    cd controlTest && java Friedman ../techniques_comparison/AUROC_${name}_techniques.csv > ../techniques_comparison/AUROC_${name}_techniques.tex && cd ..
    cd controlTest && java Friedman ../techniques_comparison/Mean_${name}_techniques.csv > ../techniques_comparison/Mean_${name}_techniques.tex && cd ..

    # Creamos tabla de tiempos
    cols="1"
    for j in `seq 5 4 $max`
    do
        cols+=",$j"
    done
    cut -d ';' -f$cols techniques_comparison/all_networks_${name}_techniques_scores.csv | awk 'NR != 2' | csvtool transpose -t ';' - | tr ';' ',' > techniques_comparison/Time_${name}_techniques.csv
done