# Single-GENECI

![CI](https://github.com/AdrianSeguraOrtiz/GENECI/actions/workflows/ci.yml/badge.svg)
![Release](https://github.com/AdrianSeguraOrtiz/GENECI/actions/workflows/release.yml/badge.svg)
![Pypi](https://img.shields.io/pypi/v/GENECI/1.0.2)
<img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>

[Single-GENECI (GEne NEtwork Consensus Inference)](https://github.com/AdrianSeguraOrtiz/Single-GENECI) is a software package whose main functionality consists of an evolutionary algorithm to determine the optimal ensemble of machine learning techniques for genetic network inference based on the confidence levels and topological characteristics of its results.

![Alt text](https://github.com/AdrianSeguraOrtiz/GENECI/raw/v-1.0.1/docs/diagram.svg)

# Prerequisites

- Python => 3.9
- Docker

# Instalation

```sh
pip install geneci==1.0.2
```

# Integrated techniques

* **ARACNE**: [Algorithm for the Reconstruction of Accurate Cellular NEtworks (ARACNE)](https://bmcbioinformatics.biomedcentral.com/articles/10.1186/1471-2105-7-S1-S7) bases the identification of interactions on a pairwise correlation coefficient called mutual information. This coefficient measures the information or uncertainty reduction (entropy) of a random variable as a consequence of knowing the value of another. After obtaining a series of candidate interactions, this tool carries out a filtering process by applying a statistical threshold whose calculation is based on the Relevance Networks method. Finally, in order to eliminate false positives caused by indirect relationships in the network, ARACNE reviews all the triplets passed by the filter and uses the [data processing inequality property (DPI)](https://arxiv.org/abs/1107.0740v2) to eliminate the interaction with the least mutual information.

* **C3NET**: [Conservative Causal Core NETwork (C3NET)](https://bmcsystbiol.biomedcentral.com/articles/10.1186/1752-0509-4-132) again uses the mutual information coefficient to detect candidate connections. However, in its second phase it applies a rather demanding filtering process where only the most significant interaction of each gene is finally selected. This connection corresponds to the one with the highest mutual information value among the neighboring relationships of a gene. Therefore, each gene can only contribute one interaction to the list and therefore the maximum number of connections that C3NET can report is equivalent to the number of genes in the network. The purpose of this procedure is to ensure high reliability of the links exposed in the output network, providing a solid skeleton where the presence of false negatives is preferred over the usual number of false positives.

* **BC3NET**: [Bagging C3NET (BC3NET)](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0033624) attempts to alleviate the limitations imposed by the filtering process of the previous algorithm. Their approach is to generate several versions of the input data using a nonparametric bootstrap and apply the C3NET algorithm to each of these versions. This provides an ensemble of binary gene networks that are subsequently consensualized into a single network of weights.

* **CLR**: [Context Likelihood or Relatedness network (CLR)](https://pubmed.ncbi.nlm.nih.gov/17214507/) applies in the first instance the same procedure as the previous techniques, i.e. it calculates the mutual information coefficients in order to select candidate connections. However, this technique introduces an intermediate step before filtering, aimed at eliminating spurious correlations and indirect interactions. For this purpose, it calculates the statistical probability of each mutual information value within the context of its network, i.e. it performs a normalization process. This, in addition to eliminating possible false positives, corrects errors caused by inadequate or unequal sampling.

* **GENIE3**: [GEne Network Inference with Ensemble of trees (GENIE3)](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0012776) decomposes the problem of inferring a network of n genes into n different regression subproblems. In each of them the algorithm must construct a function that allows explaining the expression profile of the current gene as a function of the rest. The coefficients assigned to the other genes in this function are taken as confidence indicators, so that if the expression of the target gene is highly dependent on the expression of a particular gene, it follows that the two genes are clearly connected in the network.

* **KBOOST**: [kernel PCA regression and gradient boosting to reconstruct gene regulatory networks (KBOOST)](https://www.nature.com/articles/s41598-021-94919-6) like GENIE3, divides the inference problem for each gene present in the network. In each subproblem, a mathematical model is built to predict the expression of the target gene using [kernel principal component analysis (KPCA)](https://link.springer.com/chapter/10.1007/BFb0020217) on the expression levels of a likely subset of transcription factors. Different models are then compared and the probability of one gene regulating another is estimated using [Bayesian Model Averaging (BMA)](https://www.tandfonline.com/doi/abs/10.1080/01621459.1997.10473615).

* **MRNET**: [Minimum Redundancy NETworks (MRNET)](https://pubmed.ncbi.nlm.nih.gov/18354736/) proposes to perform network inference using the [Maximum Relevance Minimum Redundancy (MRMR) feature selection method](https://pubmed.ncbi.nlm.nih.gov/15852500/). This method is applied using a forward selection strategy, which implies that the procedure is strongly conditioned by the first variables selected. For each pair of genes evaluated during the course of the algorithm, this tool performs two calculations. First, it calculates the relevance of their connection, i.e. the mutual information coefficient seen so far. And secondly, it assigns a redundancy value, which corresponds to the average mutual information with respect to the previously ranked variables. After that, the optimization algorithm selects those interactions that simultaneously have a high relevance and a low redundancy. The purpose of this filtering is to eliminate false positives caused by indirect connections in the network, since although these cases have good mutual information (relevance), their level of redundancy will also be high, which will lead to their discrimination in the final list.

* **MRNETB**: [Minimum Redundancy NETworks using Backward elimination (MRNETB)](https://citeseerx.ist.psu.edu/viewdoc/download;jsessionid=5BF715493E925163623B3F3F6FE3EA88?doi=10.1.1.712.830&rep=rep1&type=pdf) replaces the forward selection strategy seen in the MRNET technique with a backward elimination procedure combined with sequential replacement. The objective lies in removing the limitation discussed in the previous technique with respect to the first variables selected. Instead, MRNETB starts with the set of all available variables and then discards at each step the one whose elimination leads to a larger increase of the objective function. In addition, in order to refine this strategy, a sequential replacement operator is introduced that takes care of exchanging the state of a selected and an unselected variable in order to further increase the fitness function output.

* **PCIT**: [Partial Correlation coefficient with Information Theory (PCIT)](https://pubmed.ncbi.nlm.nih.gov/18784117/) identifies candidate interactions between genes by applying partial correlation coefficients combined with an information theory approach. For each trio of genes, the algorithm calculates the three first-order partial correlation coefficients and then applies the [data processing inequality theorem (DPI)](https://arxiv.org/abs/1107.0740v2) from information theory. This allows you to obtain a local tolerance level that is then used as a threshold during filtering.

* **TIGRESS**: [Trustful Inference of Gene REgulation with Stability Selection (TIGRESS)](https://bmcsystbiol.biomedcentral.com/articles/10.1186/1752-0509-6-145) divides the inference problem into regression subproblems in a manner similar to that seen in GENIE3 and KBOOST. That is, for each gene, a function must be constructed to explain its expression profile as a function of the others. TIGRESS employs the LARS method during feature selection, which unlike other methods does not completely re-optimize the fitted model after each incorporation, but only partially refines it. However, [LARS](https://projecteuclid.org/journals/annals-of-statistics/volume-32/issue-2/Least-angle-regression/10.1214/009053604000000067.short) has proven to be quite sensitive to data with high levels of correlation and does not allow to extract scores about the relevance of each gene in target function. Therefore, TIGRESS incorporates the [stability selection procedure](https://rss.onlinelibrary.wiley.com/doi/10.1111/j.1467-9868.2010.00740.x), which iteratively runs the above method on randomly perturbed data and scores each feature based on the number of times it has been selected.

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