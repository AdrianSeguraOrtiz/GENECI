from pathlib import Path
from enum import Enum

import pandas as pd
import typer
from arboreto.algo import diy
from arboreto.core import ET_KWARGS, RF_KWARGS, SGBM_KWARGS

class Regressor(str, Enum):
    RF = "RF"
    GBM = "GBM"
    ET = "ET"

def process_list(conf_list):
    v_conf = conf_list["importance"]
    v_scaled = (v_conf - min(v_conf)) / (max(v_conf) - min(v_conf))
    conf_list["importance"] = v_scaled
    conf_list = conf_list.loc[conf_list["importance"] != 0]
    return(conf_list)


def genie3(
        in_file: str = typer.Argument(..., help="CSV input file"),
        output_folder: str = typer.Argument(..., help="Path to output folder"),
        regressor_type: Regressor = typer.Argument(..., help="Regression type: Random Forest regression (RF), Gradient Boosting Machine regression with early-stopping regularization (GBM) or ExtraTrees regression (ET)")
    ):
    
    # Load the expression matrix
    ex_matrix = pd.read_csv(in_file, index_col=0).T

    # Define gene identifiers
    tf_names = list(ex_matrix.columns.values)

    # Infer gene regulatory network
    if regressor_type.name == "RF":
        ## Random Forest regression (RF)
        conf_list = diy(expression_data=ex_matrix, tf_names=tf_names, regressor_type='RF', regressor_kwargs=RF_KWARGS)
    elif regressor_type.name == "GBM":
        ## Gradient Boosting Machine regression with early-stopping regularization (GBM)
        conf_list = diy(expression_data=ex_matrix, tf_names=tf_names, regressor_type='GBM', regressor_kwargs=SGBM_KWARGS)
    elif regressor_type.name == "ET":
        ## ExtraTrees regression (ET)
        conf_list = diy(expression_data=ex_matrix, tf_names=tf_names, regressor_type='ET', regressor_kwargs=ET_KWARGS)
    
    # Standardization
    conf_list = process_list(conf_list)

    # Save list
    conf_list.to_csv(f"./{output_folder}/{Path(in_file).stem}/lists/GRN_GENIE3_{regressor_type.name}.csv", header=False, index=False)


if __name__ == "__main__":
    typer.run(genie3)