from pathlib import Path
from dreamtools import D3C4, D4C2, D5C4
import pandas as pd 
import argparse
import shutil
from easydev import Progress
import numpy as np

class MyD3C4(D3C4):
    def _init(self):
        return

class MyD5C4(D5C4):
    def _get_G(self, gold):
        regulators = [int(reg) for reg in list(set(gold[0]))]
        targets = [int(tar) for tar in list(set(gold[[0,1]].stack()))]

        N, M = gold[0].max(), gold[1].max()

        A = np.zeros((int(N), int(M)))
        for row in gold[[0,1]].values:
            i, j = row
            A[int(i)-1, int(j)-1] = 1

        G = np.zeros((int(N), int(M)))

        pb = Progress(len(regulators), 1)
        for i, x in enumerate(regulators):
            for j, y in enumerate(targets):
                if A[x-1, y-1] == 1:
                    G[x-1, y-1] = 1
                elif x != y:
                    G[x-1, y-1] = -1
            pb.animate(i+1)
        return G
    
    def _remove_edges_not_in_gs(self, prediction, G):
        N, M = G.shape

        data_pred = [tuple(x) for x in prediction[[0,1]].values]

        count = 0
        tokeep = []
        for ikeep, row in enumerate(data_pred):
            i, j = row
            if (i <= N) and (j <= M):
                if G[int(i)-1, int(j)-1] != 0:
                    count += 1
                    tokeep.append(ikeep)

        return prediction.copy().ix[tokeep]
    
    def download_goldstandard(self):
        filenames = []
        for tag in [1,3,4]:
            filename = "DREAM5_NetworkInference_Edges_Network%s.tsv" % tag
            try:
                filepath = self.get_pathname(filename)
            except:
                filepath = None
            filenames.append(filepath)
        return filenames


parser = argparse.ArgumentParser(description='This component is responsible for evaluating the accuracy with which networks belonging to the DREAM challenges are predicted.')
parser.add_argument('--challenge', type=str, help='DREAM challenge to which the inferred network belongs')
parser.add_argument('--network-id', type=str, help='Predicted network identifier. Ex: 10_1')
parser.add_argument('--synapse-folder', type=Path, help='Path to the folder containing the necessary synapse files')
parser.add_argument('--confidence-list', type=Path, help='Path to the CSV file with the list of trusted values')

args = parser.parse_args()

csv_table = pd.read_table(args.confidence_list, sep=',')
tsv_filename = args.confidence_list.stem + ".tsv"
csv_table.to_csv(tsv_filename, sep="\t", index=False)

folder = "/root/.config/dreamtools/dream" + args.challenge[1] + "/" + args.challenge + "/"
shutil.copytree(str(args.synapse_folder), folder)

if args.challenge == "D3C4":
    s = MyD3C4(download=False)
    measures = s.score_prediction(filename = tsv_filename, subname = args.network_id)
    print("AUPR: " + str(measures["AUPR"]))
    print("AUROC: " + str(measures["AUROC"]))

elif args.challenge == "D4C2":
    s = D4C2(download=False)
    measures = s.score_prediction(filename = tsv_filename, subname = args.network_id)
    print("AUPR: " + str(measures["AUPR"]))
    print("AUROC: " + str(measures["AUROC"]))

elif args.challenge == "D5C4":
    s = MyD5C4(download=False)
    measures = s.score_challengeA(filename = tsv_filename, tag = int(args.network_id))
    print()
    print("AUPR: " + str(measures["aupr"]))
    print("AUROC: " + str(measures["auroc"]))

else:
    raise Exception("The challenge entered is invalid or not implemented.")


