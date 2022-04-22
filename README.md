# EAGRN-Inference
Evolutionary algorithm for determining the optimal ensemble of unsupervised learning techniques for gene network inference.

# Example procedure

1. Generar .jar con dependencias:

```sh
cd EAGRN-JMetal
mvn clean compile assembly:single
cd ..
```

2. Generar imágenes

```sh
bash generate_images.sh
```

3. Descargar datos simulados de expresión y sus respectivos gold standard:

```sh
python EAGRN-Inference.py extract-data expression-data --database DREAM3 --database DREAM4 --database DREAM5 --database SynTReN --database Rogers --database GeneNetWeaver --database IRMA --username TFM-SynapseAccount --password TFM-SynapsePassword

python EAGRN-Inference.py extract-data gold-standard --database DREAM3 --database DREAM4 --database DREAM5 --database SynTReN --database Rogers --database GeneNetWeaver --database IRMA --username TFM-SynapseAccount --password TFM-SynapsePassword
```

4. Ejecutar algoritmo para un conjunto de datos de expresión concreto:

```sh
python EAGRN-Inference.py run --expression-data input_data/DREAM4/EXP/dream4_010_01_exp.csv --technique aracne --technique bc3net --technique c3net --technique clr --technique genie3_rf --technique genie3_gbm --technique genie3_et --technique mrnet --technique mrnetb --technique pcit --technique tigress --technique kboost
```

Este proceso también se puede dividir en dos partes:

4.1. Inferir redes de regulación génica mediante las técnicas individuales disponibles:

```sh
python EAGRN-Inference.py infer-network --expression-data input_data/DREAM4/EXP/dream4_010_01_exp.csv --technique aracne --technique bc3net --technique c3net --technique clr --technique genie3_rf --technique genie3_gbm --technique genie3_et --technique mrnet --technique mrnetb --technique pcit --technique tigress --technique kboost
```

4.2. Optimizar el ensemble de las listas de confianza resultantes del comando anterior:

```sh
python EAGRN-Inference.py optimize-ensemble --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_ARACNE.csv --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_BC3NET.csv --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_C3NET.csv --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_CLR.csv --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_GENIE3_RF.csv --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_GENIE3_GBM.csv --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_GENIE3_ET.csv --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_MRNET.csv --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_MRNETB.csv --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_PCIT.csv --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_TIGRESS.csv --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_KBOOST.csv --gene-names inferred_networks/dream4_010_01_exp/gene_names.txt
```

5. Evaluar la calidad de la red génica inferida respecto a la gold standard

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

# Console script

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
* `--mutation [PolynomialMutation|CDGMutation|GroupedAndLinkedPolynomialMutation|GroupedPolynomialMutation|LinkedPolynomialMutation|NonUniformMutation|NullMutation|SimpleRandomMutation|UniformMutation]`: Mutation operator  [default: PolynomialMutation]
* `--repairer [StandardizationRepairer|GreedyRepair]`: Solution repairer to keep the sum of weights equal to 1  [default: GreedyRepair]
* `--population-size INTEGER`: Population size  [default: 100]
* `--num-evaluations INTEGER`: Number of evaluations  [default: 100000]
* `--cut-off-criteria [MinConfidence|MaxNumLinksBestConf|MinConfFreq]`: Criteria for determining which links will be part of the final binary matrix.  [default: MinConfFreq]
* `--cut-off-value FLOAT`: Numeric value associated with the selected criterion. Ex: MinConfidence = 0.5, MaxNumLinksBestConf = 10, MinConfFreq = 0.2  [default: 0.2]
* `--no-graphics / --no-no-graphics`: Indicate if you do not want to represent the evolution of the fitness value.  [default: False]
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
* `--mutation [PolynomialMutation|CDGMutation|GroupedAndLinkedPolynomialMutation|GroupedPolynomialMutation|LinkedPolynomialMutation|NonUniformMutation|NullMutation|SimpleRandomMutation|UniformMutation]`: Mutation operator  [default: PolynomialMutation]
* `--repairer [StandardizationRepairer|GreedyRepair]`: Solution repairer to keep the sum of weights equal to 1  [default: GreedyRepair]
* `--population-size INTEGER`: Population size  [default: 100]
* `--num-evaluations INTEGER`: Number of evaluations  [default: 100000]
* `--cut-off-criteria [MinConfidence|MaxNumLinksBestConf|MinConfFreq]`: Criteria for determining which links will be part of the final binary matrix.  [default: MinConfFreq]
* `--cut-off-value FLOAT`: Numeric value associated with the selected criterion. Ex: MinConfidence = 0.5, MaxNumLinksBestConf = 10, MinConfFreq = 0.2  [default: 0.2]
* `--no-graphics / --no-no-graphics`: Indicate if you do not want to represent the evolution of the fitness value.  [default: False]
* `--output-dir PATH`: Path to the output folder.  [default: inferred_networks]
* `--help`: Show this message and exit.


# Techniques contemplated 
- GENIE3:
    - Python: https://arboreto.readthedocs.io/en/latest/ (GENIE3.py) (C) --> Te permite RF, ET y GBM

- CLR: 
    - R: https://www.bioconductor.org/packages/release/bioc/html/minet.html (CLR.R) (NC)

- ARACNE:
    - R: https://www.bioconductor.org/packages/release/bioc/html/minet.html (ARACNE.R) (NC)

- MRNET:
    - R: https://www.bioconductor.org/packages/release/bioc/html/minet.html (MRNET.R) (NC)

- MRNETB:
    - R: https://www.bioconductor.org/packages/release/bioc/html/minet.html (MRNETB.R) (NC)

- C3NET
    - R: https://cran.rstudio.com/web/packages/c3net/index.html (C3NET.R) (NC)

- BC3NET 
    - R: https://cran.rstudio.com/web/packages/bc3net/index.html (BC3NET.R) (C)

- PCIT
    - R: http://www.bioconductor.org/packages/release/bioc/html/CeTF.html (PCIT.R) (NC)

- TIGRESS
    - R: https://github.com/jpvert/tigress (TIGRESS.R) (C)

- KBOOST
    - R: http://www.bioconductor.org/packages/release/bioc/html/KBoost.html (KBOOST.R) (NC)

## Annotations

Respecto a GENIE3, CLR, ARACNE, MRNET y MRNETB:
 - GENIE3 se implementa en el paquete GENIE3
 - CLR, ARACNE, MRNET y MRNETB se implementan en minet
 - BioNERO es un paquete reciente de R/Bioconductor pero llama a los dos anteriores para usar GENIE3, CLR y ARACNE. Aunque sea más actual, simplemente llama a librerías antiguas simplificando los parámetros de entrada (lo cual no nos interesa). Además de que no implementa ni MRNET ni MRNETB, por eso se han escogido los paquetes antiguos.

Respecto a C3NET y BC3NET:
 - Tienen muchos parámetros que no entiendo, preguntar cuáles combinaciones se podrían probar

 Respecto a JUMP3:
 - Se ha intentado utilizar el código del siguiente repositorio: https://github.com/vahuynh/Jump3.
 - En local y con la última versión de Matlab dá error en una función random.
 - Para probar con otras versiones de Matlab empecé a usar contenedores pero al requerir licencia es muy complicado. En primer lugar, el id del ordenador donde se instala la licencia debe ser el mismo que donde se ejecuta el script, por lo que su uso dentro de docker no me funciona. Además habría que añadir parámetros adicionales al script principal únicamente requeridos en caso de escoger esta técnica de inferencia. 
 - En caso de lograr que se ejecutase y saber solventar el problema de la licencia, no tengo ni idea de como poder pasarle los parámetros de entrada al script de matlab.