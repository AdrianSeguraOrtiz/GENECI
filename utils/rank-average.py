import pandas as pd
import typer
from typing import List, Optional

def normalized_rank_average(
        file: Optional[List[str]] = typer.Option(..., help="CSV input files"),
        output_file: str = typer.Option(..., help="Path to output file"),
    ):

    # Leer todos los archivos CSV de entrada
    dfs = [pd.read_csv(f, header=None, names=["source", "target", "confidence"+str(i)]) for i, f in enumerate(file)]
    
    # Fusionar las redes en un único DataFrame
    res = dfs.pop(0)
    for df in dfs:
        res = pd.merge(res, df, on=["source", "target"], how="outer")

    # Rellenar valores NaN con 0 (ausencia de arista en una red dada)
    res = res.fillna(0)

    # Obtener las columnas de confianza
    confidence_cols = res.columns[2:]

    # Asignar ranking dentro de cada red (columna de confianza)
    for col in confidence_cols:
        res[col + "_rank"] = res[col].rank(method="average", ascending=False)

    # Calcular el ranking promedio
    res["avg_rank"] = res[[col + "_rank" for col in confidence_cols]].mean(axis=1)

    # Normalizar la confianza en el rango [0,1]
    res["confidence"] = 1 - (res["avg_rank"] - res["avg_rank"].min()) / (res["avg_rank"].max() - res["avg_rank"].min())

    # Guardar la red consensuada en el archivo de salida
    res[["source", "target", "confidence"]].to_csv(output_file, header=False, index=False)

if __name__ == "__main__":
    typer.run(normalized_rank_average)
