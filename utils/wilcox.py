import pandas as pd
from scipy.stats import wilcoxon

# Leer el archivo CSV directamente en un DataFrame
df = pd.read_csv("functions_comparison/AUROC_degree_functions.csv")

# Calcular el p-valor de Wilcoxon para v1 y v2 en general
p_value = wilcoxon(df["binarizeddegreedistribution"], df["weighteddegreedistribution"]).pvalue

# Imprimir el p-valor resultante
print("P-valor entre v1 y v2 en general:", p_value)