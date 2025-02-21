![CI](https://github.com/AdrianSeguraOrtiz/GENECI/actions/workflows/ci.yml/badge.svg)
![Release](https://github.com/AdrianSeguraOrtiz/GENECI/actions/workflows/release.yml/badge.svg)
![Pypi](https://img.shields.io/pypi/v/GENECI/3.0.1)
<img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>


<img src="https://github.com/AdrianSeguraOrtiz/GENECI/raw/v-3.0.1/docs/logo.png" width="40%" align="right" style="margin: 1em">

**BIO-INSIGHT (Biologically Informed Optimizator - INtegrating Software to Infer Grns by Holistic Thinking)** is a software package designed for intelligent consensus of multiple techniques for inferring gene regulation networks. Given the expression levels of different genes subjected to various perturbations, BIO-INSIGHT allows for the inference of the underlying network by applying in parallel a wide variety of known inference techniques and subsequently merging their results. To this end, a **parallel asynchronous many-objective evolutionary algorithm** is applied to optimize the weights assigned to the different techniques based on observed **confidence levels**, **topological characteristics** of the network, **network dynamics**, **detection of highly recurrent motifs** in real biological networks, **importance of interactions**, **contextualized analysis of graph metrics** and, in case of a time series as input, **maintenance of the loyalty** to it.

![Alt text](https://github.com/AdrianSeguraOrtiz/GENECI/raw/v-3.0.1/docs/diagram.svg)

BIO-INSIGHT offers the following **functionalities**: network inference using individual techniques, optimization of consensus across multiple solutions, construction of benchmark networks (from scratch or based on real networks), evaluation of accuracy concerning gold standards, network binarization algorithms, graphical representation of networks and optimization results, and modularized network segmentation.

To implement all the functionalities mentioned above, it has been necessary to program in multiple languages such as Java, Python, R, Matlab, Julia, etc. To integrate all the utilities into a single tool, it has been decided to **dockerize components** and use Python as the main means of orchestration. This, in addition to facilitating **task parallelization**, reduces the complexity of installation and requirements for our software package.

# Prerequisites

- Python == 3.10.7 
- Docker == 24.0.2

# Instalation

```sh
pip install geneci==3.0.1
```

# Output

To execute BIO-INSIGHT, the `run` command is provided with the file containing the **expression levels** of the genes that make up the network, the **list of techniques** to be agreed upon and the values of the different **algorithm parameters** in the event of not wishing to use those established by default. If more than one proposed objectives are used, the following folders are obtained after execution:

- `ea_consensus`: Evolutionary algorithm results.
    - `FUN.csv`: List with fitness values for each individual in the final population for each of the objective functions.
    - `VAR.csv`: List of winning weight vectors, i.e., individuals from the last generation.
    - `fitness_evolution.txt` and `fitness_evolution.html`: In each generation, the most optimal value found for each objective function is recorded. These values are stored in the text file and subsequently represented in graphs in HTML format.
    - `parallel_coordinates.html`: File containing a graphical representation of parallel coordinates. Each column refers to a specific objective function, and each horizontal line represents an individual from the final population. This graph is very useful to observe conflicts between different fitness functions in a multi-objective evolutionary algorithm.
    - `pareto_front.html`: If the number of objectives is less than or equal to 3 (n <= 3), the Pareto front is represented in an n-dimensional graph, where each axis corresponds to a different fitness function.
- `lists`: Set of networks inferred for each of the techniques before their consensus.
- `measurements/techniques_times.txt`: File containing the execution time taken by each technique.

# Integrated techniques

BIO-INSIGHT integrates the 26 inference techniques already contemplated in [MO-GENECI](https://github.com/AdrianSeguraOrtiz/MO-GENECI): [ARACNE](https://bmcbioinformatics.biomedcentral.com/articles/10.1186/1471-2105-7-S1-S7), [BC3NET](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0033624), [C3NET](https://bmcsystbiol.biomedcentral.com/articles/10.1186/1752-0509-4-132), [CLR]((https://pubmed.ncbi.nlm.nih.gov/17214507/)), [GENIE3_RF](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0012776), [GRNBOOST2](https://doi.org/10.1093/bioinformatics/bty916), [GENIE3_ET](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0012776), [MRNET](https://pubmed.ncbi.nlm.nih.gov/18354736/), [MRNETB](https://citeseerx.ist.psu.edu/viewdoc/download;jsessionid=5BF715493E925163623B3F3F6FE3EA88?doi=10.1.1.712.830&rep=rep1&type=pdf), [PCIT](https://pubmed.ncbi.nlm.nih.gov/18784117/), [TIGRESS](https://bmcsystbiol.biomedcentral.com/articles/10.1186/1752-0509-6-145), [KBOOST](https://www.nature.com/articles/s41598-021-94919-6), [MEOMI](https://doi.org/10.1093/bioinformatics/btac717), [JUMP3](https://doi.org/10.1093/bioinformatics/btu863), [NARROMI](https://doi.org/10.1093/bioinformatics/bts619), [CMI2NI](https://doi.org/10.1093/nar/gku1315), [RSNET](https://doi.org/10.1186/s12859-022-04696-w), [PCACMI](https://doi.org/10.1093/bioinformatics/btr626), [LOCPCACMI](https://doi.org/10.26599/TST.2018.9010097), [PLSNET](https://doi.org/10.1186/s12859-016-1398-6), [PIDC](https://doi.org/10.1016%2Fj.cels.2017.08.014), [PUC](https://doi.org/10.1016%2Fj.cels.2017.08.014), [GRNVBEM](https://doi.org/10.1093/bioinformatics/btx605), [LEAP](https://doi.org/10.1093/bioinformatics/btw729), [NONLINEARODES](https://doi.org/10.1093/bioinformatics/btaa032), [INFERELATOR](https://doi.org/10.1093/bioinformatics/btac117).

# Example procedure

1. **Obtain simulated expression data and their respective gold standards**. As in [MO-GENECI](https://github.com/AdrianSeguraOrtiz/MO-GENECI).

2. **Inference and consensus** of networks for the selected expression data. To perform this task, you can make use of the **run** command or proceed to an equivalent execution consisting of the **infer-network** and **optimize-ensemble** commands. This can be very useful when you need to incorporate external trust lists or run the evolutionary algorithm with different configurations on the same files, without the need to infer them several times.

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
           --function ReduceNonEssentialsInteractions --function Dynamicity \
           --function EigenVectorDistribution --algorithm NSGAII --plot-results \
           --output-dir inferred_networks
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
                         --function ReduceNonEssentialsInteractions --function Dynamicity \
                         --function EigenVectorDistribution --algorithm NSGAII --plot-results \
                         --output-dir inferred_networks/geneci_consensus
```

3. **Representation** of inferred networks using the **draw-network** command. As in [MO-GENECI](https://github.com/AdrianSeguraOrtiz/MO-GENECI).

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
* `plot-optimization`: Graph execution results. The evolution of Fitness functions, the Pareto front, the parallel coordinate graph and the chord diagram can be represented. In addition, all of them will be stored in files except the chord diagram, whose interactivity is too complex to be stored.
* `weighted-confidence`: Calculate the weighted sum of the confidence levels reported in several files based on a given distribution of weights.

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
* `--algorithm [GA|NSGAII|SMPSO]`: Evolutionary algorithm to be used during the optimization process. All are intended for a multi-objective approach with the exception of the genetic algorithm (GA).  [required]
* `--threads INTEGER`: Number of threads to be used during parallelization. By default, the maximum number of threads available in the system is used.  [default: 64]
* `--plot-results / --no-plot-results`: Indicate if you want to represent results graphically. [default: --plot-results]
* `--output-dir PATH`: Path to the output folder.  [default: <<conf_list_path>>/../ea_consensus]
* `--help`: Show this message and exit.

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
* `--algorithm [GA|NSGAII|SMPSO]`: Evolutionary algorithm to be used during the optimization process. All are intended for a multi-objective approach with the exception of the genetic algorithm (GA).  [required]
* `--threads INTEGER`: Number of threads to be used during parallelization. By default, the maximum number of threads available in the system is used.  [default: 64]
* `--str-threads TEXT`: Comma-separated list with the identifying numbers of the threads to be used. If specified, the threads variable will automatically be set to the length of the list.
* `--plot-results / --no-plot-results`: Indicate if you want to represent results graphically. [default: --plot-results]
* `--output-dir PATH`: Path to the output folder.  [default: inferred_networks]
* `--help`: Show this message and exit.