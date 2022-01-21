import pandas as pd

from arboreto.algo import diy
from arboreto.core import RF_KWARGS, SGBM_KWARGS, ET_KWARGS

if __name__ == '__main__':

    in_file = '../data/DREAM4/EXP/dream4_010_01_exp.csv'

    # Load the expression matrix
    ex_matrix = pd.read_csv(in_file, index_col=0).T

    # Define gene identifiers
    tf_names = list(ex_matrix.columns.values)

    # Infer gene regulatory network
    ## Random Forest regression (RF)
    conf_list_RF = diy(expression_data=ex_matrix, tf_names=tf_names, regressor_type='RF', regressor_kwargs=RF_KWARGS)
    print(conf_list_RF)

    ## Gradient Boosting Machine regression with early-stopping regularization (GBM)
    conf_list_GBM = diy(expression_data=ex_matrix, tf_names=tf_names, regressor_type='GBM', regressor_kwargs=SGBM_KWARGS)
    print(conf_list_GBM)

    ## ExtraTrees regression (ET)
    conf_list_ET = diy(expression_data=ex_matrix, tf_names=tf_names, regressor_type='ET', regressor_kwargs=ET_KWARGS)
    print(conf_list_ET)

    # OPTIONAL: Export inferred gene conf_list to CSV file
    #conf_list.to_csv(out_file, index=False, header=False)