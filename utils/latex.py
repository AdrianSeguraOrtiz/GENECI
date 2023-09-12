import pandas as pd
from tabulate import tabulate
import re

# Tabla 1 en formato LaTeX
table1_latex = r'''

'''

# Tabla 2 en formato LaTeX
table2_latex = r'''

'''

def latex_to_dataframe(latex_table):
    # Extraer los datos de la tabla LaTeX utilizando una expresión regular
    pattern = r'\\begin{tabular}{.*}\n(.*)\\end{tabular}'
    table_content = re.search(pattern, latex_table, re.DOTALL).group(1)

    # Remover los comandos LaTeX para obtener solo las filas y las celdas
    table_content = table_content.replace(r'\hline', '').strip()

    # Dividir las filas y las celdas
    rows = table_content.split(r'\\')
    data = [re.split(r'&', row.replace(r'\\', '').replace('\n', '')) for row in rows]
    data.pop()

    # Crear el DataFrame de pandas
    df = pd.DataFrame(data[1:], columns=[col.strip() for col in data[0]])

    return df

# Convertir tablas LaTeX a DataFrames
df_table1 = latex_to_dataframe(table1_latex)
df_table2 = latex_to_dataframe(table2_latex)

# Ordenar la tabla de Friedman por el ranking
df_table1["Ranking"] = pd.to_numeric(df_table1["Ranking"], downcast="float")
df_table1_sorted = df_table1.sort_values(by='Ranking', ascending=True)

# Combinar ambas tablas
df_combined = pd.merge(df_table1_sorted, df_table2, left_on='Algorithm', right_on='algorithm', how='left')

# Seleccionar solo las columnas necesarias
df_combined = df_combined[['Algorithm', 'Ranking', '$p_{Holm}$']]

# Renombrar columnas
df_combined.columns = ['Technique', "$Friedman's {Rank}$", "$Holm's {Adj-p}$"]

# Crear la tabla LaTeX final
latex_table_combined = tabulate(df_combined, headers='keys', tablefmt='latex', showindex=False)

# Imprimir la tabla LaTeX final
print(latex_table_combined)
