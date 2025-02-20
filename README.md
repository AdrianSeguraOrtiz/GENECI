![CI](https://github.com/AdrianSeguraOrtiz/GENECI/actions/workflows/ci.yml/badge.svg)
![Release](https://github.com/AdrianSeguraOrtiz/GENECI/actions/workflows/release.yml/badge.svg)
![Pypi](https://img.shields.io/pypi/v/GENECI/2.0.2)

[MO-GENECI (Multi-Objective GEne NEtwork Consensus Inference)](https://github.com/AdrianSeguraOrtiz/MO-GENECI) is a software package derived from [Single-GENECI](https://github.com/AdrianSeguraOrtiz/Single-GENECI) designed for intelligent consensus of multiple techniques for inferring gene regulation networks. Given the expression levels of different genes subjected to various perturbations, MO-GENECI allows for the inference of the underlying network by applying in parallel a wide variety of known inference techniques and subsequently merging their results. To this end, a **multi-objective evolutionary algorithm** is applied to optimize the weights assigned to the different techniques based on observed **confidence levels**, **topological characteristics** of the network and **detection of highly recurrent motifs** in real biological networks.

![Alt text](https://github.com/AdrianSeguraOrtiz/GENECI/raw/v-2.0.1/docs/diagram.svg)

MO-GENECI offers the following **functionalities**: network inference using individual techniques, optimization of consensus across multiple solutions, construction of benchmark networks (from scratch or based on real networks), evaluation of accuracy concerning gold standards, network binarization algorithms, and graphical representation.

To implement all the functionalities mentioned above, it has been necessary to program in multiple languages such as Java, Python, R, Matlab, Julia, etc. To integrate all the utilities into a single tool, it has been decided to **dockerize components** and use Python as the main means of orchestration. This, in addition to facilitating **task parallelization**, reduces the complexity of installation and requirements for our software package.

# Prerequisites

- Python => 3.9
- Docker

# Instalation

```sh
pip install geneci==2.0.2
```

# Output

To execute MO-GENECI, the `run` command is provided with the file containing the expression levels of the genes that make up the network, the list of techniques to be agreed upon and the values of the different algorithm parameters in the event of not wishing to use those established by default. If the three proposed objectives are used, the following files are obtained after execution:

- `FUN.csv`: List with fitness values for each individual in the final population for each of the objective functions.
- `VAR.csv`: List of winning weight vectors, i.e., individuals from the last generation.
- `fitness_evolution.txt` and `fitness_evolution.html`: In each generation, the most optimal value found for each objective function is recorded. These values are stored in the text file and subsequently represented in graphs in HTML format.
- `parallel_coordinates.html`: File containing a graphical representation of parallel coordinates. Each column refers to a specific objective function, and each horizontal line represents an individual from the final population. This graph is very useful to observe conflicts between different fitness functions in a multi-objective evolutionary algorithm.
- `pareto_front.html`: Pareto front represented in a three-dimensional graph, where each axis refers to a different fitness function.

# Integrated techniques

* **ARACNE**: [Algorithm for the Reconstruction of Accurate Cellular NEtworks (ARACNE)](https://bmcbioinformatics.biomedcentral.com/articles/10.1186/1471-2105-7-S1-S7) bases the identification of interactions on a pairwise correlation coefficient called mutual information. This coefficient measures the information or uncertainty reduction (entropy) of a random variable as a consequence of knowing the value of another. After obtaining a series of candidate interactions, this tool carries out a filtering process by applying a statistical threshold whose calculation is based on the Relevance Networks method. Finally, in order to eliminate false positives caused by indirect relationships in the network, ARACNE reviews all the triplets passed by the filter and uses the [data processing inequality property (DPI)](https://arxiv.org/abs/1107.0740v2) to eliminate the interaction with the least mutual information.

* **C3NET**: [Conservative Causal Core NETwork (C3NET)](https://bmcsystbiol.biomedcentral.com/articles/10.1186/1752-0509-4-132) again uses the mutual information coefficient to detect candidate connections. However, in its second phase it applies a rather demanding filtering process where only the most significant interaction of each gene is finally selected. This connection corresponds to the one with the highest mutual information value among the neighboring relationships of a gene. Therefore, each gene can only contribute one interaction to the list and therefore the maximum number of connections that C3NET can report is equivalent to the number of genes in the network. The purpose of this procedure is to ensure high reliability of the links exposed in the output network, providing a solid skeleton where the presence of false negatives is preferred over the usual number of false positives.

* **BC3NET**: [Bagging C3NET (BC3NET)](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0033624) attempts to alleviate the limitations imposed by the filtering process of the previous algorithm. Their approach is to generate several versions of the input data using a nonparametric bootstrap and apply the C3NET algorithm to each of these versions. This provides an ensemble of binary gene networks that are subsequently consensualized into a single network of weights.

* **CLR**: [Context Likelihood or Relatedness network (CLR)](https://pubmed.ncbi.nlm.nih.gov/17214507/) applies in the first instance the same procedure as the previous techniques, i.e. it calculates the mutual information coefficients in order to select candidate connections. However, this technique introduces an intermediate step before filtering, aimed at eliminating spurious correlations and indirect interactions. For this purpose, it calculates the statistical probability of each mutual information value within the context of its network, i.e. it performs a normalization process. This, in addition to eliminating possible false positives, corrects errors caused by inadequate or unequal sampling.

* **GENIE3**: [GEne Network Inference with Ensemble of trees (GENIE3)](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0012776) decomposes the problem of inferring a network of n genes into n different regression subproblems. In each of them the algorithm must construct a function that allows explaining the expression profile of the current gene as a function of the rest. The coefficients assigned to the other genes in this function are taken as confidence indicators, so that if the expression of the target gene is highly dependent on the expression of a particular gene, it follows that the two genes are clearly connected in the network.

* **GRNBOOST2**: [Gene Regulatory Network inference using gradient BOOSTing (GRNBOOST2)](https://doi.org/10.1093/bioinformatics/bty916) is based on the architecture of GENIE3 and therefore belongs to the class of regression-based GRN inference methods. For each gene in the dataset, a tree-based regression model is trained to predict its expression profile using the expression values of a set of candidate transcription factors (TFs). Each model produces a partial GRN with regulatory associations from the best predicting TFs to the target gene. All regulatory associations are combined and sorted by importance to finalize the GRN output.

* **KBOOST**: [kernel PCA regression and gradient boosting to reconstruct gene regulatory networks (KBOOST)](https://www.nature.com/articles/s41598-021-94919-6) like GENIE3, divides the inference problem for each gene present in the network. In each subproblem, a mathematical model is built to predict the expression of the target gene using [kernel principal component analysis (KPCA)](https://link.springer.com/chapter/10.1007/BFb0020217) on the expression levels of a likely subset of transcription factors. Different models are then compared and the probability of one gene regulating another is estimated using [Bayesian Model Averaging (BMA)](https://www.tandfonline.com/doi/abs/10.1080/01621459.1997.10473615).

* **MRNET**: [Minimum Redundancy NETworks (MRNET)](https://pubmed.ncbi.nlm.nih.gov/18354736/) proposes to perform network inference using the [Maximum Relevance Minimum Redundancy (MRMR) feature selection method](https://pubmed.ncbi.nlm.nih.gov/15852500/). This method is applied using a forward selection strategy, which implies that the procedure is strongly conditioned by the first variables selected. For each pair of genes evaluated during the course of the algorithm, this tool performs two calculations. First, it calculates the relevance of their connection, i.e. the mutual information coefficient seen so far. And secondly, it assigns a redundancy value, which corresponds to the average mutual information with respect to the previously ranked variables. After that, the optimization algorithm selects those interactions that simultaneously have a high relevance and a low redundancy. The purpose of this filtering is to eliminate false positives caused by indirect connections in the network, since although these cases have good mutual information (relevance), their level of redundancy will also be high, which will lead to their discrimination in the final list.

* **MRNETB**: [Minimum Redundancy NETworks using Backward elimination (MRNETB)](https://citeseerx.ist.psu.edu/viewdoc/download;jsessionid=5BF715493E925163623B3F3F6FE3EA88?doi=10.1.1.712.830&rep=rep1&type=pdf) replaces the forward selection strategy seen in the MRNET technique with a backward elimination procedure combined with sequential replacement. The objective lies in removing the limitation discussed in the previous technique with respect to the first variables selected. Instead, MRNETB starts with the set of all available variables and then discards at each step the one whose elimination leads to a larger increase of the objective function. In addition, in order to refine this strategy, a sequential replacement operator is introduced that takes care of exchanging the state of a selected and an unselected variable in order to further increase the fitness function output.

* **PCIT**: [Partial Correlation coefficient with Information Theory (PCIT)](https://pubmed.ncbi.nlm.nih.gov/18784117/) identifies candidate interactions between genes by applying partial correlation coefficients combined with an information theory approach. For each trio of genes, the algorithm calculates the three first-order partial correlation coefficients and then applies the [data processing inequality theorem (DPI)](https://arxiv.org/abs/1107.0740v2) from information theory. This allows you to obtain a local tolerance level that is then used as a threshold during filtering.

* **TIGRESS**: [Trustful Inference of Gene REgulation with Stability Selection (TIGRESS)](https://bmcsystbiol.biomedcentral.com/articles/10.1186/1752-0509-6-145) divides the inference problem into regression subproblems in a manner similar to that seen in GENIE3 and KBOOST. That is, for each gene, a function must be constructed to explain its expression profile as a function of the others. TIGRESS employs the LARS method during feature selection, which unlike other methods does not completely re-optimize the fitted model after each incorporation, but only partially refines it. However, [LARS](https://projecteuclid.org/journals/annals-of-statistics/volume-32/issue-2/Least-angle-regression/10.1214/009053604000000067.short) has proven to be quite sensitive to data with high levels of correlation and does not allow to extract scores about the relevance of each gene in target function. Therefore, TIGRESS incorporates the [stability selection procedure](https://rss.onlinelibrary.wiley.com/doi/10.1111/j.1467-9868.2010.00740.x), which iteratively runs the above method on randomly perturbed data and scores each feature based on the number of times it has been selected.

* **CMI2NI**: [Conditional Mutual Inclusivity principle-based Network Inference (CMI2NI)](https://doi.org/10.1093/nar/gku1315) is a gene regulatory network (GRN) inference method that uses the principle of conditional mutual inclusivity to identify direct regulatory relationships between genes. CMI2NI first constructs a pairwise association matrix using Pearson correlation coefficients between the expression profiles of all gene pairs. It then applies the conditional mutual inclusivity principle to select a set of candidate regulatory genes for each target gene, and prunes this set using a scoring function that takes into account the dependencies among the candidate genes. Finally, a directed network is reconstructed using a maximum likelihood estimator. CMI2NI has been shown to outperform several other state-of-the-art GRN inference methods in terms of accuracy and robustness on both synthetic and real-world datasets.

* **GRNVBEM**: [Gene Regulatory Network inference using Variational Bayesian Expectation-Maximization algorithm (GRNVBEM)](https://doi.org/10.1093/bioinformatics/btx605) is a Bayesian network inference method that incorporates prior knowledge in the form of network topology constraints and gene expression data to infer a GRN. The algorithm applies variational Bayesian inference to learn the structure and parameters of the network. GRNVBEM assumes that the expression levels of genes are generated from a Gaussian distribution, and that the network topology follows a scale-free distribution. The algorithm iteratively updates the posterior distribution over the network structure using the expectation-maximization algorithm. The final inferred network is the most probable network structure given the data and prior information.

* **INFERELATOR**: [Inferelator](https://doi.org/10.1186/gb-2006-7-5-r36) is a gene network inference method that uses a regularized linear regression model to predict the gene expression of a gene based on the expressions of other genes in a sample. The model uses a coefficient matrix that represents the interactions between the genes and a measure of the relevance of each gene in the prediction. The original version ([INFERRELATOR 1.0](https://doi.org/10.1186/gb-2006-7-5-r36)) uses a protein interaction database to restrict the possible interactions. The later version ([INFERRELATOR 2.0](https://doi.org/10.1109/IEMBS.2009.5334018)) incorporates promoter information into the coefficient matrix. Finally, the latest version ([INFERRELATOR 3.0](https://doi.org/10.1093/bioinformatics/btac117)) uses an information theory-based feature selection technique to reduce the number of candidate genes and improve accuracy.

* **JUMP3**: [Jump3](https://doi.org/10.1093/bioinformatics/btu863) is a gene regulatory network inference method based on the concept of "jumping" between different types of data sources to improve accuracy. It uses a hybrid of Bayesian networks and support vector machines to predict regulatory interactions between genes. Jump3 takes as input gene expression data and three types of prior knowledge: protein-protein interactions, transcription factor binding motifs, and pathway information. It then uses a "jumping" strategy to integrate these different sources of information and produce a final regulatory network. Unlike many other methods that rely on a single data source, Jump3 is designed to leverage the strengths of multiple data types to produce more accurate predictions.

* **LEAP**: [Lag-based Expression Association for Pseudotime-series](https://doi.org/10.1093/bioinformatics/btw729) is a gene regulatory network inference method that uses a time-lagged ensemble approach. It first constructs multiple gene regulatory networks from time-series data using the GENIE3 algorithm. Then, it constructs a set of time-lagged ensembles by randomly sampling subsets of networks and applying time delays to each one. Finally, it identifies the most stable interactions across all ensembles to obtain the final network. LEAP improves on GENIE3 by incorporating temporal information and reducing the impact of noisy and non-consistent interactions.

* **LOCPCACMI**: [Local Path Consistency Algorithm based on Conditional Mutual Information (LOCPCACMI)](https://doi.org/10.26599/TST.2018.9010097) first identifies local gene clusters and then infers the local network structure for each cluster by a Path Consistency Algorithm based on Conditional Mutual Information (PCA-CMI). The final structure of the GRN is denoted as dependence among genes by an ensemble of the obtained local network structures. Compared to other information theory-based network inference methods, including ARACNE, MRNET, PCA-CMI, and PCA-PMI, Loc-PCA-CMI outperforms the other four methods in DREAM3 datasets, especially in size 50 and 100 networks. The method aims to address issues such as external noise in the original data, topology sparseness in the network structure, and non-linear dependency among genes that can introduce redundant regulatory relationships in the network inference process.

* **MEOMI**: [Mixed Entropy Optimizing context-related likelihood Mutual Information (MEOMI)](https://doi.org/10.1093/bioinformatics/btac717) is an information-theoretic method that estimates the mutual information matrix between genes from gene expression data. The method applies a matrix completion algorithm to handle the missing values in the data and estimate the full mutual information matrix. The resulting matrix is then used to infer the regulatory relationships among genes and construct the gene regulatory network. Compared to other methods, MEOMI achieves higher accuracy in both synthetic and real gene expression datasets. The method also handles large-scale datasets efficiently and is robust to noise in the data.

* **NARROMI**: [Noise And Redundancy reduction technology by combining Recursive Optimization and Mutual Information](https://doi.org/10.1093/bioinformatics/bts619) is a method that combines recursive optimization (RO) based on ordinary differential equations and mutual information (MI) based on information theory. NARROMI first removes noisy regulations with low pairwise correlations using MI and then excludes redundant regulations from indirect regulators through RO. The RO step can determine regulatory directions without prior knowledge of regulators, thereby improving the accuracy of inferred GRNs.

* **NONLINEARODES**: [NON-LINEAR Ordinary Differential EquationS](https://doi.org/10.1093/bioinformatics/btaa032) is a method that uses non-linear ordinary differential equation (ODE) models to capture dynamic gene regulation and an importance measurement strategy to efficiently infer putative regulatory links. Compared to linear ODE models like implemented in [HIDI](https://doi.org/10.1093/bioinformatics/btx501) and [SCODE](https://doi.org/10.1093/bioinformatics/btx194), non-linear ODE models require more gene expression data and computational resources, but can capture a wider range of regulatory behaviors.

* **PCACMI**: [Path Consistency Algorithm based on Conditional Mutual Information](https://doi.org/10.1093/bioinformatics/btr626) is a method that considers the non-linear dependence and topological structure of GRNs by using a path consistency algorithm (PCA) based on conditional mutual information (CMI). In this algorithm, the conditional dependence between a pair of genes is represented by the CMI between them. The algorithm starts with initializing the gene expression data and setting a parameter for deciding the independence. Then, it generates the complete network for all genes and sets L=-1. In the next step, the PCACMI algorithm increases the value of L by one unit (L=L+1) and then selects the adjacent genes that are connected with both genes i and j. If the number of adjacent genes is less than L, the algorithm stops. Otherwise, it selects L genes from the adjacent genes and computes the L-order CMI for all selections. The algorithm chooses the maximal CMI and sets the corresponding edge to zero if it is less than the parameter. The algorithm repeats these steps until all edges have been considered.

* **PIDC**: [Partial Information Decomposition and context](https://doi.org/10.1016%2Fj.cels.2017.08.014) is an algorithm for inferring gene interaction networks from single-cell data. It uses information about the local network context of each gene and its unique contribution to partial information dependence to infer relationships between genes, enabling it to distinguish between direct and indirect interactions. The implementation of the algorithm in the Julia programming language allows for fast and scalable calculation of gene interaction networks.

* **PLSNET**: [PLS-based gene NETwork inference method](https://doi.org/10.1186/s12859-016-1398-6) is an ensemble gene regulatory network inference method that decomposes the problem of inferring a network of p genes into p subproblems. Each subproblem is solved using a Partial least squares (PLS) based feature selection algorithm. A statistical technique is used to refine the predictions and improve the inferred regulatory network. In this method, regulatory genes are scored based on their impacts on multiple target genes, and an updated adjacency matrix W is calculated based on the variances in each row of the original W matrix. If a regulatory gene regulates many target genes, its variance in the corresponding row of W is elevated.

* **PUC**: [Proportional Unique Contribution](https://doi.org/10.1016%2Fj.cels.2017.08.014) is a measure used in the inference of gene regulation networks that quantifies the unique contribution of each gene to the mutual information (MI) between two genes. This measure is used to identify the most important interactions between genes and to avoid overestimating the importance of redundant genes. It is integrated into the same Julia project as PIDC.

* **RSNET**: [Redundancy Silencing and Network Enhancement Technique](https://doi.org/10.1186/s12859-022-04696-w) is a method for inferring gene regulatory networks that uses a redundancy silencing and network improvement technique to address the problem of numerous indirect interactions inherited in predictions. In the proposed method, redundant interactions, including weak and indirect connections, are silenced through recursive adaptive optimization. Meanwhile, highly correlated regulators are constrained to improve the true positive rate of prediction. The algorithm uses both linear and non-linear interactions to overcome the limitations of linear or non-linear methods.

# Example procedure

1. **Obtain simulated expression data and their respective gold standards**. To do this, we have two options: 

- **Extraction**: Use the **extract-data** command to download expression data from known challenges and benchmarks.

```sh
# Expression data
geneci extract-data expression-data --database DREAM4 --output-dir input_data

# Gold standard
geneci extract-data gold-standard --database DREAM4 --output-dir input_data
```

- **Simulation**: Use the **generate-data** command to generate expression data through the SysGenSIM simulator. In this case, data can be generated from scratch by choosing a particular node size and distribution, or from real biological networks stored in multiple databases. In both cases, the type of perturbation to be simulated must be specified.

```sh
# From scratch
geneci generate-data generate-from-scratch --topology eipo-modular \
                                           --network-size 20 \
                                           --perturbation knockout \
                                           --output-dir input_data

# From real network
geneci generate-data download-real-network --database BioGrid \
                                           --id Oryza_sativa_Japonica \
                                           --output-dir input_data
geneci generate-data generate-from-real-network --real-list-of-links input_data/simulated_based_on_real/RAW/BioGrid_Oryza_sativa_Japonica.tsv 
                                                --perturbation overexpression
                                                --output-dir input_data
```

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
           --algorithm NSGAII --plot-fitness-evolution --plot-pareto-front \
           --plot-parallel-coordinates --output-dir inferred_networks
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
                         --plot-parallel-coordinates --output-dir inferred_networks/geneci_consensus
```

- **Consensus under own criteria**: Assign specific weights to each of the files resulting from each technique. In case the researcher has some experience in this domain, he can determine for himself the weights he wants to assign to each inferred network to build his own consensus network.

```sh
geneci weighted-confidence --weight-file-summand 0.5*inferred_networks/dream4_100_01_exp/lists/GRN_GENIE3_ET.csv \
                           --weight-file-summand 0.25*inferred_networks/dream4_100_01_exp/lists/GRN_CMI2NI.csv \
                           --weight-file-summand 0.25*inferred_networks/dream4_100_01_exp/lists/GRN_PIDC.csv \
                           --output-file inferred_networks/dream4_100_01_exp/weighted_confidence.csv
```

3. **Representation** of inferred networks using the **draw-network** command:

```sh
geneci draw-network --confidence-list inferred_networks/dream4_100_01_exp/lists/GRN_LOCPCACMI.csv \
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
                    --mode Both --nodes-distribution Spring \
                    --output-folder inferred_networks/dream4_100_01_exp/network_graphics
```

4. **Evaluation** of the quality of the inferred gene network with respect to the gold standard. Two procedures have been implemented: one specific to networks extracted from DREAM challenges, and another generic one that approaches the problem as a binary classification exercise. In both cases, the evaluation procedure can be applied to a list of interactions with their respective confidence levels, a certain weight distribution referring to the consensus, or even a Pareto front generated by our multi-objective algorithm mode that allows the representation of a parallel coordinate plot including both fitness functions and AUROC and AUPR metrics (which is quite useful for identifying high-quality regions). 

- **DREAM**: For the evaluation of networks from DREAM challenges, the evaluation data must be previously downloaded using the **extract-data** command and the **evaluation-data** subcommand, which requires providing the database and credentials of an account on the Synapse platform. After that, the **evaluate** command is used followed by the **dream-prediction** subcommand to access the three input options mentioned above. In any case, the challenge identifier, network identifier, evaluation files and input files need to be specified. The input files will depend on the chosen option: **dream-list-of-links**, **dream-weight-distribution** or **dream-pareto-front**.

```sh
# 1. Download evaluation data
geneci extract-data evaluation-data --database DREAM4 --username TFM-SynapseAccount --password TFM-SynapsePassword

# 2. Evaluate the accuracy of the inferred consensus network.
geneci evaluate dream-prediction dream-list-of-links --challenge D4C2 --network-id 100_1 \
                                                     --synapse-file input_data/DREAM4/EVAL/pdf_size100_1.mat \
                                                     --confidence-list inferred_networks/dream4_100_01_exp/ea_consensus/final_list.csv
```

- **Generic**: For network evaluation using the generic procedure, we directly use the **evaluate** command followed by the **generic-prediction** subcommand. This gives us access to the three types of input mentioned earlier, to which we must provide the gold standard of the problem and the relevant input files: **generic-list-of-links**, **generic-weight-distribution**, and **generic-pareto-front**.

```sh
geneci evaluate generic-prediction generic-list-of-links --confidence-list inferred_networks/sim_BioGrid_Oryza_sativa_Japonica_mixed_exp/ea_consensus/final_list.csv
                                                         --gs-binary-matrix input_data/simulated_based_on_real/GS/sim_BioGrid_Oryza_sativa_Japonica_mixed_gs.csv
```

5. **Binarization** of the inferred gene network. In many cases, it is useful to apply a cutoff criterion to convert a list of confidence values into a real network that asserts the specific interaction between genes. For this purpose, the **apply-cut** command is used, which is provided with the list of confidence values, the cutoff criterion and its corresponding threshold value.

```sh
geneci apply-cut --confidence-list inferred_networks/dream4_100_01_exp/ea_consensus/final_list.csv \
                 --cut-off-criteria PercLinksWithBestConf --cut-off-value 0.4 \
                 --output-file inferred_networks/dream4_100_01_exp/ea_consensus/final_list_binarized.csv
```

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

## `geneci apply-cut`

Converts a list of confidence values into a binary matrix that represents the final gene network.

**Usage**:

```console
$ geneci apply-cut [OPTIONS]
```

**Options**:

* `--confidence-list PATH`: Path to the CSV file with the list of trusted values.  [required]
* `--gene-names PATH`: Path to the TXT file with the name of the contemplated genes separated by comma and without space. If not specified, only the genes specified in the list of trusts will be considered.
* `--cut-off-criteria [MinConf|NumLinksWithBestConf|PercLinksWithBestConf]`: Criteria for determining which links will be part of the final binary matrix.  [required]
* `--cut-off-value FLOAT`: Numeric value associated with the selected criterion. Ex: MinConf = 0.5, NumLinksWithBestConf = 10, PercLinksWithBestConf = 0.4  [required]
* `--output-file PATH`: Path to the output CSV file that will contain the binary matrix resulting from the cutting operation.  [default: <<conf_list_path>>/../networks/<<conf_list_name>>.csv]
* `--help`: Show this message and exit.

## `geneci cluster-network`

Divide an initial gene network into several communities following the Infomap (recommended) or Louvain grouping algorithm.

**Usage**:

```console
$ geneci cluster-network [OPTIONS]
```

**Options**:

* `--confidence-list PATH`: Path to the CSV file with the list of trusted values.  [required]
* `--algorithm [Louvain|Infomap]`: Clustering algorithm  [default: Infomap] 
* `--output-folder PATH`: Path to output folder  [default: communities]
* `--help`: Show this message and exit.

## `geneci draw-network`

Draw gene regulatory networks from confidence lists.

**Usage**:

```console
$ geneci draw-network [OPTIONS]
```

**Options**:

* `--confidence-list TEXT`: Paths of the CSV files with the confidence lists to be represented  [required]
* `--mode [Static2D|Interactive3D|Both]`: Mode of representation  [default: Both]
* `--nodes-distribution [Spring|Circular|Kamada_kawai]`: Node distribution in graph  [default: Spring]
* `--output-folder PATH`: Path to output folder  [default: <<conf_list_path>>/../network_graphics]
* `--help`: Show this message and exit.

## `geneci evaluate`

Evaluate the accuracy of the inferred network with respect to its gold standard.

**Usage**:

```console
$ geneci evaluate [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `dream-prediction`: Evaluate the accuracy with which networks belonging to the DREAM challenges are predicted.
* `generic-prediction`: Evaluate the accuracy with which any generic network has been predicted with respect to a given gold standard. To do so, it approaches the case as a binary classification problem between 0 and 1.

### `geneci evaluate dream-prediction`

Evaluate the accuracy with which networks belonging to the DREAM challenges are predicted.

**Usage**:

```console
$ geneci evaluate dream-prediction [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `dream-list-of-links`: Evaluate one list of links with confidence levels.
* `dream-pareto-front`: Evaluate pareto front.
* `dream-weight-distribution`: Evaluate one weight distribution.

#### `geneci evaluate dream-prediction dream-list-of-links`

Evaluate one list of links with confidence levels.

**Usage**:

```console
$ geneci evaluate dream-prediction dream-list-of-links [OPTIONS]
```

**Options**:

* `--challenge [D3C4|D4C2|D5C4]`: DREAM challenge to which the inferred network belongs  [required]
* `--network-id TEXT`: Predicted network identifier. Ex: 10_1  [required]
* `--synapse-file PATH`: Paths to files from synapse needed to perform inference evaluation. To download these files you need to register at https://www.synapse.org/# and download them manually or run the command extract-data evaluation-data.  [required]
* `--confidence-list PATH`: Path to the CSV file with the list of trusted values.  [required]
* `--help`: Show this message and exit.

#### `geneci evaluate dream-prediction dream-pareto-front`

Evaluate pareto front.

**Usage**:

```console
$ geneci evaluate dream-prediction dream-pareto-front [OPTIONS]
```

**Options**:

* `--challenge [D3C4|D4C2|D5C4]`: DREAM challenge to which the inferred network belongs  [required]
* `--network-id TEXT`: Predicted network identifier. Ex: 10_1  [required]
* `--synapse-file PATH`: Paths to files from synapse needed to perform inference evaluation. To download these files you need to register at https://www.synapse.org/# and download them manually or run the command extract-data evaluation-data.  [required]
* `--weights-file PATH`: File with the weights corresponding to a pareto front.  [required]
* `--fitness-file PATH`: File with the fitness values corresponding to a pareto front.  [required]
* `--confidence-folder PATH`: Folder route that contains the confidence lists whose names correspond to those registered in the file of the file 'weights_file'.  [required]
* `--output-dir PATH`: Output folder path  [default: <<weights_file_dir>>]
* `--plot-metrics / --no-plot-metrics`: Indicate if you want to represent parallel coordinates graph with AUROC and AUPR metrics.  [default: plot-metrics]
* `--help`: Show this message and exit.

#### `geneci evaluate dream-prediction dream-weight-distribution`

Evaluate one weight distribution.

**Usage**:

```console
$ geneci evaluate dream-prediction dream-weight-distribution [OPTIONS]
```

**Options**:

* `--challenge [D3C4|D4C2|D5C4]`: DREAM challenge to which the inferred network belongs  [required]
* `--network-id TEXT`: Predicted network identifier. Ex: 10_1  [required]
* `--synapse-file PATH`: Paths to files from synapse needed to perform inference evaluation. To download these files you need to register at https://www.synapse.org/# and download them manually or run the command extract-data evaluation-data.  [required]
* `--weight-file-summand TEXT`: Paths of the CSV files with the confidence lists together with its associated weights. Example: 0.7*/path/to/list.csv  [required]
* `--help`: Show this message and exit.

### `geneci evaluate generic-prediction`

Evaluate the accuracy with which any generic network has been predicted with respect to a given gold standard. To do so, it approaches the case as a binary classification problem between 0 and 1.

**Usage**:

```console
$ geneci evaluate generic-prediction [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `generic-list-of-links`: Evaluate one list of links with confidence levels.
* `generic-pareto-front`: Evaluate pareto front.
* `generic-weight-distribution`: Evaluate one weight distribution.

#### `geneci evaluate generic-prediction generic-list-of-links`

Evaluate one list of links with confidence levels.

**Usage**:

```console
$ geneci evaluate generic-prediction generic-list-of-links [OPTIONS]
```

**Options**:

* `--confidence-list PATH`: Path to the CSV file with the list of trusted values.  [required]
* `--gs-binary-matrix PATH`: Gold standard binary network  [required]
* `--help`: Show this message and exit.

#### `geneci evaluate generic-prediction generic-pareto-front`

Evaluate pareto front.

**Usage**:

```console
$ geneci evaluate generic-prediction generic-pareto-front [OPTIONS]
```

**Options**:

* `--weights-file PATH`: File with the weights corresponding to a pareto front.  [required]
* `--fitness-file PATH`: File with the fitness values corresponding to a pareto front.  [required]
* `--confidence-folder PATH`: Folder route that contains the confidence lists whose names correspond to those registered in the file of the file 'weights_file'.  [required]
* `--gs-binary-matrix PATH`: Gold standard binary network  [required]
* `--output-dir PATH`: Output folder path  [default: <<weights_file_dir>>]
* `--plot-metrics / --no-plot-metrics`: Indicate if you want to represent parallel coordinates graph with AUROC and AUPR metrics.  [default: plot-metrics]
* `--help`: Show this message and exit.

#### `geneci evaluate generic-prediction generic-weight-distribution`

Evaluate one weight distribution.

**Usage**:

```console
$ geneci evaluate generic-prediction generic-weight-distribution [OPTIONS]
```

**Options**:

* `--weight-file-summand TEXT`: Paths of the CSV files with the confidence lists together with its associated weights. Example: 0.7*/path/to/list.csv  [required]
* `--gs-binary-matrix PATH`: Gold standard binary network  [required]
* `--help`: Show this message and exit.

## `geneci extract-data`

Extract public data generated by simulators such as SynTReN, Rogers and GeneNetWeaver, as well as data from known challenges like DREAM3, DREAM4, DREAM5 and IRMA.

**Usage**:

```console
$ geneci extract-data [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `evaluation-data`: Download evaluation data of DREAM challenges.
* `expression-data`: Download time series of gene expression data (already produced by simulators and published in challenges).
* `gold-standard`: Download gold standards (of networks already produced by simulators and published in challenges).

### `geneci extract-data evaluation-data`

Download evaluation data of DREAM challenges.

**Usage**:

```console
$ geneci extract-data evaluation-data [OPTIONS]
```

**Options**:

* `--database [DREAM3|DREAM4|DREAM5]`: Databases for downloading evaluation data.  [required]
* `--output-dir PATH`: Path to the output folder.  [default: input_data]
* `--username TEXT`: Synapse account username.  [required]
* `--password TEXT`: Synapse account password.  [required]
* `--help`: Show this message and exit.

### `geneci extract-data expression-data`

Download time series of gene expression data (already produced by simulators and published in challenges).

**Usage**:

```console
$ geneci extract-data expression-data [OPTIONS]
```

**Options**:

* `--database [DREAM3|DREAM4|DREAM5|SynTReN|Rogers|GeneNetWeaver|IRMA]`: Databases for downloading expression data.  [required]
* `--output-dir PATH`: Path to the output folder.  [default: input_data]
* `--username TEXT`: Synapse account username. Only necessary when selecting DREAM3 or DREAM5.
* `--password TEXT`: Synapse account password. Only necessary when selecting DREAM3 or DREAM5.
* `--help`: Show this message and exit.

### `geneci extract-data gold-standard`

Download gold standards (of networks already produced by simulators and published in challenges).

**Usage**:

```console
$ geneci extract-data gold-standard [OPTIONS]
```

**Options**:

* `--database [DREAM3|DREAM4|DREAM5|SynTReN|Rogers|GeneNetWeaver|IRMA]`: Databases for downloading gold standards.  [required]
* `--output-dir PATH`: Path to the output folder.  [default: input_data]
* `--username TEXT`: Synapse account username. Only necessary when selecting DREAM3 or DREAM5.
* `--password TEXT`: Synapse account password. Only necessary when selecting DREAM3 or DREAM5.
* `--help`: Show this message and exit.

## `geneci generate-data`

Simulate time series with gene expression levels using the SysGenSIM simulator. They can be generated from scratch or based on the interactions of a real gene network.

**Usage**:

```console
$ geneci generate-data [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `download-real-network`: Download real gene regulatory networks in the form of interaction lists to be fed into the expression data simulator.
* `generate-from-real-network`: Simulate time series with gene expression levels using the SysGenSIM simulator from real-world networks.
* `generate-from-scratch`: Simulate time series with gene expression levels using the SysGenSIM simulator from scratch.

### `geneci generate-data download-real-network`

Download real gene regulatory networks in the form of interaction lists to be fed into the expression data simulator.

**Usage**:

```console
$ geneci generate-data download-real-network [OPTIONS]
```

**Options**:

* `--database [TFLink|RegulonDB|RegNetwork|BioGrid|GRNdb]`: Database from which the real gene regulatory network is to be obtained.  [required]
* `--id TEXT`: The identifier of the gene network within the selected database.  [required]
* `--output-dir PATH`: Path to the output folder.  [default: input_data]
* `--help`: Show this message and exit.

### `geneci generate-data generate-from-real-network`

Simulate time series with gene expression levels using the SysGenSIM simulator from real-world networks.

**Usage**:

```console
$ geneci generate-data generate-from-real-network [OPTIONS]
```

**Options**:

* `--real-list-of-links PATH`: Path to the csv file with the list of links. You can only specify either a value of 1 for an activation link or -1 to indicate inhibition.  [required]
* `--perturbation [knockout|knockdown|overexpression|mixed]`: Type of perturbation to apply on the network to simulate expression levels for genes.  [required]
* `--output-dir PATH`: Path to the output folder.  [default: input_data]
* `--help`: Show this message and exit.

### `geneci generate-data generate-from-scratch`

Simulate time series with gene expression levels using the SysGenSIM simulator from scratch.

**Usage**:

```console
$ geneci generate-data generate-from-scratch [OPTIONS]
```

**Options**:

* `--topology [random|random-acyclic|scale-free|small-world|eipo|random-modular|eipo-modular]`: The type of topology to be attributed to the simulated gene network.  [required]
* `--network-size INTEGER RANGE`: Number of genes that will make up the simulated gene network.  [x>=20; required]
* `--perturbation [knockout|knockdown|overexpression|mixed]`: Type of perturbation to apply on the network to simulate expression levels for genes.  [required]
* `--output-dir PATH`: Path to the output folder.  [default: input_data]
* `--help`: Show this message and exit.

## `geneci infer-network`

Infer gene regulatory networks from expression data. Several techniques are available: ARACNE, BC3NET, C3NET, CLR, GENIE3_RF, GRNBOOST2, GENIE3_ET, MRNET, MRNETB, PCIT, TIGRESS, KBOOST, MEOMI, JUMP3, NARROMI, CMI2NI, RSNET, PCACMI, LOCPCACMI, PLSNET, PIDC, PUC, GRNVBEM, LEAP, NONLINEARODES and INFERELATOR

**Usage**:

```console
$ geneci infer-network [OPTIONS]
```

**Options**:

* `--expression-data PATH`: Path to the CSV file with the expression data. Genes are distributed in rows and experimental conditions (time series) in columns.  [required]
* `--technique [ARACNE|BC3NET|C3NET|CLR|GENIE3_RF|GRNBOOST2|GENIE3_ET|MRNET|MRNETB|PCIT|TIGRESS|KBOOST|MEOMI|JUMP3|NARROMI|CMI2NI|RSNET|PCACMI|LOCPCACMI|PLSNET|PIDC|PUC|GRNVBEM|LEAP|NONLINEARODES|INFERELATOR]`: Inference techniques to be performed.  [required]
* `--threads INTEGER`: Number of threads to be used during parallelization. By default, the maximum number of threads available in the system is used.  [default: 64]
* `--str-threads TEXT`: Comma-separated list with the identifying numbers of the threads to be used. If specified, the threads variable will automatically be set to the length of the list.
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
* `--algorithm [GA|NSGAII|SMPSO]`: Evolutionary algorithm to be used during the optimization process. All are intended for a multi-objective approach with the exception of the genetic algorithm (GA).  [required]
* `--threads INTEGER`: Number of threads to be used during parallelization. By default, the maximum number of threads available in the system is used.  [default: 64]
* `--plot-fitness-evolution / --no-plot-fitness-evolution`: Indicate if you want to represent the evolution of the fitness values.  [default: no-plot-fitness-evolution]
* `--plot-pareto-front / --no-plot-pareto-front`: Indicate if you want to represent the Pareto front (only available for multi-objective mode of 2 or 3 functions). [default: no-plot-pareto-front]
* `--plot-parallel-coordinates / --no-plot-parallel-coordinates`: Indicate if you want to represent the parallel coordinate graph (only available for multi-objective mode). [default: no-plot-parallel-coordinates]
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
* `--plot-fitness-evolution / --no-plot-fitness-evolution`: Indicate if you want to represent the evolution of the fitness values.  [default: no-plot-fitness-evolution]
* `--plot-pareto-front / --no-plot-pareto-front`: Indicate if you want to represent the Pareto front (only available for multi-objective mode of 2 or 3 functions). [default: no-plot-pareto-front]
* `--plot-parallel-coordinates / --no-plot-parallel-coordinates`: Indicate if you want to represent the parallel coordinate graph (only available for multi-objective mode). [default: no-plot-parallel-coordinates]
* `--output-dir PATH`: Path to the output folder.  [default: inferred_networks]
* `--help`: Show this message and exit.

## `geneci weighted-confidence`

Calculate the weighted sum of the confidence levels reported in several files based on a given distribution of weights.

**Usage**:

```console
$ geneci weighted-confidence [OPTIONS]
```

**Options**:

* `--weight-file-summand TEXT`: Paths of the CSV files with the confidence lists together with its associated weights. Example: 0.7*/path/to/list.csv  [required]
* `--output-file PATH`: Output file path  [default: <<conf_list_path>>/../weighted_confidence.csv]
* `--help`: Show this message and exit.