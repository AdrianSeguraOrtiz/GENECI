# GENECI

![CI](https://github.com/AdrianSeguraOrtiz/GENECI/actions/workflows/ci.yml/badge.svg)
![Release](https://github.com/AdrianSeguraOrtiz/GENECI/actions/workflows/release.yml/badge.svg)
![Pypi](https://img.shields.io/pypi/v/GENECI)
![License](https://img.shields.io/apm/l/GENECI)
<img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>

GENECI (GEne NEtwork Consensus Inference) is a software package whose main functionality consists of an evolutionary algorithm to determine the optimal ensemble of machine learning techniques for genetic network inference based on the confidence levels and topological characteristics of its results.

![Alt text](https://github.com/AdrianSeguraOrtiz/GENECI/raw/main/docs/diagram.svg)

# Prerequisites

- Python => 3.9
- Docker

# Instalation

```sh
pip install geneci
```

# Example procedure

1. **Download simulated expression data and their respective gold standards**. For this purpose, the **extract-data** command is used with the subcommands expression-data and gold-standard, to which the database and the output folder are specified:

```sh
# Expression data
geneci extract-data expression-data --database DREAM4

# Gold standard
geneci extract-data gold-standard --database DREAM4
```

2. **Inference and consensus** of networks for the selected expression data. To perform this task, you can make use of the **run** command or proceed to an equivalent execution consisting of the **infer-network** and **optimize-ensemble** commands. This can be very useful when you need to incorporate external trust lists or run the evolutionary algorithm with different configurations on the same files, without the need to infer them several times.

- **Form 1**: Procedure prefixed by the command run

```sh
geneci run --expression-data input_data/DREAM4/EXP/dream4_010_01_exp.csv \
           --technique aracne --technique bc3net --technique c3net \
           --technique clr --technique genie3_rf --technique genie3_gbm \
           --technique genie3_et --technique mrnet --technique mrnetb \
           --technique pcit --technique tigress --technique kboost
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
                         --gene-names inferred_networks/dream4_010_01_exp/gene_names.txt
```

3. **Representation** of inferred networks using the **draw-network** command:

```sh
geneci draw-network --confidence-list inferred_networks/dream4_010_01_exp/ea_consensus/final_list.csv \
                    --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_ARACNE.csv \
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
                    --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_KBOOST.csv
```

4. **Evaluation** of the quality of the inferred gene network with respect to the gold standard. To do this, the evaluation data is previously downloaded with the **extract-data** command and the **evaluation-data** subcommand, which is provided with the database and the credentials of an account on the Synapse platform. After that, the **evaluate** command is executed with the subcommand **dream-prediction** to which the challenge identifier, the network identifier and the path to the evaluation files are given:

```sh
# 1. Download evaluation data
geneci extract-data evaluation-data --database DREAM4 --username TFM-SynapseAccount --password TFM-SynapsePassword

# 2. Evaluate the accuracy of the inferred consensus network.
geneci evaluate dream-prediction --challenge D4C2 --network-id 10_1 \
                                 --synapse-file input_data/DREAM4/EVAL/pdf_size10_1.mat \
                                 --confidence-list inferred_networks/dream4_010_01_exp/ea_consensus/final_list.csv
```

5. **Binarization** of the inferred gene network. In many cases, it is useful to apply a cutoff criterion to convert a list of confidence values into a real network that asserts the specific interaction between genes. For this purpose, the **apply-cut** command is used, which is provided with the list of confidence values, the cutoff criterion and its corresponding threshold value.

```sh
geneci apply-cut --confidence-list inferred_networks/dream4_010_01_exp/ea_consensus/final_list.csv \
                 --cut-off-criteria MinConfidence --cut-off-value 0.2
```

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

## `apply-cut`

Converts a list of confidence values into a binary matrix that represents the final gene network.

**Usage**:

```console
$ apply-cut [OPTIONS]
```

**Options**:

* `--confidence-list PATH`: Path to the CSV file with the list of trusted values.  [required]
* `--gene-names PATH`: Path to the TXT file with the name of the contemplated genes separated by comma and without space. If not specified, only the genes specified in the list of trusts will be considered.
* `--cut-off-criteria [MinConfidence|MaxNumLinksBestConf]`: Criteria for determining which links will be part of the final binary matrix.  [required]
* `--cut-off-value FLOAT`: Numeric value associated with the selected criterion. Ex: MinConfidence = 0.5, MaxNumLinksBestConf = 10  [required]
* `--output-file PATH`: Path to the output CSV file that will contain the binary matrix resulting from the cutting operation.  [default: <<conf_list_path>>/../networks/<<conf_list_name>>.csv]
* `--help`: Show this message and exit.

## `draw-network`

Draw gene regulatory networks from confidence lists.

**Usage**:

```console
$ draw-network [OPTIONS]
```

**Options**:

* `--confidence-list TEXT`: Paths of the CSV files with the confidence lists to be represented  [required]
* `--mode [Static2D|Interactive3D|Both]`: Mode of representation  [default: Both]
* `--nodes-distribution [Spring|Circular|Kamada_kawai]`: Node distribution in graph  [default: Spring]
* `--output-folder TEXT`: Path to output folder  [default: <<conf_list_path>>/../network_graphics]
* `--help`: Show this message and exit.

## `evaluate`

Evaluate the accuracy of the inferred network with respect to its gold standard.

**Usage**:

```console
$ evaluate [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `dream-prediction`: Evaluate the accuracy with which networks...
* `generic-prediction`: Evaluate the accuracy with which any generic...

### `evaluate dream-prediction`

Evaluate the accuracy with which networks belonging to the DREAM challenges are predicted.

**Usage**:

```console
$ evaluate dream-prediction [OPTIONS]
```

**Options**:

* `--challenge [D3C4|D4C2|D5C4]`: DREAM challenge to which the inferred network belongs  [required]
* `--network-id TEXT`: Predicted network identifier. Ex: 10_1  [required]
* `--synapse-file PATH`: Paths to files from synapse needed to perform inference evaluation. To download these files you need to register at https://www.synapse.org/# and download them manually or run the command extract-data evaluation-data.  [required]
* `--confidence-list PATH`: Path to the CSV file with the list of trusted values.  [required]
* `--help`: Show this message and exit.

### `evaluate generic-prediction`

Evaluate the accuracy with which any generic network has been predicted with respect to a given gold standard. To do so, it approaches the case as a binary classification problem between 0 and 1.

**Usage**:

```console
$ evaluate generic-prediction [OPTIONS]
```

**Options**:

* `--inferred-binary-matrix PATH`: [required]
* `--gs-binary-matrix PATH`: [required]
* `--help`: Show this message and exit.

## `extract-data`

Extract data from different simulators and known challenges. These include DREAM3, DREAM4, DREAM5, SynTReN, Rogers, GeneNetWeaver and IRMA.

**Usage**:

```console
$ extract-data [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `evaluation-data`: Download evaluation data from various DREAM...
* `expression-data`: Download differential expression data from...
* `gold-standard`: Download gold standards from various...

### `extract-data evaluation-data`

Download evaluation data from various DREAM challenges.

**Usage**:

```console
$ extract-data evaluation-data [OPTIONS]
```

**Options**:

* `--database [DREAM3|DREAM4|DREAM5]`: Databases for downloading evaluation data.  [required]
* `--output-dir PATH`: Path to the output folder.  [default: input_data]
* `--username TEXT`: Synapse account username.  [required]
* `--password TEXT`: Synapse account password.  [required]
* `--help`: Show this message and exit.

### `extract-data expression-data`

Download differential expression data from various databases such as DREAM3, DREAM4, DREAM5, SynTReN, Rogers, GeneNetWeaver and IRMA.

**Usage**:

```console
$ extract-data expression-data [OPTIONS]
```

**Options**:

* `--database [DREAM3|DREAM4|DREAM5|SynTReN|Rogers|GeneNetWeaver|IRMA]`: Databases for downloading expression data.  [required]
* `--output-dir PATH`: Path to the output folder.  [default: input_data]
* `--username TEXT`: Synapse account username. Only necessary when selecting DREAM3 or DREAM5.
* `--password TEXT`: Synapse account password. Only necessary when selecting DREAM3 or DREAM5.
* `--help`: Show this message and exit.

### `extract-data gold-standard`

Download gold standards from various databases such as DREAM3, DREAM4, DREAM5, SynTReN, Rogers, GeneNetWeaver and IRMA.

**Usage**:

```console
$ extract-data gold-standard [OPTIONS]
```

**Options**:

* `--database [DREAM3|DREAM4|DREAM5|SynTReN|Rogers|GeneNetWeaver|IRMA]`: Databases for downloading gold standards.  [required]
* `--output-dir PATH`: Path to the output folder.  [default: input_data]
* `--username TEXT`: Synapse account username. Only necessary when selecting DREAM3 or DREAM5.
* `--password TEXT`: Synapse account password. Only necessary when selecting DREAM3 or DREAM5.
* `--help`: Show this message and exit.

## `infer-network`

Infer gene regulatory networks from expression data. Several techniques are available: ARACNE, BC3NET, C3NET, CLR, GENIE3, MRNET, MRNET, MRNETB and PCIT.

**Usage**:

```console
$ infer-network [OPTIONS]
```

**Options**:

* `--expression-data PATH`: Path to the CSV file with the expression data. Genes are distributed in rows and experimental conditions (time series) in columns.  [required]
* `--technique [ARACNE|BC3NET|C3NET|CLR|GENIE3_RF|GENIE3_GBM|GENIE3_ET|MRNET|MRNETB|PCIT|TIGRESS|KBOOST]`: Inference techniques to be performed.  [required]
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
* `--gene-names PATH`: Path to the TXT file with the name of the contemplated genes separated by comma and without space. If not specified, only the genes specified in the lists of trusts will be considered.
* `--crossover [SBXCrossover|BLXAlphaCrossover|DifferentialEvolutionCrossover|NPointCrossover|NullCrossover|WholeArithmeticCrossover]`: Crossover operator  [default: SBXCrossover]
* `--crossover-probability FLOAT`: Crossover probability  [default: 0.9]
* `--mutation [PolynomialMutation|CDGMutation|GroupedAndLinkedPolynomialMutation|GroupedPolynomialMutation|LinkedPolynomialMutation|NonUniformMutation|NullMutation|SimpleRandomMutation|UniformMutation]`: Mutation operator  [default: PolynomialMutation]
* `--mutation-probability FLOAT`: Mutation probability. [default: 1/len(files)]
* `--repairer [StandardizationRepairer|GreedyRepair]`: Solution repairer to keep the sum of weights equal to 1  [default: StandardizationRepairer]
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

## `run`

Infer gene regulatory network from expression data by employing multiple unsupervised learning techniques and applying a genetic algorithm for consensus optimization.

**Usage**:

```console
$ run [OPTIONS]
```

**Options**:

* `--expression-data PATH`: Path to the CSV file with the expression data. Genes are distributed in rows and experimental conditions (time series) in columns.  [required]
* `--technique [ARACNE|BC3NET|C3NET|CLR|GENIE3_RF|GENIE3_GBM|GENIE3_ET|MRNET|MRNETB|PCIT|TIGRESS|KBOOST]`: Inference techniques to be performed.  [required]
* `--crossover [SBXCrossover|BLXAlphaCrossover|DifferentialEvolutionCrossover|NPointCrossover|NullCrossover|WholeArithmeticCrossover]`: Crossover operator  [default: SBXCrossover]
* `--crossover-probability FLOAT`: Crossover probability  [default: 0.9]
* `--mutation [PolynomialMutation|CDGMutation|GroupedAndLinkedPolynomialMutation|GroupedPolynomialMutation|LinkedPolynomialMutation|NonUniformMutation|NullMutation|SimpleRandomMutation|UniformMutation]`: Mutation operator  [default: PolynomialMutation]
* `--mutation-probability FLOAT`: Mutation probability. [default: 1/len(files)]
* `--repairer [StandardizationRepairer|GreedyRepair]`: Solution repairer to keep the sum of weights equal to 1  [default: StandardizationRepairer]
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