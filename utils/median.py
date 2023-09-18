import pandas as pd
import typer
from typing import List, Optional

def median(
        file: Optional[List[str]] = typer.Option(..., help="CSV input files"),
        output_file: str = typer.Option(..., help="Path to output file"),
    ):

    # Read all input CSV files
    dfs = [pd.read_csv(f, header=None, names=["source", "target", "confidence"+str(i)]) for i,f in enumerate(file)]

    # Merge them in the same dataframe
    res = dfs.pop(0)
    for df in dfs:
        res = pd.merge(res, df, on=["source", "target"], how="outer")
    
    # Fill Nas with zeros
    res = res.fillna(0)

    # Calculate median
    res["median"] = res.iloc[:, 2:].median(1)

    # Save result in output_file
    res[["source", "target", "median"]].to_csv(output_file, header=False, index=False)

if __name__ == "__main__":
    typer.run(median)