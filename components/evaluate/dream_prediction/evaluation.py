from pathlib import Path
from dreamtools import D4C2, D5C1
import pandas as pd 
import argparse
import shutil


parser = argparse.ArgumentParser(description='This component is responsible for evaluating the accuracy with which networks belonging to the DREAM challenges are predicted.')
parser.add_argument('--challenge', type=str, help='DREAM challenge to which the inferred network belongs')
parser.add_argument('--network-id', type=str, help='Predicted network identifier. Ex: 10_1')
parser.add_argument('--mat-file', type=Path, help='Path to the .mat file required for performance evaluation')
parser.add_argument('--confidence-list', type=Path, help='Path to the CSV file with the list of trusted values')

args = parser.parse_args()

s = None
if args.challenge == "D4C2":
    s = D4C2(download=False)
elif args.challenge == "D5C1":
    s = D5C1(download=False)
else:
    raise Exception("The challenge entered is invalid or not implemented.")

folder = "/root/.config/dreamtools/dream" + args.challenge[1] + "/" + args.challenge + "/"
shutil.copyfile(str(args.mat_file), folder + "/pdf_size" + args.network_id + ".mat")

csv_table = pd.read_table(args.confidence_list, sep=',')
tsv_filename = args.confidence_list.stem + ".tsv"
csv_table.to_csv(tsv_filename, sep="\t", index=False)

measures = s.score_prediction(filename = tsv_filename, subname = args.network_id)
print("AUPR: " + str(measures["AUPR"]))
print("AUROC: " + str(measures["AUROC"]))
