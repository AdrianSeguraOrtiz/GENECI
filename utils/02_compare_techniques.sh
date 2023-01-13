## DREAM3
for network_folder in ../template/*-trajectories_exp/
do
    id=$(echo $(basename $network_folder) | cut -d "-" -f 2)
    size=$(echo $(basename $network_folder) | cut -d "-" -f 1)
    size=${size#"InSilicoSize"}

    name="D3_${size}_${id}"
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

## DREAM4
for network_folder in ../template/dream4*_exp/
do
    id=$(echo $(basename $network_folder) | cut -d "_" -f 3)
    id=${id#"0"}
    size=$(echo $(basename $network_folder) | cut -d "_" -f 2)
    size=${size#"0"}

    name="D4_${size}_${id}"
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

## IRMA
for network_folder in ../template/switch-*_exp/
do
    id=$(basename $network_folder)
    id=${id%"_exp"}

    name="IRMA_${id}"
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

# Unimos todos los resultados en una misma tabla
chmod a+x paste.pl
./paste.pl ../template/*/gs_scores/*-techniques_scores.csv > all_networks_techniques_scores.csv

echo -e ";$(cat all_networks_techniques_scores.csv)" > all_networks_techniques_scores.csv
cols="1"
networks=($(ls ../template/))
max=$(( ${#networks[@]}*4+2 ))
for i in `seq 6 4 $max`
do
    cols+=",$i"
done

cut -d ';' -f$cols --complement all_networks_techniques_scores.csv > tmp.csv && mv -f tmp.csv all_networks_techniques_scores.csv

# Creamos la tabla de AUPR para el test estadístico
max=$(( ${#networks[@]}*3+1 ))
cols="1"
for i in `seq 2 3 $max`
do
    cols+=",$i"
done
cut -d ';' -f$cols all_networks_techniques_scores.csv | awk 'NR != 2' | csvtool transpose -t ';' - | tr ';' ',' > AUPR_techniques.csv
sed -i '1s/^/Network/' AUPR_techniques.csv


# Creamos la tabla de AUROC para el test estadístico
max=$(( ${#networks[@]}*3+1 ))
cols="1"
for i in `seq 3 3 $max`
do
    cols+=",$i"
done
cut -d ';' -f$cols all_networks_techniques_scores.csv | awk 'NR != 2' | csvtool transpose -t ';' - | tr ';' ',' > AUROC_techniques.csv
sed -i '1s/^/Network/' AUROC_techniques.csv

# Creamos una tabla con la media de ambas métricas
max=$(( ${#networks[@]}*3+1 ))
cols="1"
for i in `seq 4 3 $max`
do
    cols+=",$i"
done
cut -d ';' -f$cols all_networks_techniques_scores.csv | awk 'NR != 2' | csvtool transpose -t ';' - | tr ';' ',' > Mean_techniques.csv
sed -i '1s/^/Network/' Mean_techniques.csv

# Ejecutamos los tests de Friedman
cd controlTest && java Friedman.java ../AUPR_techniques.csv > ../AUPR_techniques.tex && cd ..
cd controlTest && java Friedman.java ../AUROC_techniques.csv > ../AUROC_techniques.tex && cd ..
cd controlTest && java Friedman.java ../Mean_techniques.csv > ../Mean_techniques.tex && cd ..