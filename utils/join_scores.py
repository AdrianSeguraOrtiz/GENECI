import typer
import re
import pandas as pd

def find_nearest_row(df, target_value, column_name):
    idx = (df[column_name]-target_value).abs().idxmin()
    return df.loc[idx, ["AUPR", "AUROC", "Mean"]]

def search_metrics(file):
    # Read mean file
    with open(file, 'r') as f:
        contenido = f.read()

    # Search the auroc value
    match_auroc = re.search(r'AUROC:\s+(\d+\.\d+)', contenido)
    auroc = float(match_auroc.group(1))

    # Search the AUPR value
    match_aupr = re.search(r'AUPR:\s+(\d+\.\d+)', contenido)
    aupr = float(match_aupr.group(1))
    
    # Add to final df
    return [aupr, auroc, (aupr+auroc)/2]

def join_scores(
        tecs_file: str = typer.Option(..., help="Path to CSV tecs file"),
        geneci_file: str = typer.Option(..., help="Path to CSV geneci file"),
        mean_file: str = typer.Option(None, help="Path to mean file"),
        median_file: str = typer.Option(None, help="Path to median file"),
        output_file: str = typer.Option(..., help="Path to output file"),
    ):
    
    # Read tecs file
    df_tecs = pd.read_csv(tecs_file, header=1, sep=";")
    if 'Time' in df_tecs.columns:
        del df_tecs["Time"]
    
    # Read geneci file
    df_geneci = pd.read_csv(geneci_file, header=1, sep= ",")
    df_geneci.rename(columns={'Accuracy Mean': 'Mean'}, inplace=True)
    
    # Get best geneci
    best_scaled_mean = df_geneci["Mean Scaled"].max()
    best_row = find_nearest_row(df_geneci, best_scaled_mean, "Mean Scaled") 
    best_row = pd.DataFrame([["BEST_GENECI"] + best_row.tolist()], columns=["Technique"] + best_row.index.tolist())
    df_tecs = pd.concat([df_tecs, best_row], ignore_index=True)
    
    # Get median geneci
    median_scaled_mean = df_geneci["Mean Scaled"].median()
    median_row = find_nearest_row(df_geneci, median_scaled_mean, "Mean Scaled")
    median_row = pd.DataFrame([["MEDIAN_GENECI"] + median_row.tolist()], columns=["Technique"] + median_row.index.tolist())
    df_tecs = pd.concat([df_tecs, median_row], ignore_index=True)
    
    # Mean file
    if mean_file:
        mean = search_metrics(mean_file)
        df_tecs = pd.concat([df_tecs, pd.DataFrame([["MEAN"] + mean], columns=df_tecs.columns.tolist())], ignore_index=True)
    
    # Median file
    if median_file:
        median = search_metrics(median_file)
        df_tecs = pd.concat([df_tecs, pd.DataFrame([["MEDIAN"] + median], columns=df_tecs.columns.tolist())], ignore_index=True)

    # Save in csv output file
    df_tecs.to_csv(output_file, index=False, sep=";")

if __name__ == "__main__":
    typer.run(join_scores)