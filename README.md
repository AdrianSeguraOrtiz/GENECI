# GENECI
GENECI (GEne NEtwork Consensus Inference) is a software package whose main functionality consists of an evolutionary algorithm to determine the optimal ensemble of machine learning techniques for genetic network inference based on the confidence levels and topological characteristics of its results.

![Alt text](./docs/diagram.svg)

# Example procedure

1. Generate .jar with dependencies:

```sh
cd EAGRN-JMetal
mvn clean compile assembly:single
cd ..
```

2. Generate docker images:

```sh
bash generate_images.sh
```

3. Download simulated expression data and their respective gold standards:

```sh
python EAGRN-Inference.py extract-data expression-data --database DREAM3 --database DREAM4 --database DREAM5 --database SynTReN --database Rogers --database GeneNetWeaver --database IRMA --username TFM-SynapseAccount --password TFM-SynapsePassword

python EAGRN-Inference.py extract-data gold-standard --database DREAM3 --database DREAM4 --database DREAM5 --database SynTReN --database Rogers --database GeneNetWeaver --database IRMA --username TFM-SynapseAccount --password TFM-SynapsePassword
```

4. Execute algorithm for a particular expression data set:

```sh
python EAGRN-Inference.py run --expression-data input_data/DREAM4/EXP/dream4_010_01_exp.csv --technique aracne --technique bc3net --technique c3net --technique clr --technique genie3_rf --technique genie3_gbm --technique genie3_et --technique mrnet --technique mrnetb --technique pcit --technique tigress --technique kboost
```

This process can also be divided into two parts:

4.1. Infer gene regulatory networks using available individual techniques:

```sh
python EAGRN-Inference.py infer-network --expression-data input_data/DREAM4/EXP/dream4_010_01_exp.csv --technique aracne --technique bc3net --technique c3net --technique clr --technique genie3_rf --technique genie3_gbm --technique genie3_et --technique mrnet --technique mrnetb --technique pcit --technique tigress --technique kboost
```

4.2. Optimise the assembly of the trusted lists resulting from the above command:

```sh
python EAGRN-Inference.py optimize-ensemble --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_ARACNE.csv --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_BC3NET.csv --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_C3NET.csv --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_CLR.csv --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_GENIE3_RF.csv --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_GENIE3_GBM.csv --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_GENIE3_ET.csv --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_MRNET.csv --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_MRNETB.csv --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_PCIT.csv --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_TIGRESS.csv --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_KBOOST.csv --gene-names inferred_networks/dream4_010_01_exp/gene_names.txt
```

5. Represent the inferred networks using both static 2D and interactive 3D plots that facilitate the study of intersections and comparisons between techniques:

```sh
python EAGRN-Inference.py draw-network --confidence-list inferred_networks/dream4_010_01_exp/ea_consensus_1/final_list.csv --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_ARACNE.csv --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_BC3NET.csv --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_C3NET.csv --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_CLR.csv --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_GENIE3_RF.csv --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_GENIE3_GBM.csv --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_GENIE3_ET.csv --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_MRNET.csv --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_MRNETB.csv --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_PCIT.csv --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_TIGRESS.csv --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_KBOOST.csv
```

6. Evaluate the accuracy of the inferred gene network against the gold standard:

```sh
# DREAM 3
python EAGRN-Inference.py extract-data evaluation-data --database DREAM3 --username TFM-SynapseAccount --password TFM-SynapsePassword

python EAGRN-Inference.py evaluate dream-prediction --challenge D3C4 --network-id 10_Yeast1 --synapse-file input_data/DREAM3/EVAL/PDF_InSilicoSize10_Yeast1.mat --synapse-file input_data/DREAM3/EVAL/DREAM3GoldStandard_InSilicoSize10_Yeast1.txt --confidence-list inferred_networks/InSilicoSize10-Yeast1-trajectories_exp/ea_consensus/final_list.csv

# DREAM 4
python EAGRN-Inference.py extract-data evaluation-data --database DREAM4 --username TFM-SynapseAccount --password TFM-SynapsePassword

python EAGRN-Inference.py evaluate dream-prediction --challenge D4C2 --network-id 10_1 --synapse-file input_data/DREAM4/EVAL/pdf_size10_1.mat --confidence-list inferred_networks/dream4_010_01_exp/ea_consensus/final_list.csv

# DREAM 5
python EAGRN-Inference.py extract-data evaluation-data --database DREAM5 --username TFM-SynapseAccount --password TFM-SynapsePassword

python EAGRN-Inference.py evaluate dream-prediction --challenge D5C4 --network-id 1 --synapse-file input_data/DREAM5/EVAL/DREAM5_NetworkInference_Edges_Network1.tsv --synapse-file input_data/DREAM5/EVAL/DREAM5_NetworkInference_GoldStandard_Network1.tsv --synapse-file input_data/DREAM5/EVAL/Network1_AUPR.mat --synapse-file input_data/DREAM5/EVAL/Network1_AUROC.mat --confidence-list inferred_networks/net1_exp/lists/GRN_ARACNE.csv
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

* `apply-cut`: Converts a list of confidence values into a...
* `draw-network`: Draw gene regulatory networks from confidence...
* `evaluate`: Evaluate the accuracy of the inferred network...
* `extract-data`: Extract data from different simulators and...
* `infer-network`: Infer gene regulatory networks from...
* `optimize-ensemble`: Analyzes several trust lists and builds a...
* `run`: Infer gene regulatory network from expression...

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