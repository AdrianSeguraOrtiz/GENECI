import typer 
from typing import List
import pandas as pd

def csvs2latex(
    csv_table: List[str] = typer.Option(..., help="Paths of the CSV files with the score tables")
):

    str_res = """
\\begin{table}[!t]
    \\begin{center}
        \\setlength{\\tabcolsep}{0.5em} 
        \\def\\arraystretch{1.2}
        \\resizebox{\\textwidth}{!}{\\begin{tabular}{t | t t t t t t t t t t} 
            \\hline
    
    """

    str_head_1 = "\t    \\multirow{2}{*}{\\textbf{Técnica}}"
    str_head_2 = "\t    "
    dict_str_techniques_values = dict()
    net_names = list()

    for f in csv_table:
        df = pd.read_csv(f, sep=";", header=None)
        max_auroc = max([float(v) for v in df.iloc[2:-1, 2]])
        max_aupr = max([float(v) for v in df.iloc[2:-1, 1]])
        
        for index, row in df.iterrows():
            if index == 0: 
                net_names.append(row[0])
                str_head_1 += "& \\multicolumn{2}{ c }{\\textbf{" + row[0] + "}} "
            elif index == 1: 
                str_head_2 += "& \\textbf{AUROC} & \\textbf{AUPR} "
            else:
                if row[0] not in dict_str_techniques_values.keys(): 
                    if "GENECI" in row[0]: dict_str_techniques_values[row[0]] = "\\textbf{" + row[0] + "} "
                    else: dict_str_techniques_values[row[0]] = row[0] + " "

                auroc = str(round(float(row[2]), 4))
                if float(row[2]) == max_auroc or "GENECI" in row[0]: auroc = "\\textbf{" + auroc + "}"
                aupr = str(round(float(row[1]), 4))
                if float(row[1]) == max_aupr or "GENECI" in row[0]: aupr = "\\textbf{" + aupr + "}"
                dict_str_techniques_values[row[0]] += "& " + auroc + " & " + aupr + " "
    
    str_res += str_head_1 + "\\\\ \n" + str_head_2 + "\\\\ \n \t    \\hline \n"
    for k,v in dict_str_techniques_values.items():
        if "GENECI" in k: 
            str_res += "\t    \\hline \n"
        str_res += "\t    " + v + "\\\\ \n"

    str_res += """
            \\hline
        \\end{tabular}}
    \\end{center}
    \\caption{Valores de precisión para las redes de DX y tamaño XX}
    \\label{precision-DX-TXX}
\\end{table}
    """
    print(str_res.replace("_", "\_"))


if __name__ == "__main__":
    typer.run(csvs2latex)