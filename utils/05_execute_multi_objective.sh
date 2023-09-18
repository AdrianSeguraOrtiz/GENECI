source ../.venv/bin/activate

# Ordenamos las redes por tamaño de menor a mayor
sizes=()
for network_folder in ../inferred_networks/*/
do
    filename=$(basename $network_folder)
    exp_file="$network_folder/$filename.csv"
    lines=$(wc -l < $exp_file)
    sizes+=($lines)
done
sorted_sizes=($(printf '%s\n' "${sizes[@]}" | sort -nu))

sorted_networks=()
for size in ${sorted_sizes[@]}
do
    for network_folder in ../inferred_networks/*/
    do
        filename=$(basename $network_folder)
        exp_file="$network_folder/$filename.csv"
        lines=$(wc -l < $exp_file)
        if [ $lines == $size ]
        then
            sorted_networks+=($network_folder)
        fi
    done
done

echo ${sorted_networks[@]}

# Para cada red ejecutamos GENECI en modo multi-objetivo
opt_ensemble_multi_obj() {
    nf=$1

    if [ -d "$nf/ea_consensus_mo_q-dd-m" ]; then
        return 1
    fi

    str=""
    for confidence_list in $nf/lists/*.csv
    do 
        str+="--confidence-list $confidence_list "
    done

    functions=('quality' 'degreedistribution' 'motifs')
    str_func=""
    for func in ${functions[@]}
    do
        str_func+="--function $func "
    done

    { time python ../geneci/main.py optimize-ensemble $str $str_func --gene-names $nf/gene_names.txt \--time-series $nf/$(basename $nf).csv \
                                                    --crossover-probability 0.9 --num-parents 4 --mutation-probability 0.05 --mutation-strength 0.1 \
                                                    --population-size 300 --num-evaluations 250000 --algorithm NSGAII \
                                                    --plot-fitness-evolution --plot-pareto-front --plot-parallel-coordinates \
                                                    --threads 50 --output-dir $nf/ea_consensus_mo_q-dd-m ; } 2>> $nf/measurements/multi-objective_times.txt
    echo "^ q-dd-m" >> $nf/measurements/multi-objective_times.txt
}
export -f opt_ensemble_multi_obj
parallel --jobs 1 opt_ensemble_multi_obj ::: ${sorted_networks[@]}

# Evaluamos los frentes de pareto generados
pareto_eval() {
    nf=$1

    mkdir -p $nf/measurements

    base=$(basename $nf)
    if [[ $base =~ ^.*-trajectories_exp ]]
    then
        dream=true
        id=$(echo $base | cut -d "-" -f 2)
        size=$(echo $base | cut -d "-" -f 1)
        size=${size#"InSilicoSize"}

        challenge="D3C4"
        network_id="${size}_${id}"
        eval_files_str="--synapse-file ../input_data/DREAM3/EVAL/PDF_InSilicoSize${size}_${id}.mat --synapse-file ../input_data/DREAM3/EVAL/DREAM3GoldStandard_InSilicoSize${size}_${id}.txt"

    elif [[ $base =~ ^dream4.*_exp ]]
    then
        dream=true
        id=$(echo $base | cut -d "_" -f 3)
        id=${id#"0"}
        size=$(echo $base | cut -d "_" -f 2)
        size=${size#"0"}

        challenge="D4C2"
        network_id="${size}_${id}"
        eval_files_str="--synapse-file ../input_data/DREAM4/EVAL/pdf_size${size}_${id}.mat"

    elif [[ $base =~ ^net.*_exp ]]
    then
        dream=true
        id=${base#"net"}
        id=${id%"_exp"}

        challenge="D5C4"
        network_id="$id"
        eval_files_str="--synapse-file ../input_data/DREAM5/EVAL/DREAM5_NetworkInference_Edges_Network${id}.tsv --synapse-file ../input_data/DREAM5/EVAL/DREAM5_NetworkInference_GoldStandard_Network${id}.tsv --synapse-file ../input_data/DREAM5/EVAL/Network${id}_AUPR.mat --synapse-file ../input_data/DREAM5/EVAL/Network${id}_AUROC.mat"

    elif [[ $base =~ ^switch-.*_exp ]]
    then
        dream=false
        gs="../input_data/IRMA/GS/irma_gs.csv"
    else
        dream=false
        name=${base%"_exp"}
        gs=$(ls ../input_data/*/GS/${name}_gs.csv)
    fi

    if [ "$dream" = true ]
    then
        tag="dream"
        flags="--challenge $challenge --network-id $network_id $eval_files_str"
    else
        tag="generic"
        flags="--gs-binary-matrix $gs"
    fi

    python ../geneci/main.py evaluate ${tag}-prediction ${tag}-pareto-front $flags \
                --weights-file $nf/ea_consensus_mo_q-dd-m/VAR.csv \
                --fitness-file $nf/ea_consensus_mo_q-dd-m/FUN.csv \
                --confidence-folder $nf/lists \
                --output-dir $nf/measurements
}
export -f pareto_eval
parallel --jobs 10 pareto_eval ::: ${sorted_networks[@]}

# Juntamos los valores de precisión de las técnicas con los de geneci
for network_folder in ${sorted_networks[@]}
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

    python join_scores.py --tecs-file $network_folder/measurements/$name-techniques_scores.csv \
                                --geneci-file $network_folder/measurements/evaluated_front.csv \
                                --mean-file $network_folder/measurements/mean.txt \
                                --median-file $network_folder/measurements/median.txt \
                                --output-file $network_folder/measurements/scores.csv

    sed -i "1i $name;$name;$name;$name" $network_folder/measurements/scores.csv
done

# Para cada grupo de tamaños unimos sus tablas en una sola. 
# De esta forma compararemos el rendimiento de GENECI para 
# diferentes tamaños de redes. Para cuantificar su rendimiento usamos el ranking 
# estadístico de Friedman sobre cada uno de los scores: AUPR, AUROC, Media((AUPR+AUROC) / 2)

sizes=(0 25 110 250 2000)
iters=$(( ${#sizes[@]} - 1 ))
chmod a+x paste.pl
mkdir -p final_comparison
for (( i=0; i<=$iters; i++ ))
do 
    tables=()
    for network_folder in ../inferred_networks/*/
    do
        base=$(basename $network_folder)
        lines=$(wc -l < $network_folder/$base.csv)
        if [ $i == $iters ] && [ $lines -gt ${sizes[$i]} ]
        then
            tables+=($network_folder/measurements/scores.csv)
        elif [ $lines -gt ${sizes[$i]} ] && [ $lines -lt ${sizes[$(( $i + 1 ))]} ]
        then
            tables+=($network_folder/measurements/scores.csv)
        fi
    done

    name=${sizes[$i]}
    if [ $i != $iters ]
    then
        name+="-${sizes[$(( $i + 1 ))]}"
    fi

    ./paste.pl ${tables[@]} > final_comparison/all_networks_${name}_final_scores.csv
    cols="1"
    max=$(( ${#tables[@]}*4+2 ))
    for j in `seq 6 4 $max`
    do
        cols+=",$j"
    done
    cut -d ';' -f$cols --complement final_comparison/all_networks_${name}_final_scores.csv > tmp.csv && mv -f tmp.csv final_comparison/all_networks_${name}_final_scores.csv
    max=$(( ${#tables[@]}*3+1 ))

    # Eliminar mean y median
    pattern1="^MEDIAN;"
    pattern2="^MEAN;"
    sed -i '/\('"$pattern1"'\|'"$pattern2"'\)/d' "final_comparison/all_networks_${name}_final_scores.csv"

    # Creamos la tabla de AUPR para el test estadístico
    cols="1"
    for j in `seq 2 3 $max`
    do
        cols+=",$j"
    done
    cut -d ';' -f$cols final_comparison/all_networks_${name}_final_scores.csv | awk 'NR != 2' | csvtool transpose -t ';' - | tr ';' ',' > final_comparison/AUPR_${name}_final.csv

    # Creamos la tabla de AUROC para el test estadístico
    cols="1"
    for j in `seq 3 3 $max`
    do
        cols+=",$j"
    done
    cut -d ';' -f$cols final_comparison/all_networks_${name}_final_scores.csv | awk 'NR != 2' | csvtool transpose -t ';' - | tr ';' ',' > final_comparison/AUROC_${name}_final.csv

    # Creamos una tabla con la media de ambas métricas
    cols="1"
    for j in `seq 4 3 $max`
    do
        cols+=",$j"
    done
    cut -d ';' -f$cols final_comparison/all_networks_${name}_final_scores.csv | awk 'NR != 2' | csvtool transpose -t ';' - | tr ';' ',' > final_comparison/Mean_${name}_final.csv

    # Ejecutamos los tests de Friedman
    cd controlTest && java Friedman ../final_comparison/AUPR_${name}_final.csv > ../final_comparison/AUPR_${name}_final.tex && cd ..
    cd controlTest && java Friedman ../final_comparison/AUROC_${name}_final.csv > ../final_comparison/AUROC_${name}_final.tex && cd ..
    cd controlTest && java Friedman ../final_comparison/Mean_${name}_final.csv > ../final_comparison/Mean_${name}_final.tex && cd ..
done

# Makes graphics
nets=(
# 0-25:
"IRMA-off:switch-off_exp;IRMA-on:switch-on_exp;D4_10_1:dream4_010_01_exp;D4_10_2:dream4_010_02_exp;D4_10_3:dream4_010_03_exp;D4_10_4:dream4_010_04_exp;D4_10_5:dream4_010_05_exp;D3_10_E1:InSilicoSize10-Ecoli1-trajectories_exp;D3_10_E2:InSilicoSize10-Ecoli2-trajectories_exp;D3_10_Y1:InSilicoSize10-Yeast1-trajectories_exp;D3_10_Y2:InSilicoSize10-Yeast2-trajectories_exp;D3_10_Y3:InSilicoSize10-Yeast3-trajectories_exp"
"BG-SV40-M:sim_BioGrid_Simian_Virus_40_mixed_exp;BG-SPATC-M:sim_BioGrid_Streptococcus_pneumoniae_ATCCBAA255_mixed_exp;BG-BS168-M:sim_BioGrid_Bacillus_subtilis_168_mixed_exp;TFL-RN-M:sim_TFLink_Rattus_norvegicus_mixed_exp;BG-VV-M:sim_BioGrid_Vaccinia_Virus_mixed_exp;BG-SLP-M:sim_BioGrid_Strongylocentrotus_purpuratus_mixed_exp;BG-CR-M:sim_BioGrid_Chlamydomonas_reinhardtii_mixed_exp;BG-SIV-M:sim_BioGrid_Simian_Immunodeficiency_Virus_mixed_exp;FS-EM20-KD:sim_eipo-modular_size-20_knockdown_exp;FS-EM20-KO:sim_eipo-modular_size-20_knockout_exp;FS-EM20-O:sim_eipo-modular_size-20_overexpression_exp;FS-SF20-KD:sim_scale-free_size-20_knockdown_exp;FS-SF20-KO:sim_scale-free_size-20_knockout_exp;FS-SF20-O:sim_scale-free_size-20_overexpression_exp;BG-ZM-M:sim_BioGrid_Zea_mays_mixed_exp"

# 25-110:
"D3_50_E1:InSilicoSize50-Ecoli1-trajectories_exp;D3_50_E2:InSilicoSize50-Ecoli2-trajectories_exp;D3_50_Y1:InSilicoSize50-Yeast1-trajectories_exp;D3_50_Y2:InSilicoSize50-Yeast2-trajectories_exp;D3_50_Y3:InSilicoSize50-Yeast3-trajectories_exp;D3_100_E1:InSilicoSize100-Ecoli1-trajectories_exp;D3_100_E2:InSilicoSize100-Ecoli2-trajectories_exp;D3_100_Y1:InSilicoSize100-Yeast1-trajectories_exp;D3_100_Y2:InSilicoSize100-Yeast2-trajectories_exp;D3_100_Y3:InSilicoSize100-Yeast3-trajectories_exp"
"FS-EM50-KD:sim_eipo-modular_size-50_knockdown_exp;FS-EM50-KO:sim_eipo-modular_size-50_knockout_exp;FS-EM50-O:sim_eipo-modular_size-50_overexpression_exp;FS-SF50-KD:sim_scale-free_size-50_knockdown_exp;FS-SF50-KO:sim_scale-free_size-50_knockout_exp;FS-SF50-O:sim_scale-free_size-50_overexpression_exp;FS-EM100-KD:sim_eipo-modular_size-100_knockdown_exp;FS-EM100-KO:sim_eipo-modular_size-100_knockout_exp;FS-EM100-O:sim_eipo-modular_size-100_overexpression_exp;FS-SF100-KD:sim_scale-free_size-100_knockdown_exp;FS-SF100-KO:sim_scale-free_size-100_knockout_exp;FS-SF100-O:sim_scale-free_size-100_overexpression_exp"
"BG-NC-M:sim_BioGrid_Neurospora_crassa_OR74A_mixed_exp;BG-GM-M:sim_BioGrid_Glycine_max_mixed_exp;BG-CS-M:sim_BioGrid_Chlorocebus_sabaeus_mixed_exp;BG-HIV2-M:sim_BioGrid_Human_Immunodeficiency_Virus_2_mixed_exp;BG-EN-M:sim_BioGrid_Emericella_nidulans_FGSC_A4_mixed_exp;TFL-CE-M:sim_TFLink_Caenorhabditis_elegans_mixed_exp;BG-CG-M:sim_BioGrid_Cricetulus_griseus_mixed_exp;D4-100-1:dream4_100_01_exp;D4-100-2:dream4_100_02_exp;D4-100-3:dream4_100_03_exp;D4-100-4:dream4_100_04_exp;D4-100-5:dream4_100_05_exp"

# 110-250:
"BG-SS-M:sim_BioGrid_Sus_scrofa_mixed_exp;BG-HPV5-M:sim_BioGrid_Human_papillomavirus_5_mixed_exp;BG-HHV5-M:sim_BioGrid_Human_Herpesvirus_5_mixed_exp;BG-CF-M:sim_BioGrid_Canis_familiaris_mixed_exp;TFL-DM-M:sim_TFLink_Drosophila_melanogaster_mixed_exp;FS-EM200-KD:sim_eipo-modular_size-200_knockdown_exp;FS-EM200-KO:sim_eipo-modular_size-200_knockout_exp;FS-EM200-O:sim_eipo-modular_size-200_overexpression_exp;FS-SF200-KD:sim_scale-free_size-200_knockdown_exp;FS-SF200-KO:sim_scale-free_size-200_knockout_exp;FS-SF200-O:sim_scale-free_size-200_overexpression_exp;BG-HHV1-M:sim_BioGrid_Human_Herpesvirus_1_mixed_exp"

# 250-2000:
"SNT300:syntren300_exp;SNT1000:syntren1000_exp;RGR1000:rogers1000_exp;GNW1565:gnw1565_exp;RN-MOUSE-M:sim_RegNetwork_mouse_mixed_exp;RN-HUMAN-M:sim_RegNetwork_human_mixed_exp;TFL-SC-M:sim_TFLink_Saccharomyces_cerevisiae_mixed_exp"
"BG-MM-M:sim_BioGrid_Macaca_mulatta_mixed_exp;BG-OSJ-M:sim_BioGrid_Oryza_sativa_Japonica_mixed_exp;BG-OC-M:sim_BioGrid_Oryctolagus_cuniculus_mixed_exp;BG-GG-M:sim_BioGrid_Gallus_gallus_mixed_exp;BG-HPV6B-M:sim_BioGrid_Human_papillomavirus_6b_mixed_exp;BG-HPV16-M:sim_BioGrid_Human_papillomavirus_16_mixed_exp;BG-HHV4-M:sim_BioGrid_Human_Herpesvirus_4_mixed_exp;BG-DR-M:sim_BioGrid_Danio_rerio_mixed_exp;BG-BT-M:sim_BioGrid_Bos_taurus_mixed_exp;BG-MERSC-M:sim_BioGrid_Middle-East_Respiratory_Syndrome-related_Coronavirus_mixed_exp;BG-PF-M:sim_BioGrid_Plasmodium_falciparum_3D7_mixed_exp;BG-XL-M:sim_BioGrid_Xenopus_laevis_mixed_exp;BG-HHV8-M:sim_BioGrid_Human_Herpesvirus_8_mixed_exp"
"GRNdb-FB-M:sim_GRNdb_Fetal-Brain_mixed_exp;GRNdb-FT-M:sim_GRNdb_Fetal-Thymus_mixed_exp;GRNdb-AP-M:sim_GRNdb_Adult-Pancreas_mixed_exp;GRNdb-AA-M:sim_GRNdb_Adult-Adipose_mixed_exp;GRNdb-AL-M:sim_GRNdb_Adult-Lung_mixed_exp;GRNdb-AAC-M:sim_GRNdb_Adult-Ascending-Colon_mixed_exp;GRNdb-AM-M:sim_GRNdb_Adult-Muscle_mixed_exp;GRNdb-ALV-M:sim_GRNdb_Adult-Liver_mixed_exp;GRNdb-AE-M:sim_GRNdb_Adult-Epityphlon_mixed_exp;GRNdb-FC-M:sim_GRNdb_Fetal-Calvaria_mixed_exp;GRNdb-AR-M:sim_GRNdb_Adult-Rectum_mixed_exp"

# 2000-...:
"GNW2000:gnw2000_exp;RegDB-EC-M:sim_RegulonDB_Escherichia_coli_mixed_exp"
)

mkdir -p graphics
i=0

# Recorrer la lista de redes génicas
for net in ${nets[@]}; do

    # Separar las redes génicas dentro de cada elemento
    IFS=';' read -ra networks <<< "$net"

    # Argumentos para ejecutar el script
    str=""
    
    # Recorrer las redes génicas separadas
    for network in ${networks[@]}; do
        # Dividir el elemento en el identificador y el nombre de la red génica
        IFS=':' read -r id name <<< "$network"
      
        # Añadir al argumento el identificador y el nombre
        str+="$id ../inferred_networks/$name/measurements/scores.csv "
    done

    # Barplot
    Rscript barplot.R $str graphics/barplot$i.pdf

    # Radar
    Rscript radar.R $str graphics/radar$i.pdf

    # Lines
    Rscript lines.R $str graphics/lines$i.pdf

    i=$(( $i + 1 ))

done

# Makes final groups graphics
nets=(
# 0-25:
"D4_10_3:dream4_010_03_exp;D4_10_5:dream4_010_05_exp;D3_10_E1:InSilicoSize10-Ecoli1-trajectories_exp;D3_10_Y2:InSilicoSize10-Yeast2-trajectories_exp;BG-SV40-M:sim_BioGrid_Simian_Virus_40_mixed_exp;TFL-RN-M:sim_TFLink_Rattus_norvegicus_mixed_exp;BG-CR-M:sim_BioGrid_Chlamydomonas_reinhardtii_mixed_exp;BG-SIV-M:sim_BioGrid_Simian_Immunodeficiency_Virus_mixed_exp;FS-EM20-KO:sim_eipo-modular_size-20_knockout_exp;FS-SF20-O:sim_scale-free_size-20_overexpression_exp"

# 25-110:
"D3_50_Y2:InSilicoSize50-Yeast2-trajectories_exp;D3_50_Y3:InSilicoSize50-Yeast3-trajectories_exp;D3_100_E1:InSilicoSize100-Ecoli1-trajectories_exp;FS-EM50-KO:sim_eipo-modular_size-50_knockout_exp;FS-SF50-O:sim_scale-free_size-50_overexpression_exp;FS-EM100-KD:sim_eipo-modular_size-100_knockdown_exp;FS-SF100-KD:sim_scale-free_size-100_knockdown_exp;BG-EN-M:sim_BioGrid_Emericella_nidulans_FGSC_A4_mixed_exp;D4-100-2:dream4_100_02_exp;D4-100-5:dream4_100_05_exp"

# 110-250:
"BG-SS-M:sim_BioGrid_Sus_scrofa_mixed_exp;BG-HPV5-M:sim_BioGrid_Human_papillomavirus_5_mixed_exp;BG-HHV5-M:sim_BioGrid_Human_Herpesvirus_5_mixed_exp;TFL-DM-M:sim_TFLink_Drosophila_melanogaster_mixed_exp;FS-EM200-KD:sim_eipo-modular_size-200_knockdown_exp;FS-EM200-KO:sim_eipo-modular_size-200_knockout_exp;FS-EM200-O:sim_eipo-modular_size-200_overexpression_exp;FS-SF200-KD:sim_scale-free_size-200_knockdown_exp;FS-SF200-KO:sim_scale-free_size-200_knockout_exp;FS-SF200-O:sim_scale-free_size-200_overexpression_exp"

# 250-2000:
"RN-MOUSE-M:sim_RegNetwork_mouse_mixed_exp;RN-HUMAN-M:sim_RegNetwork_human_mixed_exp;SNT1000:syntren1000_exp;BG-GG-M:sim_BioGrid_Gallus_gallus_mixed_exp;BG-DR-M:sim_BioGrid_Danio_rerio_mixed_exp;BG-MERSC-M:sim_BioGrid_Middle-East_Respiratory_Syndrome-related_Coronavirus_mixed_exp;BG-HHV8-M:sim_BioGrid_Human_Herpesvirus_8_mixed_exp;GRNdb-FB-M:sim_GRNdb_Fetal-Brain_mixed_exp;GRNdb-AA-M:sim_GRNdb_Adult-Adipose_mixed_exp;GRNdb-AM-M:sim_GRNdb_Adult-Muscle_mixed_exp"
)

mkdir -p final_grouped_graphics
i=0

# Recorrer la lista de redes génicas
for net in ${nets[@]}; do

    # Separar las redes génicas dentro de cada elemento
    IFS=';' read -ra networks <<< "$net"

    # Argumentos para ejecutar el script
    str=""
    
    # Recorrer las redes génicas separadas
    for network in ${networks[@]}; do
        # Dividir el elemento en el identificador y el nombre de la red génica
        IFS=':' read -r id name <<< "$network"
      
        # Añadir al argumento el identificador y el nombre
        str+="$id ../inferred_networks/$name/measurements/scores.csv "
    done

    # Barplot
    Rscript barplot.R $str final_grouped_graphics/barplot$i.pdf

    # Radar
    Rscript radar.R $str final_grouped_graphics/radar$i.pdf

    # Lines
    Rscript lines.R $str final_grouped_graphics/lines$i.pdf

    i=$(( $i + 1 ))

done