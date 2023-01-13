# Unimos las tablas de las funciones con las de las técnicas
join -t, -a1 -a2 -e '?' <(sort AUPR_functions.csv) <(sort AUPR_techniques.csv) > temp_AUPR.csv
n=$(grep -n 'Network' temp_AUPR.csv | cut -f1 -d:)
printf '%s\n' "${n}m0" 'w AUPR.csv' 'q' | ed -s temp_AUPR.csv
rm temp_AUPR.csv

join -t, -a1 -a2 -e '?' <(sort AUROC_functions.csv) <(sort AUROC_techniques.csv) > temp_AUROC.csv
n=$(grep -n 'Network' temp_AUROC.csv | cut -f1 -d:)
printf '%s\n' "${n}m0" 'w AUROC.csv' 'q' | ed -s temp_AUROC.csv
rm temp_AUROC.csv

join -t, -a1 -a2 -e '?' <(sort Mean_functions.csv) <(sort Mean_techniques.csv) > temp_Mean.csv
n=$(grep -n 'Network' temp_Mean.csv | cut -f1 -d:)
printf '%s\n' "${n}m0" 'w Mean.csv' 'q' | ed -s temp_Mean.csv
rm temp_Mean.csv

# Ejecutamos los tests de Friedman
cd controlTest && java Friedman.java ../AUPR.csv > ../AUPR.tex && cd ..
cd controlTest && java Friedman.java ../AUROC.csv > ../AUROC.tex && cd ..
cd controlTest && java Friedman.java ../Mean.csv > ../Mean.tex && cd ..