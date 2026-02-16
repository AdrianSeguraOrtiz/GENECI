![CI](https://github.com/AdrianSeguraOrtiz/GENECI/actions/workflows/ci.yml/badge.svg)
![Release](https://github.com/AdrianSeguraOrtiz/GENECI/actions/workflows/release.yml/badge.svg)
![Pypi](https://img.shields.io/pypi/v/GENECI)
![License](https://img.shields.io/apm/l/GENECI)
<img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>


**GENECI (GEne NEtwork Consensus Inference)** is a software package designed for intelligent consensus of multiple techniques for inferring gene regulation networks. Given the expression levels of different genes subjected to various perturbations, GENECI allows for the inference of the underlying network by applying in parallel a wide variety of known inference techniques and subsequently merging their results. To this end, a **many-objective evolutionary algorithm** is applied to optimize the weights assigned to the different techniques based on observed **confidence levels**, **topological characteristics** of the network, **network dynamics**, **detection of highly recurrent motifs** in real biological networks, **importance of interactions**, **contextualized analysis of graph metrics** and, in case of a time series as input, **maintenance of the loyalty** to it.

![Alt text](https://github.com/AdrianSeguraOrtiz/GENECI/raw/dev/docs/diagram.svg)

GENECI offers the following **functionalities**: network inference using individual techniques, optimization of consensus across multiple solutions, construction of benchmark networks (from scratch or based on real networks), evaluation of accuracy concerning gold standards, network binarization algorithms, graphical representation of networks and optimization results, and modularized network segmentation.

To implement all the functionalities mentioned above, it has been necessary to program in multiple languages such as Java, Python, R, Matlab, Julia, etc. To integrate all the utilities into a single tool, it has been decided to **dockerize components** and use Python as the main means of orchestration. This, in addition to facilitating **task parallelization**, reduces the complexity of installation and requirements for our software package.

# Prerequisites

- Python >= 3.13,<3.14
- Docker

# Instalation

```sh
pip install geneci==5.0.0
```

# Output

To execute GENECI, you typically run `infer-network` first and then `apply-consensus` over the generated confidence lists. If more than one objective is used during consensus optimization, the following files are obtained after execution:

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

1. **Obtain expression data and gold standards**.

- **Benchmark downloads**:

```sh
# Expression data
geneci benchmarking expression-data download --database DREAM4 --output-dir input_data

# Gold standard
geneci benchmarking gene-regulatory-networks gold-standard --database DREAM4 --output-dir input_data
```

- **Simulation with SysGenSIM**:

```sh
# From scratch
geneci benchmarking expression-data generate generate-from-scratch \
  --topology eipo-modular \
  --network-size 20 \
  --perturbation knockout \
  --output-dir input_data

# From real network
geneci benchmarking gene-regulatory-networks download-real-network \
  --database BioGrid \
  --id Oryza_sativa_Japonica \
  --output-dir input_data

geneci benchmarking expression-data generate generate-from-real-network \
  --real-list-of-links input_data/simulated_based_on_real/RAW/BioGrid_Oryza_sativa_Japonica.tsv \
  --perturbation overexpression \
  --output-dir input_data
```

2. **Inference and consensus**.

```sh
# 1. Infer GRN lists with individual techniques
geneci infer-network \
  --expression-data input_data/DREAM4/EXP/dream4_100_01_exp.csv \
  --technique ARACNE --technique BC3NET --technique C3NET --technique CLR \
  --technique GENIE3_RF --technique GRNBOOST2 --technique GENIE3_ET \
  --technique MRNET --technique MRNETB --technique PCIT --technique TIGRESS \
  --technique KBOOST --technique MEOMI --technique NARROMI --technique CMI2NI \
  --technique RSNET --technique PCACMI --technique LOCPCACMI --technique PLSNET \
  --technique PIDC --technique PUC --technique GRNVBEM --technique LEAP \
  --technique NONLINEARODES --technique INFERELATOR \
  --output-dir inferred_networks

# 2. Apply evolutionary consensus
geneci apply-consensus \
  --confidence-list inferred_networks/dream4_100_01_exp/lists/GRN_LOCPCACMI.csv \
  --confidence-list inferred_networks/dream4_100_01_exp/lists/GRN_BC3NET.csv \
  --confidence-list inferred_networks/dream4_100_01_exp/lists/GRN_PLSNET.csv \
  --function Quality --function DegreeDistribution --function Motifs \
  --algorithm NSGAII \
  --output-dir inferred_networks/dream4_100_01_exp/ea_consensus
```

3. **Network visualization**.

```sh
geneci plotting draw-network \
  --confidence-list inferred_networks/dream4_100_01_exp/lists/GRN_LOCPCACMI.csv \
  --confidence-list inferred_networks/dream4_100_01_exp/lists/GRN_BC3NET.csv \
  --mode Interactive2D \
  --nodes-distribution Spring \
  --output-folder inferred_networks/dream4_100_01_exp/network_graphics
```

4. **Validation against benchmarks**.

```sh
# Download DREAM validation assets
geneci benchmarking validation evaluation-data \
  --database DREAM4 \
  --username TFM-SynapseAccount \
  --password TFM-SynapsePassword

# Validate one inferred list in DREAM mode
geneci benchmarking validation validate dream-prediction dream-list-of-links \
  --challenge D4C2 \
  --network-id 100_1 \
  --synapse-file input_data/DREAM4/EVAL/pdf_size100_1.mat \
  --confidence-list inferred_networks/dream4_100_01_exp/ea_consensus/final_list.csv

# Validate in generic mode
geneci benchmarking validation validate generic-prediction generic-list-of-links \
  --confidence-list inferred_networks/sim_BioGrid_Oryza_sativa_Japonica_mixed_exp/ea_consensus/final_list.csv \
  --gs-binary-matrix input_data/simulated_based_on_real/GS/sim_BioGrid_Oryza_sativa_Japonica_mixed_gs.csv
```

5. **Postprocessing (network binarization)**.

```sh
geneci postprocessing apply-cut \
  --confidence-list inferred_networks/dream4_100_01_exp/ea_consensus/final_list.csv \
  --cut-off-criteria PercLinksWithBestConf \
  --cut-off-value 0.4 \
  --output-file inferred_networks/dream4_100_01_exp/ea_consensus/final_list_binarized.csv
```

# CLI reference

Current CLI structure:

```text
geneci
├── infer-network
├── apply-consensus
├── benchmarking
│   ├── gene-regulatory-networks
│   │   ├── download-real-network
│   │   └── gold-standard
│   ├── expression-data
│   │   ├── download
│   │   └── generate
│   │       ├── generate-from-scratch
│   │       └── generate-from-real-network
│   └── validation
│       ├── evaluation-data
│       └── validate
│           ├── dream-prediction
│           │   ├── dream-list-of-links
│           │   ├── dream-weight-distribution
│           │   └── dream-pareto-front
│           └── generic-prediction
│               ├── generic-list-of-links
│               ├── generic-weight-distribution
│               └── generic-pareto-front
├── plotting
│   └── draw-network
└── postprocessing
    └── apply-cut
```

Top-level help:

```console
$ geneci --help
```

Subtree help examples:

```console
$ geneci benchmarking --help
$ geneci benchmarking expression-data --help
$ geneci benchmarking validation validate --help
$ geneci plotting draw-network --help
$ geneci postprocessing apply-cut --help
```
