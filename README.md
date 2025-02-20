![CI](https://github.com/AdrianSeguraOrtiz/GENECI/actions/workflows/ci.yml/badge.svg)
![Release](https://github.com/AdrianSeguraOrtiz/GENECI/actions/workflows/release.yml/badge.svg)
![Pypi](https://img.shields.io/pypi/v/GENECI/2.5.1)

[PBEvoGen (Preference Based Evolutionary Gene network consensus inference)](https://github.com/AdrianSeguraOrtiz/PBEvoGen) is a software package derived from [MO-GENECI](https://github.com/AdrianSeguraOrtiz/MO-GENECI) that incorporates a preference selection mechanism that allows the user to guide the exploration of the evolutionary algorithm based on prior knowledge of the search space.

![Alt text](https://github.com/AdrianSeguraOrtiz/GENECI/raw/v-2.5.1/docs/diagram.svg)


# Prerequisites

- Python => 3.9
- Docker

# Instalation

```sh
pip install geneci==2.5.1
```

# Integrated techniques

PBEvoGen integrates the 26 inference techniques already contemplated in [MO-GENECI](https://github.com/AdrianSeguraOrtiz/MO-GENECI): ARACNE, BC3NET, C3NET, CLR, GENIE3_RF, GRNBOOST2, GENIE3_ET, MRNET, MRNETB, PCIT, TIGRESS, KBOOST, MEOMI, JUMP3, NARROMI, CMI2NI, RSNET, PCACMI, LOCPCACMI, PLSNET, PIDC, PUC, GRNVBEM, LEAP, NONLINEARODES, INFERELATOR.

# Example procedure

1. **Obtain simulated expression data and their respective gold standards**. As in [MO-GENECI](https://github.com/AdrianSeguraOrtiz/MO-GENECI).

2. **Inference and consensus** of networks for the selected expression data. Unlike in [MO-GENECI](https://github.com/AdrianSeguraOrtiz/MO-GENECI), PBEvoGen integrates the `--reference-point` parameter that allows the specification of a reference point to condition the selection of individuals.

- **Form 1**: Procedure prefixed by the command run.

```sh
geneci run --expression-data input_data/DREAM4/EXP/dream4_100_01_exp.csv \
           --technique ARACNE --technique BC3NET --technique C3NET --technique CLR \
           --technique GENIE3_RF --technique GRNBOOST2 --technique GENIE3_ET \
           --technique MRNET --technique MRNETB --technique PCIT --technique TIGRESS \
           --technique KBOOST --technique MEOMI --technique NARROMI --technique CMI2NI \
           --technique RSNET --technique PCACMI --technique LOCPCACMI --technique PLSNET \
           --technique PIDC --technique PUC --technique GRNVBEM --technique LEAP \
           --technique NONLINEARODES --technique INFERELATOR \
           --crossover-probability 0.9 --mutation-probability 0.05 --population-size 100 \
           --num-parents 3 --mutation-strength 0.1 \
           --num-evaluations 50000 --cut-off-criteria PercLinksWithBestConf --cut-off-value 0.4 \
           --function Quality --function DegreeDistribution --function Motifs \
           --algorithm NSGAII --plot-fitness-evolution --plot-pareto-front \
           --plot-parallel-coordinates --output-dir inferred_networks \
           --reference-point "0.65;35.0;-1800.0"
```

- **Form 2**: Division of the procedure into several commands

```sh
# 1. Inference using individual techniques
geneci infer-network --expression-data input_data/DREAM4/EXP/dream4_100_01_exp.csv \
                     --technique ARACNE --technique BC3NET --technique C3NET --technique CLR \
                     --technique GENIE3_RF --technique GRNBOOST2 --technique GENIE3_ET \
                     --technique MRNET --technique MRNETB --technique PCIT --technique TIGRESS \
                     --technique KBOOST --technique MEOMI --technique NARROMI --technique CMI2NI \
                     --technique RSNET --technique PCACMI --technique LOCPCACMI --technique PLSNET \
                     --technique PIDC --technique PUC --technique GRNVBEM --technique LEAP \
                     --technique NONLINEARODES --technique INFERELATOR \
                     --output-dir inferred_networks/geneci_consensus

# 2. Optimize the assembly of the trust lists resulting from the above command
geneci optimize-ensemble --confidence-list inferred_networks/dream4_100_01_exp/lists/GRN_LOCPCACMI.csv \
                         --confidence-list inferred_networks/dream4_100_01_exp/lists/GRN_BC3NET.csv \
                         --confidence-list inferred_networks/dream4_100_01_exp/lists/GRN_PLSNET.csv \
                         --confidence-list inferred_networks/dream4_100_01_exp/lists/GRN_GRNVBEM.csv \
                         --confidence-list inferred_networks/dream4_100_01_exp/lists/GRN_CMI2NI.csv \
                         --confidence-list inferred_networks/dream4_100_01_exp/lists/GRN_CLR.csv \
                         --confidence-list inferred_networks/dream4_100_01_exp/lists/GRN_INFERELATOR.csv \
                         --confidence-list inferred_networks/dream4_100_01_exp/lists/GRN_GRNBOOST2.csv \
                         --confidence-list inferred_networks/dream4_100_01_exp/lists/GRN_PCACMI.csv \
                         --confidence-list inferred_networks/dream4_100_01_exp/lists/GRN_MRNET.csv \
                         --confidence-list inferred_networks/dream4_100_01_exp/lists/GRN_PCIT.csv \
                         --confidence-list inferred_networks/dream4_100_01_exp/lists/GRN_KBOOST.csv \
                         --confidence-list inferred_networks/dream4_100_01_exp/lists/GRN_MEOMI.csv \
                         --confidence-list inferred_networks/dream4_100_01_exp/lists/GRN_NONLINEARODES.csv \
                         --confidence-list inferred_networks/dream4_100_01_exp/lists/GRN_GENIE3_ET.csv \
                         --confidence-list inferred_networks/dream4_100_01_exp/lists/GRN_NARROMI.csv \
                         --confidence-list inferred_networks/dream4_100_01_exp/lists/GRN_GENIE3_RF.csv \
                         --confidence-list inferred_networks/dream4_100_01_exp/lists/GRN_RSNET.csv \
                         --confidence-list inferred_networks/dream4_100_01_exp/lists/GRN_PIDC.csv \
                         --confidence-list inferred_networks/dream4_100_01_exp/lists/GRN_ARACNE.csv \
                         --confidence-list inferred_networks/dream4_100_01_exp/lists/GRN_MRNETB.csv \
                         --confidence-list inferred_networks/dream4_100_01_exp/lists/GRN_TIGRESS.csv \
                         --confidence-list inferred_networks/dream4_100_01_exp/lists/GRN_LEAP.csv \
                         --confidence-list inferred_networks/dream4_100_01_exp/lists/GRN_PUC.csv \
                         --confidence-list inferred_networks/dream4_100_01_exp/lists/GRN_C3NET.csv \
                         --crossover-probability 0.9 --mutation-probability 0.05 --population-size 100 \
                         --num-parents 3 --mutation-strength 0.1 \
                         --num-evaluations 50000 --cut-off-criteria PercLinksWithBestConf --cut-off-value 0.4 \
                         --function Quality --function DegreeDistribution --function Motifs \
                         --algorithm NSGAII --plot-fitness-evolution --plot-pareto-front \
                         --plot-parallel-coordinates --output-dir inferred_networks/geneci_consensus \
                         --reference-point "0.65;35.0;-1800.0"
```

3. **Representation** of inferred networks. As in [MO-GENECI](https://github.com/AdrianSeguraOrtiz/MO-GENECI).
4. **Evaluation** of the quality of the inferred gene network with respect to the gold standard. As in [MO-GENECI](https://github.com/AdrianSeguraOrtiz/MO-GENECI).
5. **Binarization** of the inferred gene network. As in [MO-GENECI](https://github.com/AdrianSeguraOrtiz/MO-GENECI).

# `geneci`

**Usage**:

```console
$ geneci [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `apply-cut`: Converts a list of confidence values into a binary matrix that represents the final gene network.
* `cluster-network`: Divide an initial gene network into several communities following the Infomap (recommended) or Louvain grouping algorithm.
* `draw-network`: Draw gene regulatory networks from confidence lists.
* `evaluate`: Evaluate the accuracy of the inferred network with respect to its gold standard.
* `extract-data`: Extract public data generated by simulators such as SynTReN, Rogers and GeneNetWeaver, as well as data from known challenges like DREAM3, DREAM4, DREAM5 and IRMA.
* `generate-data`: Simulate time series with gene expression levels using the SysGenSIM simulator. They can be generated from scratch or based on the interactions of a real gene network.
* `infer-network`: Infer gene regulatory networks from expression data. Several techniques are available: ARACNE, BC3NET, C3NET, CLR, GENIE3_RF, GRNBOOST2, GENIE3_ET, MRNET, MRNETB, PCIT, TIGRESS, KBOOST, MEOMI, JUMP3, NARROMI, CMI2NI, RSNET, PCACMI, LOCPCACMI, PLSNET, PIDC, PUC, GRNVBEM, LEAP, NONLINEARODES and INFERELATOR.
* `optimize-ensemble`: Analyzes several trust lists and builds a consensus network by applying an evolutionary algorithm.
* `run`: Infer gene regulatory network from expression data by employing multiple unsupervised learning techniques and applying a genetic algorithm for consensus optimization.
* `weighted-confidence`: Calculate the weighted sum of the confidence levels reported in several files based on a given distribution of weights.

Only modified command specifications are shown with respect to [MO-GENECI](https://github.com/AdrianSeguraOrtiz/MO-GENECI).

## `geneci run`

Infer gene regulatory network from expression data by employing multiple unsupervised learning techniques and applying a genetic algorithm for consensus optimization.

**Usage**:

```console
$ geneci run [OPTIONS]
```

**Options**:

* `--expression-data PATH`: Path to the CSV file with the expression data. Genes are distributed in rows and experimental conditions (time series) in columns.  [required]
* `--time-series PATH`: Path to the CSV file with the time series from which the individual gene networks have been inferred. This parameter is only necessary in case of specifying the fitness function Loyalty.
* `--technique [ARACNE|BC3NET|C3NET|CLR|GENIE3_RF|GRNBOOST2|GENIE3_ET|MRNET|MRNETB|PCIT|TIGRESS|KBOOST|MEOMI|JUMP3|NARROMI|CMI2NI|RSNET|PCACMI|LOCPCACMI|PLSNET|PIDC|PUC|GRNVBEM|LEAP|NONLINEARODES|INFERELATOR]`: Inference techniques to be performed.  [required]
* `--crossover-probability FLOAT`: Crossover probability  [default: 0.9]
* `--num-parents INTEGER`: Number of parents  [default: 3]
* `--mutation-probability FLOAT`: Mutation probability. [default: 1/len(files)]
* `--mutation-strength FLOAT`: Mutation strength. [default: 0.1]
* `--population-size INTEGER`: Population size  [default: 100]
* `--num-evaluations INTEGER`: Number of evaluations  [default: 25000]
* `--cut-off-criteria [MinConf|NumLinksWithBestConf|PercLinksWithBestConf]`: Criteria for determining which links will be part of the final binary matrix.  [default: PercLinksWithBestConf]
* `--cut-off-value FLOAT`: Numeric value associated with the selected criterion. Ex: MinConf = 0.5, NumLinksWithBestConf = 10, PercLinksWithBestConf = 0.4  [default: 0.4]
* `--function TEXT`: A mathematical expression that defines a particular fitness function based on the weighted sum of several independent terms. Available terms: Quality, DegreeDistribution and Motifs.  [required]
* `--reference-point TEXT`: Reference point for the Pareto front. If specified, the search will be oriented towards this point. The format is 'f1;f2;f3'. [default: "-"]
* `--algorithm [GA|NSGAII|SMPSO]`: Evolutionary algorithm to be used during the optimization process. All are intended for a multi-objective approach with the exception of the genetic algorithm (GA).  [required]
* `--threads INTEGER`: Number of threads to be used during parallelization. By default, the maximum number of threads available in the system is used.  [default: 64]
* `--str-threads TEXT`: Comma-separated list with the identifying numbers of the threads to be used. If specified, the threads variable will automatically be set to the length of the list.
* `--plot-fitness-evolution / --no-plot-fitness-evolution`: Indicate if you want to represent the evolution of the fitness values.  [default: no-plot-fitness-evolution]
* `--plot-pareto-front / --no-plot-pareto-front`: Indicate if you want to represent the Pareto front (only available for multi-objective mode of 2 or 3 functions). [default: no-plot-pareto-front]
* `--plot-parallel-coordinates / --no-plot-parallel-coordinates`: Indicate if you want to represent the parallel coordinate graph (only available for multi-objective mode). [default: no-plot-parallel-coordinates]
* `--output-dir PATH`: Path to the output folder.  [default: inferred_networks]
* `--help`: Show this message and exit.

## `geneci optimize-ensemble`

Analyzes several trust lists and builds a consensus network by applying an evolutionary algorithm

**Usage**:

```console
$ geneci optimize-ensemble [OPTIONS]
```

**Options**:

* `--confidence-list TEXT`: Paths of the CSV files with the confidence lists to be agreed upon.  [required]
* `--gene-names PATH`: Path to the TXT file with the name of the contemplated genes separated by comma and without space. If not specified, only the genes specified in the lists of trusts will be considered.
* `--time-series PATH`: Path to the CSV file with the time series from which the individual gene networks have been inferred. This parameter is only necessary in case of specifying the fitness function Loyalty.
* `--crossover-probability FLOAT`: Crossover probability  [default: 0.9]
* `--num-parents INTEGER`: Number of parents  [default: 3]
* `--mutation-probability FLOAT`: Mutation probability. [default: 1/len(files)]
* `--mutation-strength FLOAT`: Mutation strength. [default: 0.1]
* `--population-size INTEGER`: Population size  [default: 100]
* `--num-evaluations INTEGER`: Number of evaluations  [default: 25000]
* `--cut-off-criteria [MinConf|NumLinksWithBestConf|PercLinksWithBestConf]`: Criteria for determining which links will be part of the final binary matrix.  [default: PercLinksWithBestConf]
* `--cut-off-value FLOAT`: Numeric value associated with the selected criterion. Ex: MinConf = 0.5, NumLinksWithBestConf = 10, PercLinksWithBestConf = 0.4  [default: 0.4]
* `--function TEXT`: A mathematical expression that defines a particular fitness function based on the weighted sum of several independent terms. Available terms: Quality, DegreeDistribution and Motifs.  [required]
* `--reference-point TEXT`: Reference point for the Pareto front. If specified, the search will be oriented towards this point. The format is 'f1;f2;f3'. [default: "-"]
* `--algorithm [GA|NSGAII|SMPSO]`: Evolutionary algorithm to be used during the optimization process. All are intended for a multi-objective approach with the exception of the genetic algorithm (GA).  [required]
* `--threads INTEGER`: Number of threads to be used during parallelization. By default, the maximum number of threads available in the system is used.  [default: 64]
* `--plot-fitness-evolution / --no-plot-fitness-evolution`: Indicate if you want to represent the evolution of the fitness values.  [default: no-plot-fitness-evolution]
* `--plot-pareto-front / --no-plot-pareto-front`: Indicate if you want to represent the Pareto front (only available for multi-objective mode of 2 or 3 functions). [default: no-plot-pareto-front]
* `--plot-parallel-coordinates / --no-plot-parallel-coordinates`: Indicate if you want to represent the parallel coordinate graph (only available for multi-objective mode). [default: no-plot-parallel-coordinates]
* `--output-dir PATH`: Path to the output folder.  [default: <<conf_list_path>>/../ea_consensus]
* `--help`: Show this message and exit.