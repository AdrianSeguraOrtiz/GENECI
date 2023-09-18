import pandas as pd
import typer
from scipy.stats import wilcoxon

def wilcox(
    input_file: str = typer.Option(..., help="Path to csv input file"),
):

    # Cargar los datos desde el archivo CSV
    df = pd.read_csv(input_file)

    # Seleccionar las columnas de interés para los dos algoritmos que deseas comparar
    algoritmo1 = df.iloc[:, 1]
    algoritmo2 = df.iloc[:, 2]

    # Aplicar la prueba de Wilcoxon
    statistic, p_value = wilcoxon(algoritmo1, algoritmo2)

    # Imprimir los resultados
    print("Estadístico de la prueba:", statistic)
    print("Valor p:", p_value)


if __name__ == "__main__":
    typer.run(wilcox)