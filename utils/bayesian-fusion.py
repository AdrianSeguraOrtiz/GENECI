import pandas as pd
import typer
from typing import List, Optional

def bayesian_fusion(
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

    # Parámetros iniciales de la distribución Beta
    alpha_prior = 1  # Creencia inicial de existencia de la arista
    beta_prior = 1   # Creencia inicial de no existencia

    # Actualizar la distribución Beta con los valores observados
    res["alpha"] = alpha_prior + res[confidence_cols].sum(axis=1)
    res["beta"] = beta_prior + (1 - res[confidence_cols]).sum(axis=1)

    # Calcular la confianza final como la media de la distribución Beta
    res["confidence"] = res["alpha"] / (res["alpha"] + res["beta"])

    # Guardar la red consensuada en el archivo de salida
    res[["source", "target", "confidence"]].to_csv(output_file, header=False, index=False)

if __name__ == "__main__":
    typer.run(bayesian_fusion)