import pandas as pd
import numpy as np
import argparse

def is_dominated(point, others):
    """
    Check if a point is dominated by any point in a set of others.
    A point is dominated if another point is:
    - Less than or equal in all dimensions, and
    - Strictly less in at least one dimension.
    """
    return np.any((others <= point).all(axis=1) & (others < point).any(axis=1))

def main(fun_file, var_file, output_fun, output_var):
    # Cargar los archivos
    fun_data = pd.read_csv(fun_file)
    var_data = pd.read_csv(var_file)
    
    if len(fun_data) != len(var_data):
        raise ValueError("FUN.csv y VAR.csv deben tener el mismo número de filas.")
    
    # Convertir los datos de FUN a numpy para calcular la dominancia
    fun_data_np = fun_data.to_numpy()

    # Identificar las filas no dominadas
    non_dominated_indices = []
    for i, point in enumerate(fun_data_np):
        others = np.delete(fun_data_np, i, axis=0)
        if not is_dominated(point, others):
            non_dominated_indices.append(i)
    
    # Extraer las filas no dominadas de ambos archivos
    fun_non_dominated = fun_data.iloc[non_dominated_indices]
    var_non_dominated = var_data.iloc[non_dominated_indices]
    
    # Guardar los resultados en nuevos archivos
    fun_non_dominated.to_csv(output_fun, index=False)
    var_non_dominated.to_csv(output_var, index=False)
    print(f"Puntos no dominados guardados en: {output_fun} y {output_var}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Calcular puntos no dominados en FUN.csv y sincronizarlos con VAR.csv.")
    parser.add_argument("--fun-file", help="Ruta al archivo FUN.csv")
    parser.add_argument("--var-file", help="Ruta al archivo VAR.csv")
    parser.add_argument("--output-fun", help="Ruta para guardar el archivo de salida de FUN no dominado")
    parser.add_argument("--output-var", help="Ruta para guardar el archivo de salida de VAR no dominado")
    
    args = parser.parse_args()
    main(args.fun_file, args.var_file, args.output_fun, args.output_var)
