# Memetic-GENECI

![CI](https://github.com/AdrianSeguraOrtiz/GENECI/actions/workflows/ci.yml/badge.svg)
![Release](https://github.com/AdrianSeguraOrtiz/GENECI/actions/workflows/release.yml/badge.svg)
![Pypi](https://img.shields.io/pypi/v/GENECI/1.5.2)
<img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>

[Memetic-GENECI](https://github.com/AdrianSeguraOrtiz/Memetic-GENECI) is a software package derived from [Single-GENECI (GEne NEtwork Consensus Inference)](https://github.com/AdrianSeguraOrtiz/Single-GENECI) that incorporates an additional **local search** phase to guide the evolution of individuals based on **known interactions**. Injection of domain expert knowledge has been shown to improve the accuracy with which Single-GENECI optimises consensus between different gene regulatory network inference techniques.

<div align="center"><img src="https://github.com/AdrianSeguraOrtiz/GENECI/raw/v-1.5.1/docs/diagram.svg"></div>

# Prerequisites

- Python => 3.9
- Docker

# Instalation

```sh
pip install geneci==1.5.2
```

# Integrated techniques

The same as those contemplated in [Single-GENECI](https://github.com/AdrianSeguraOrtiz/Single-GENECI)

# Example procedure

1. **Download simulated expression data and their respective gold standards**. As in [Single-GENECI](https://github.com/AdrianSeguraOrtiz/Single-GENECI)

2. **Inference and consensus** of networks for the selected expression data. Unlike in [Single-GENECI](https://github.com/AdrianSeguraOrtiz/Single-GENECI) in this case a list of known interactions can be specified via the `--known-interactions` parameter by providing a txt or csv file with the following structure:

```txt
G1,G2,1
G1,G3,1
G3,G4,1
...
```

In addition, the `--memetic-distance-type` parameter is also incorporated to consider **one**, **some** or **all** of the known interactions in each iteration of the local search phase, and the `--memetic-probability` parameter to determine the probability with which an individual is subjected to it.

- **Form 1**: Procedure prefixed by the command run

```sh
geneci run --expression-data input_data/DREAM4/EXP/dream4_010_01_exp.csv \
           --technique aracne --technique bc3net --technique c3net \
           --technique clr --technique genie3_rf --technique genie3_gbm \
           --technique genie3_et --technique mrnet --technique mrnetb \
           --technique pcit --technique tigress --technique kboost \
           --known-interactions known_interactions.txt --memetic-distance-type all \
           --memetic-probability 0.5
```

- **Form 2**: Division of the procedure into several commands

```sh
# 1. Inference using individual techniques
geneci infer-network --expression-data input_data/DREAM4/EXP/dream4_010_01_exp.csv \
                     --technique aracne --technique bc3net --technique c3net --technique clr --technique mrnet \
                     --technique mrnetb --technique genie3_rf --technique genie3_gbm --technique genie3_et \
                     --technique pcit --technique tigress --technique kboost

# 2. Optimize the assembly of the trust lists resulting from the above command
geneci optimize-ensemble --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_ARACNE.csv \
                         --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_BC3NET.csv \
                         --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_C3NET.csv \
                         --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_CLR.csv \
                         --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_GENIE3_RF.csv \
                         --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_GENIE3_GBM.csv \
                         --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_GENIE3_ET.csv \
                         --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_MRNET.csv \
                         --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_MRNETB.csv \
                         --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_PCIT.csv \
                         --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_TIGRESS.csv \
                         --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_KBOOST.csv \
                         --gene-names inferred_networks/dream4_010_01_exp/gene_names.txt \
                         --known-interactions known_interactions.txt --memetic-distance-type all \
                         --memetic-probability 0.5
```

3. **Representation** of inferred networks. As in [Single-GENECI](https://github.com/AdrianSeguraOrtiz/Single-GENECI)
4. **Evaluation** of the quality of the inferred gene network with respect to the gold standard. As in [Single-GENECI](https://github.com/AdrianSeguraOrtiz/Single-GENECI)
5. **Binarization** of the inferred gene network. As in [Single-GENECI](https://github.com/AdrianSeguraOrtiz/Single-GENECI)


# CLI

**Usage**:

```console
$ [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `apply-cut`: Converts a list of confidence values into a binary matrix that represents the final gene network.
* `draw-network`: Draw gene regulatory networks from confidence lists.
* `evaluate`: Evaluate the accuracy of the inferred network with respect to its gold standard.
* `extract-data`: Extract data from different simulators and known challenges. These include DREAM3, DREAM4, DREAM5, SynTReN, Rogers, GeneNetWeaver and IRMA.
* `infer-network`: Infer gene regulatory networks from expression data. Several techniques are available: ARACNE, BC3NET, C3NET, CLR, GENIE3, MRNET, MRNET, MRNETB and PCIT.
* `optimize-ensemble`: Analyzes several trust lists and builds a consensus network by applying an evolutionary algorithm.
* `run`: Infer gene regulatory network from expression data by employing multiple unsupervised learning techniques and applying a genetic algorithm for consensus optimization.

Only modified command specifications are shown with respect to [Single-GENECI](https://github.com/AdrianSeguraOrtiz/Single-GENECI)

## `run`

Infer gene regulatory network from expression data by employing multiple unsupervised learning techniques and applying a genetic algorithm for consensus optimization.

**Usage**:

```console
$ run [OPTIONS]
```

**Options**:

* `--expression-data PATH`: Path to the CSV file with the expression data. Genes are distributed in rows and experimental conditions (time series) in columns.  [required]
* `--known-interactions PATH`: Path to the CSV file with the known interactions between genes. If specified, a local search process will be performed during the repair [default: None].
* `--technique [ARACNE|BC3NET|C3NET|CLR|GENIE3_RF|GENIE3_GBM|GENIE3_ET|MRNET|MRNETB|PCIT|TIGRESS|KBOOST]`: Inference techniques to be performed.  [required]
* `--crossover [SBXCrossover|BLXAlphaCrossover|DifferentialEvolutionCrossover|NPointCrossover|NullCrossover|WholeArithmeticCrossover]`: Crossover operator  [default: SBXCrossover]
* `--crossover-probability FLOAT`: Crossover probability  [default: 0.9]
* `--mutation [PolynomialMutation|CDGMutation|GroupedAndLinkedPolynomialMutation|GroupedPolynomialMutation|LinkedPolynomialMutation|NonUniformMutation|NullMutation|SimpleRandomMutation|UniformMutation]`: Mutation operator  [default: PolynomialMutation]
* `--mutation-probability FLOAT`: Mutation probability. [default: 1/len(files)]
* `--repairer [StandardizationRepairer|GreedyRepair]`: Solution repairer to keep the sum of weights equal to 1  [default: StandardizationRepairer]
* `--memetic-distance-type [all|some|one]`: Memetic distance type [default: MemeticDistanceType.all]
* `--memetic-probability FLOAT`: Memetic probability [default: 0.55]
* `--population-size INTEGER`: Population size  [default: 100]
* `--num-evaluations INTEGER`: Number of evaluations  [default: 25000]
* `--cut-off-criteria [MinConfidence|MaxNumLinksBestConf|MinConfDist]`: Criteria for determining which links will be part of the final binary matrix.  [default: MinConfDist]
* `--cut-off-value FLOAT`: Numeric value associated with the selected criterion. Ex: MinConfidence = 0.5, MaxNumLinksBestConf = 10, MinConfDist = 0.2  [default: 0.5]
* `--quality-weight FLOAT`: Weight associated with the first term of the fitness function. This term tries to maximize the quality of good links (improve trust and frequency of appearance) while minimizing their quantity. It tries to establish some contrast between good and bad links so that the links finally reported are of high reliability.  [default: 0.75]
* `--topology-weight FLOAT`: Weight associated with the second term of the fitness function. This term tries to increase the degree (number of links) of those genes with a high potential to be considered as hubs. At the same time, it is intended that the number of genes that meet this condition should be relatively low, since this is what is usually observed in real gene networks. The objective is to promote the approximation of the network to a scale-free configuration and to move away from random structure.  [default: 0.25]
* `--threads INTEGER`: Number of threads to be used during parallelization. By default, the maximum number of threads available in the system is used.  [default: 8]
* `--graphics / --no-graphics`: Indicate if you want to represent the evolution of the fitness value.  [default: True]
* `--output-dir PATH`: Path to the output folder.  [default: inferred_networks]
* `--help`: Show this message and exit.

## `optimize-ensemble`

Analyzes several trust lists and builds a consensus network by applying an evolutionary algorithm

**Usage**:

```console
$ optimize-ensemble [OPTIONS]
```

**Options**:

* `--confidence-list TEXT`: Paths of the CSV files with the confidence lists to be agreed upon.  [required]
* `--known-interactions PATH`: Path to the CSV file with the known interactions between genes. If specified, a local search process will be performed during the repair [default: None].
* `--gene-names PATH`: Path to the TXT file with the name of the contemplated genes separated by comma and without space. If not specified, only the genes specified in the lists of trusts will be considered.
* `--crossover [SBXCrossover|BLXAlphaCrossover|DifferentialEvolutionCrossover|NPointCrossover|NullCrossover|WholeArithmeticCrossover]`: Crossover operator  [default: SBXCrossover]
* `--crossover-probability FLOAT`: Crossover probability  [default: 0.9]
* `--mutation [PolynomialMutation|CDGMutation|GroupedAndLinkedPolynomialMutation|GroupedPolynomialMutation|LinkedPolynomialMutation|NonUniformMutation|NullMutation|SimpleRandomMutation|UniformMutation]`: Mutation operator  [default: PolynomialMutation]
* `--mutation-probability FLOAT`: Mutation probability. [default: 1/len(files)]
* `--repairer [StandardizationRepairer|GreedyRepair]`: Solution repairer to keep the sum of weights equal to 1  [default: StandardizationRepairer]
* `--memetic-distance-type [all|some|one]`: Memetic distance type [default: MemeticDistanceType.all]
* `--memetic-probability FLOAT`: Memetic probability [default: 0.55]
* `--population-size INTEGER`: Population size  [default: 100]
* `--num-evaluations INTEGER`: Number of evaluations  [default: 25000]
* `--cut-off-criteria [MinConfidence|MaxNumLinksBestConf|MinConfDist]`: Criteria for determining which links will be part of the final binary matrix.  [default: MinConfDist]
* `--cut-off-value FLOAT`: Numeric value associated with the selected criterion. Ex: MinConfidence = 0.5, MaxNumLinksBestConf = 10, MinConfDist = 0.2  [default: 0.5]
* `--quality-weight FLOAT`: Weight associated with the first term of the fitness function. This term tries to maximize the quality of good links (improve trust and frequency of appearance) while minimizing their quantity. It tries to establish some contrast between good and bad links so that the links finally reported are of high reliability.  [default: 0.75]
* `--topology-weight FLOAT`: Weight associated with the second term of the fitness function. This term tries to increase the degree (number of links) of those genes with a high potential to be considered as hubs. At the same time, it is intended that the number of genes that meet this condition should be relatively low, since this is what is usually observed in real gene networks. The objective is to promote the approximation of the network to a scale-free configuration and to move away from random structure.  [default: 0.25]
* `--threads INTEGER`: Number of threads to be used during parallelization. By default, the maximum number of threads available in the system is used.  [default: 8]
* `--graphics / --no-graphics`: Indicate if you want to represent the evolution of the fitness value.  [default: True]
* `--output-dir PATH`: Path to the output folder.  [default: <<conf_list_path>>/../ea_consensus]
* `--help`: Show this message and exit.