![CI](https://github.com/AdrianSeguraOrtiz/GENECI/actions/workflows/ci.yml/badge.svg)
![Release](https://github.com/AdrianSeguraOrtiz/GENECI/actions/workflows/release.yml/badge.svg)
![Pypi](https://img.shields.io/pypi/v/GENECI)
![Downloads](https://assets.piptrends.com/get-last-month-downloads-badge/geneci.svg)
<img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>


**GENECI (GEne NEtwork Consensus Inference)** is a software package designed for intelligent consensus of multiple techniques for inferring gene regulation networks. Given the expression levels of different genes subjected to various perturbations, GENECI allows for the inference of the underlying network by applying in parallel a wide variety of known inference techniques and subsequently merging their results. To this end, a **many-objective evolutionary algorithm** is applied to optimize the weights assigned to the different techniques based on observed **confidence levels**, **topological characteristics** of the network, **network dynamics**, **detection of highly recurrent motifs** in real biological networks, **importance of interactions**, **contextualized analysis of graph metrics** and, in case of a time series as input, **maintenance of the loyalty** to it.

![Alt text](https://github.com/AdrianSeguraOrtiz/GENECI/raw/dev/docs/diagram.svg)

GENECI offers the following **functionalities**: network inference using individual techniques, optimization of consensus across multiple solutions, construction of benchmark networks (from scratch or based on real networks), evaluation of accuracy concerning gold standards, network binarization algorithms, graphical representation of networks and optimization results, and modularized network segmentation.

To implement all the functionalities mentioned above, it has been necessary to program in multiple languages such as Java, Python, R, Matlab, Julia, etc. To integrate all the utilities into a single tool, it has been decided to **dockerize components** and use Python as the main means of orchestration. This, in addition to facilitating **task parallelization**, reduces the complexity of installation and requirements for our software package.

# Prerequisites

- Python => 3.9
- Docker

# Instalation

```sh
pip install geneci==4.0.1.1
```

# Publications

The current version of **GENECI** integrates all the software developments presented throughout the following scientific publications, which together represent the full evolution of the framework — from its original design to the current multi-objective and preference-based consensus model for Gene Regulatory Network (GRN) inference:

* **Segura-Ortiz, A.**, García-Nieto, J., Aldana-Montes, J. F., & Navas-Delgado, I. (2023). *GENECI: a novel evolutionary machine learning consensus-based approach for the inference of gene regulatory networks.* **Computers in Biology and Medicine**, 155, 106653.
* **Segura-Ortiz, A.**, García-Nieto, J., & Aldana-Montes, J. F. (2024, June). *Exploiting medical-expert knowledge via a novel memetic algorithm for the inference of gene regulatory networks.* In *International Conference on Computational Science* (pp. 3–17). Cham: Springer Nature Switzerland.
* **Segura-Ortiz, A.**, García-Nieto, J., Aldana-Montes, J. F., & Navas-Delgado, I. (2024). *Multi-objective context-guided consensus of a massive array of techniques for the inference of Gene Regulatory Networks.* **Computers in Biology and Medicine**, 179, 108850.
* **Segura-Ortiz, A.**, Giménez-Orenga, K., García-Nieto, J., Oltra, E., & Aldana-Montes, J. F. (2025). *Multifaceted evolution focused on maximal exploitation of domain knowledge for the consensus inference of Gene Regulatory Networks.* **Computers in Biology and Medicine**, 196, 110632.
* **Segura-Ortiz, A.**, García-Nieto, J., & Aldana-Montes, J. F. (Under review, 2025). *Multi-objective consensus optimization for GRN inference: a preference-based approach.* **Computational Biology and Chemistry**.

These works collectively describe the foundation, extensions, and ongoing developments that culminate in the unified implementation available in this repository, covering evolutionary, memetic, and multi-objective consensus optimization strategies for GRN inference.



# Output

To execute GENECI, the `run` command is provided with the file containing the expression levels of the genes that make up the network, the list of techniques to be agreed upon and the values of the different algorithm parameters in the event of not wishing to use those established by default. If more than one proposed objectives are used, the following files are obtained after execution:

- `FUN.csv`: List with fitness values for each individual in the final population for each of the objective functions.
- `VAR.csv`: List of winning weight vectors, i.e., individuals from the last generation.
- `fitness_evolution.txt` and `fitness_evolution.html`: In each generation, the most optimal value found for each objective function is recorded. These values are stored in the text file and subsequently represented in graphs in HTML format.
- `parallel_coordinates.html`: File containing a graphical representation of parallel coordinates. Each column refers to a specific objective function, and each horizontal line represents an individual from the final population. This graph is very useful to observe conflicts between different fitness functions in a multi-objective evolutionary algorithm.
- `pareto_front.html`: Pareto front represented in a three-dimensional graph, where each axis refers to a different fitness function.

# Integrated techniques

* **ARACNE**: [Algorithm for the Reconstruction of Accurate Cellular NEtworks](https://bmcbioinformatics.biomedcentral.com/articles/10.1186/1471-2105-7-S1-S7): It employs an information-theoretic approach for the reverse engineering of transcriptional networks from microarray data. Initially, ARACNE identifies candidate interactions by estimating the mutual information (MI) between pairs of gene expression profiles, applying a statistical significance threshold to retain only the strongest associations. Subsequently, the algorithm applies the Data Processing Inequality (DPI) to remove most indirect interactions. Specifically, for each triplet of genes where all pairwise MI values exceed the threshold, ARACNE eliminates the edge with the smallest MI value, assuming it represents an indirect interaction. This method is designed to scale to the complexity of regulatory networks in mammalian cells, with a computational complexity of $O(N^3 + N^2M^2)$, where $N$ is the number of genes and $M$ is the number of samples.
* **BC3NET**: [Bagging C3NET](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0033624): It is based on the bootstrap aggregation (bagging) technique applied to the [C3NET](https://bmcsystbiol.biomedcentral.com/articles/10.1186/1752-0509-4-132) algorithm. The BC3NET process involves generating an ensemble of independent bootstrap datasets from the original dataset. For each of these bootstrap datasets, a network is inferred using the C3NET algorithm. These inferred networks are then aggregated to form a weighted network, where edge weights represent the frequency with which a connection between a pair of genes appears across the ensemble of networks. Finally, statistical hypothesis testing is applied to these edge weights to determine the significance of the connections, thus eliminating the need for manually selecting a threshold. The computational complexity of BC3NET is $O(B|n^2)$, where $B$ is the number of bootstraps and $n$ is the number of genes. This ensemble approach aims to reduce the variance of the estimates and address issues such as noise and outliers in expression data.
* **C3NET**: [Conservative Causal Core NETwork](https://bmcsystbiol.biomedcentral.com/articles/10.1186/1752-0509-4-132): This algorithm is based on the estimation of mutual information (MI) values combined with a maximization step to efficiently exploit causal structural information in the data. The algorithm begins by removing non-significant connections between pairs of genes through statistical significance testing of the MI values. Then, for each gene, it identifies the connection to its neighbor with the highest mutual information value. Finally, it constructs an adjacency matrix where a connection is established if the maximum MI value for a given gene corresponds to another gene. The computational complexity of C3NET is $O(n^2)$, where $n$ is the number of genes, making it one of the fastest algorithms. The C3NET approach focuses on inferring the "conservative causal core" of the network, that is, the strongest interactions, rather than the full network.
* **CLR**: [Context Likelihood or Relatedness network](https://pubmed.ncbi.nlm.nih.gov/17214507/): This algorithm infers transcriptional regulatory networks based on an extension of the relevance network approach. Like relevance networks, CLR uses mutual information (MI) to quantify the similarity between gene expression profiles, where a high MI suggests a potential regulatory interaction. The key innovation of CLR lies in its adaptive background correction step. After computing the MI for all possible regulator–target gene pairs, CLR estimates the statistical significance of each MI value within its network context. This is achieved by comparing the MI of a specific pair to the distribution of MI values for all other pairs involving the same regulator or the same target gene. The most likely interactions are those whose MI values lie significantly above these background distributions, allowing many spurious correlations and indirect influences to be filtered out. The algorithm computes a joint significance score based on the z-scores of the pairwise MI relative to the marginal MI distributions for each individual gene.
* **CMI2NI**: [Conditional Mutual Inclusivity principle-based Network Inference](https://doi.org/10.1093/nar/gku1315): This method uses the concept of conditional mutual inclusive information (CMI2) to quantify causal associations between genes, aiming to overcome the common issues of mutual information (MI) overestimation and conditional mutual information (CMI) underestimation. CMI2 is defined as the average Kullback–Leibler (KL) divergence between the joint probability distribution of three variables (two genes and a conditioning variable) and the interventional probability distributions obtained by removing the edge in each direction. For GRN inference, CMI2NI combines CMI2 with the path-consistency (PC) algorithm to eliminate indirect regulations from an initially complete graph. The algorithm starts by generating a fully connected graph and then recursively removes edges with low initial MI values and subsequent low-order CMI2 values. CMI2 is efficiently computed under the assumption of a Gaussian distribution for gene expression data using covariance matrices.
* **GENIE3**: [GEne Network Inference with Ensemble of trees](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0012776): This method decomposes the prediction of a regulatory network among $p$ genes into $p$ different regression problems. In each of these problems, the expression pattern of one gene (the target gene) is predicted from the expression patterns of all other genes (input genes), using tree-based ensemble methods such as Random Forests (GENIE3_RF) or Extra-Trees (GENIE3_ET). The importance of an input gene in predicting the expression pattern of the target gene is taken as an indication of a potential regulatory link. These potential regulatory links are then aggregated across all genes to produce a ranking of interactions, from which the full network is reconstructed. GENIE3 makes no assumptions about the nature of gene regulation, can handle combinatorial and non-linear interactions, produces directed GRNs, and is fast and scalable. Its computational complexity is on the order of $O(pTKN \log N)$, where $p$ is the number of genes, $T$ is the number of trees, $N$ is the training sample size, and $K$ is a main parameter of the tree-based methods.
* **GRNBOOST2**: [Gene Regulatory Network inference using gradient BOOSTing](https://doi.org/10.1093/bioinformatics/bty916): This is an efficient algorithm for gene regulatory network (GRN) inference that uses gradient boosting and builds upon the GENIE3 architecture. Like GENIE3, it belongs to the class of regression-based GRN inference methods. For each gene in the dataset, a tree-based regression model is trained to predict its expression profile using the expression values of a set of candidate transcription factors (TFs). Each model produces a partial GRN with regulatory associations from the most predictive TFs toward the target gene. All regulatory associations are then aggregated and ranked by importance to generate the final GRN output. GRNBoost2 employs a regularized stochastic variant of gradient boosting machines (GBMs), equipped with a heuristic early stopping strategy based on out-of-bag improvement estimates. This early stopping is triggered when the average of the last $n$ improvement values falls below zero. GRNBoost2 is implemented within the [Arboreto](https://arboreto.readthedocs.io/) framework, which leverages Dask for parallel computation, allowing the inference process to scale to large datasets. The independence of the regression tasks for each target gene makes the algorithm highly parallelizable. GRNBoost2 stands out for its efficiency, using shallower decision trees and building significantly fewer trees than GENIE3, thanks to the bias-reducing effect of gradient boosting and the early stopping mechanism.
* **GRNVBEM**: [Gene Regulatory Network inference using Variational Bayesian Expectation-Maximization algorithm](https://doi.org/10.1093/bioinformatics/btx605): This method performs gene regulatory network (GRN) inference from time-series and pseudotime data by employing a first-order autoregressive moving average model (AR1MA1) to capture noisy gene expression dynamics. Computationally, the method relies on a variational Bayesian expectation-maximization (VBEM) framework to infer the GRN. Within this framework, the binary variables describing the network topology are treated as latent variables. VBEM optimizes a free-form distribution over the latent variables and model parameters to approximate the posterior distribution by maximizing a lower bound of the marginal log-likelihood. To enable an analytical solution, GRNVBEM adopts a conjugate model with Gaussian priors over the latent variables and a scaled Inverse-Gamma distribution for the parameters. Due to the complexity of computing the marginal likelihood, a fixed-point approximation for the variance scale is used, based on the MAP estimates of the latent variables and the weights learned in previous VBEM iterations. The inference process involves the sequential application of learning rules to update the posterior hyperparameters until a convergence criterion is met.
* **INFERELATOR**: [regression and variable selection to identify transcriptional influences on genes](https://doi.org/10.1186/gb-2006-7-5-r36): This method integrates genomic annotation information and gene expression data, both from steady-state and time-series conditions, to identify transcriptional influences on genes. Inferelator uses regression and variable selection techniques, specifically L1 regression (LASSO), to produce parsimonious and predictive models. As a preprocessing step prior to network inference, the algorithm may employ an integrated biclustering method called cMonkey to group genes and conditions based on coherence in expression data, co-occurrence of cis-regulatory motifs, and functional associations, with the aim of identifying putatively co-regulated gene modules. Inferelator also models interactions between transcription factors (TFs) and environmental factors by incorporating functions of the minimum of two variables into the regression design matrix. The selection of the optimal model for each gene or bicluster is performed using cross-validation (CV) to choose the L1 shrinkage parameter that minimizes the prediction error.
* **JUMP3**: [jump trees](https://doi.org/10.1093/bioinformatics/btu863): Hybrid approach for the inference of gene regulatory networks (GRNs), combining a dynamic model of gene expression with a non-parametric decision tree-based method to reconstruct the network topology. Jump3 relies on a formal on/off model of gene expression, where the transcription rate of a gene switches between two levels depending on whether its promoter is active or inactive. For each target gene, Jump3 learns a model in the form of an ensemble of decision trees, referred to as jump trees, which predict the promoter state at any given time based on the expression levels of potential regulators at that same moment. The construction of each jump tree is performed greedily in a top-down manner, partitioning the set of time points based on tests over the expression levels of candidate regulators. Unlike standard decision trees, which split data by minimizing the entropy of the output variable, jump trees split by maximizing the likelihood of the gene expression observations, using the marginal likelihood of the node's dynamic model as the splitting criterion. To prevent overfitting, Jump3 builds an ensemble of such jump trees using an adaptation of the Extra-Trees procedure, which randomizes the test at each decision node. Finally, an importance score is derived for each candidate regulator, quantifying its relevance for predicting the promoter state of the target gene, based on the increase in likelihood produced by splits in the trees where the regulator is involved.
* **KBOOST**: [kernel PCA regression and gradient boosting to reconstruct gene regulatory networks](https://www.nature.com/articles/s41598-021-94919-6): Method for fast and scalable inference of gene regulatory networks (GRNs) that employs a combination of kernel principal component regression (KPCR), boosting, and Bayesian model averaging (BMA). The algorithm takes gene expression data as input, optionally including prior TF-target interactions, and for each gene builds a predictive model based on the kernel principal components (KPCs) of the expression of subsets of transcription factors (TFs), using an RBF kernel function to capture nonlinear relationships. Through a gradient boosting process with greedy model selection, KBoost constructs an ensemble of KPC-based models by iteratively selecting the TFs with the highest posterior distributions to predict gene expression and its residuals. Finally, the posterior probabilities of the explored models are combined using BMA to estimate the GRN, allowing the incorporation of prior knowledge as a Bayesian prior. KBoost has shown competitive performance and significantly faster runtimes compared to other GRN inference methods.
* **LEAP**: [Lag-based Expression Association for Pseudotime-series](https://doi.org/10.1093/bioinformatics/btw729): Algorithmic technique designed to construct gene networks from single-cell RNA sequencing (scRNA-Seq) data, taking into account potential time delays. Unlike methods based on simultaneous correlation, LEAP uses the estimated pseudotime of cells to order them along a temporal trajectory. It then computes the maximum correlation between the expression of gene pairs by considering different time windows with possible lags. This maximum correlation is used as a measure of co-expression strength, allowing LEAP to capture directional and potentially regulatory relationships between genes that might be overlooked by methods that only consider simultaneous associations. The algorithm also includes a function to estimate the false discovery rate (FDR) in order to assess the statistical significance of the detected associations.
* **LOC-PCA-CMI**: [Local Path Consistency Algorithm based on Conditional Mutual Information](https://doi.org/10.26599/TST.2018.9010097): Method for inferring the structure of GRNs that follows a divide-and-conquer strategy. Initially, the method identifies overlapping local clusters of genes based on the top $n$ highly co-expressed edges, determined through Pearson correlation analysis with false discovery rate (FDR) correction. Then, for each local cluster, the PCA-CMI algorithm [PCA-CMI](https://doi.org/10.1093/bioinformatics/btr626) is applied to infer the structure of the local subnetwork by repeatedly removing uncorrelated edges, from low- to high-order dependencies. Finally, the global structure of the GRN is obtained by assembling the inferred local network structures, averaging the edge weights. This approach enables Loc-PCA-CMI to handle relatively large datasets while benefiting from the accurate structure inference provided by PCA-CMI on small gene subnetworks.
* **MEOMI**: [Mixed Entropy Optimizing context-related likelihood Mutual Information](https://doi.org/10.1093/bioinformatics/btac717): Method for GRN construction based on the computation of mutual information through the combination of James–Stein entropy estimation and Bayesian estimation with a Dirichlet prior distribution. A context-related likelihood algorithm (based on [CLR](https://pubmed.ncbi.nlm.nih.gov/17214507/)) is then applied to optimize the mutual information matrix, obtaining an initial network by eliminating indirect relationships. This network is iteratively refined by computing conditional inclusive mutual information (CMI2), which considers the influence of multiple genes, and by applying a path consistency algorithm with dynamic thresholds to progressively remove redundant edges. This process leads to a more accurate final GRN. MEOMI aims to overcome the limitations of mutual information and conditional mutual information in order to infer direct regulatory relationships with greater accuracy.
* **MRNET**: [Minimum Redundancy NETworks](https://pubmed.ncbi.nlm.nih.gov/18354736/): Computational method for inferring gene networks from microarray data, based on the maximum relevance/minimum redundancy (MRMR) principle, an information-theoretic feature selection technique. MRNET extends this feature selection principle to networks in order to infer dependency relationships between genes. The MRNET strategy formulates the network inference problem as a series of supervised gene selection procedures, where each gene plays the role of a target output. For each target gene, the MRMR principle is applied to select a set of genes that have high mutual information with the target (maximum relevance) and are mutually minimally redundant. For each gene pair {Xi, Xj}, MRMR returns two scores, and the score for the pair is computed by taking the maximum of these two values. A connection between Xi and Xj is inferred if this score exceeds a given threshold. MRNET has proven to be competitive with other information-theoretic inference methods such as CLR and ARACNE in experiments using synthetically generated microarray data. The computational complexity of MRNET lies between $O(n^2)$ and $O(n^3)$, depending on the number of features selected at each step. It should be emphasized that, like other mutual information-based methods, MRNET cannot determine the directionality of interactions.
* **MRNETB**: [Minimum Redundancy NETworks using Backward elimination](https://citeseerx.ist.psu.edu/viewdoc/download;jsessionid=5BF715493E925163623B3F3F6FE3EA88?doi=10.1.1.712.830&rep=rep1&type=pdf): This is an improved version of the MRNET network inference method. The main enhancement of MRNETB lies in its variable selection strategy. While MRNET uses forward selection to identify a set of maximally independent neighbors for each variable, MRNETB employs a backward selection strategy followed by sequential replacement. This new neighbor selection strategy is implemented with the same computational cost as forward selection. MRNETB has shown significantly better performance than MRNET, regardless of the mutual information estimation method used. In comparative evaluations with other information-theoretic algorithms, such as CLR and ARACNE, MRNETB performed comparably to CLR and significantly better than ARACNE.
* **NARROMI**: [Noise And Redundancy reduction technology by combining Recursive Optimization and Mutual Information](https://doi.org/10.1093/bioinformatics/bts619): Technique for GRN inference that aims to improve accuracy by combining recursive optimization based on ordinary differential equations (RO) with mutual information (MI) from information theory. Initially, MI is used to detect and eliminate noisy regulations with low pairwise correlations. Then, the RO algorithm is applied to progressively exclude redundant regulations originating from indirect regulators, while also being capable of determining regulatory directions without prior knowledge of the regulators. Finally, the regulatory strengths inferred by RO and the MI correlations are integrated to account for both linear and nonlinear dependencies between regulators and target genes.
* **NONLINEARODES**: [NON-LINEAR Ordinary Differential EquationS](https://doi.org/10.1093/bioinformatics/btaa032): Method for GRN inference based on a nonlinear ordinary differential equation (ODE) framework to model the dynamics of gene regulation. This approach jointly leverages time-series and steady-state data to more accurately capture the transcriptional and translational processes among genes. The method decomposes the GRN inference problem into independent regression tasks for each target gene, where a nonlinear function is learned to describe the temporal evolution (or steady-state behavior) of that gene as a function of its potential regulators. To determine the relevance of candidate regulatory links, a scoring strategy based on gradient boosting trees is employed, specifically using XGBoost. Finally, all putative regulatory interactions are ranked according to their importance scores to reconstruct the GRN.
* **PCA-CMI**: [Path Consistency Algorithm based on Conditional Mutual Information](https://doi.org/10.1093/bioinformatics/btr626): Algorithm that combines the Path Consistency Algorithm (PCA) and Conditional Mutual Information (CMI) to evaluate the conditional dependence between gene pairs, thereby enabling the detection of nonlinear relationships that may be overlooked by linear correlation-based methods. PCA-CMI starts with a complete graph in which all genes are interconnected and iteratively removes edges that represent (conditional) independence relationships, beginning with lower-order dependencies until reaching a graph that represents the inferred network. This process, based on the computation of CMI from the covariance matrices of gene expression data under the assumption of a Gaussian distribution, allows PCA-CMI to distinguish between direct or causal interactions and indirect associations. The method has demonstrated superior performance compared to other approaches in evaluations using benchmark datasets such as those from the DREAM challenge.
* **PCIT**: [Partial Correlation coefficient with Information Theory](https://pubmed.ncbi.nlm.nih.gov/18784117/): Algorithm for gene network reconstruction that combines the concept of partial correlation coefficient with information theory to identify significant associations between genes. The method operates in two steps: first, it computes the partial correlation coefficients for each triplet of genes; second, it applies the Data Processing Inequality (DPI) theorem to determine a local tolerance level ($\varepsilon$) based on the average ratio between the partial correlation and the direct correlation. A connection between two genes is considered significant if the magnitude of their direct correlation is greater than the tolerance level multiplied by the magnitude of the partial correlation with a third gene. This strategy allows PCIT to identify moderate yet meaningful associations, being more sensitive than fixed-threshold methods when detecting interactions involving genes with low variability. It uses data-driven local tolerance thresholds instead of arbitrary global cutoffs.
* **PIDC**: [Partial Information Decomposition and context](https://doi.org/10.1016%2Fj.cels.2017.08.014): This algorithm is designed to infer GRNs from single-cell transcriptomic data using multivariate information measures. The method is based on partial information decomposition (PID) to explore statistical dependencies among gene triplets. For each gene pair, PIDC computes the proportional unique contribution ([PUC](https://doi.org/10.1016%2Fj.cels.2017.08.014)), which represents the proportion of mutual information explained by unique information in the context of other genes. Finally, similarly to the [CLR](https://pubmed.ncbi.nlm.nih.gov/17214507/) algorithm, PIDC incorporates network context by estimating an empirical probability distribution of PUC scores for each gene, enabling the identification of the most significant interactions per gene and overcoming the limitations of global thresholds.
* **PLSNET**: [PLS-based gene NETwork inference method](https://doi.org/10.1186/s12859-016-1398-6): Ensemble approach that uses partial least squares (PLS) regression for feature selection. The method decomposes the GRN inference problem into individual subproblems for each target gene, where the goal is to identify relevant regulatory genes through PLS-based feature selection applied repeatedly on random subsets of potential regulators. A statistical technique is then used to refine the predictions, assigning greater weight to regulatory genes that influence multiple target genes ("hub" genes).
* **PUC**: [Proportional Unique Contribution](https://doi.org/10.1016%2Fj.cels.2017.08.014): This is the core metric of the [PIDC](https://doi.org/10.1016%2Fj.cels.2017.08.014) algorithm, although its raw value can be considered as an independent GRN inference method. Its computation focuses on quantifying the average proportion of mutual information (MI) between two genes (X and Y) that is explained by the unique information they share, considering the context of all other genes (Z) in the network. For each gene pair X and Y, the ratio between the unique information they share conditional on a third gene Z and their total mutual information is computed, and this value is summed over all other genes Z in the network. A high PUC score between two genes suggests a more direct or specific functional relationship as opposed to a redundant one involving other genes. Results on simulated data indicate that the proportion of mutual information explained by the unique contribution tends to be higher between connected gene pairs.
* **RSNET**: [Redundancy Silencing and Network Enhancement Technique](https://doi.org/10.1186/s12859-022-04696-w): GRN inference method designed to address the challenge of distinguishing direct from indirect interactions. The method initially uses mutual information (MI) to define a search space of putative regulators and rank genes based on their dependency. It then applies a constraint-based recursive optimization process, in which genes with high dependency are retained in the model while redundant connections, including weak and indirect ones, are iteratively removed.
* **TIGRESS**: [Trustful Inference of Gene REgulation with Stability Selection](https://bmcsystbiol.biomedcentral.com/articles/10.1186/1752-0509-6-145): Method for GRN inference that formulates the problem as a sparse regression task and employs the Least Angle Regression (LARS) feature selection method combined with stability selection. TIGRESS stood out in the DREAM5 challenge, where it was ranked among the top methods and recognized as the best linear regression-based approach. The method introduces a novel scoring technique for stability selection, called the "area score" ($s_{area}(t, g)$), which computes the area under the selection frequency curve of a transcription factor (TF) for a target gene (TG) up to L steps of LARS, proving to be more robust and accurate than the original score. The key parameters of TIGRESS include the number of runs R, the number of LARS steps L, and the parameter $\alpha$ that controls the random re-weighting of the expression data.

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
           --algorithm NSGAII --plot-results --output-dir inferred_networks
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
                         --algorithm NSGAII --plot-results --output-dir inferred_networks/geneci_consensus
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
* `--plot-results`: Indicate if you want to represent results graphically. [default: plot-results]
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
* `--plot-results`: Indicate if you want to represent results graphically. [default: plot-results]
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