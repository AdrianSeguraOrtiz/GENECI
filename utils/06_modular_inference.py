from pathlib import Path
from geneci.main import modular_inference, SimpleConsensusCriteria, ClusteringAlgorithm, Technique
import glob

# Establecer carpeta de trabajo y lista de datos de expresion de más de 500 genes
working_dir = "../modular_experiments_test/"
expression_data = glob.glob(working_dir + "*/*.csv")
print(f"Expression data files found: {expression_data}")

# Establecer parámetros con valores fijos
global_techniques=[Technique.ARACNE, Technique.CLR, Technique.MRNET, Technique.C3NET]
modular_techniques_all=[Technique.GENIE3_ET, Technique.GENIE3_RF, Technique.GRNBOOST2, Technique.PCACMI, Technique.TIGRESS]
modular_techniques_small=[Technique.CMI2NI, Technique.INFERELATOR, Technique.RSNET]

# Establecer opciones de parámetros
consensus_options = [SimpleConsensusCriteria.RankAverage, SimpleConsensusCriteria.MeanWeights]
clustering_algorithms = [ca for ca in ClusteringAlgorithm]
preferred_size = [50, 100, 150, 200]

# 1. Inferencia modular de todas las redes con todas las opciones de parametros
for expression_file in expression_data:
    for consensus in consensus_options:
        for clustering_algorithm in clustering_algorithms:
            for size in preferred_size:
                print(f"Running modular inference for {expression_file} with consensus {consensus}, algorithm {clustering_algorithm}, and preferred size {size}")
                modular_techniques = modular_techniques_all if size > 100 else modular_techniques_all + modular_techniques_small
                output_dir = f"{Path(expression_file).parent}/{consensus}_{clustering_algorithm}_{size}"
                modular_inference(
                    expression_data=Path(expression_file),
                    global_techniques=global_techniques,
                    modular_techniques=modular_techniques,
                    consensus_criteria=consensus,
                    algorithm=clustering_algorithm,
                    preferred_size=size,
                    threads=120,
                    output_dir=Path(output_dir)
                )

# 2. Calcular precisión de redes parciales para técnicas ligeras (extracción de la global), técnicas pesadas, consenso de ligeras (consenso de extracciones) y consenso de pesadas

# 3. Calcular precisión de red global para técnicas ligeras, consenso de técnicas ligeras y producto final construido

# 4. Crear gráfico de comparación de BIO-INSIGHT vs. Estrategia modular