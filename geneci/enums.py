from enum import Enum


class Topology(str, Enum):
    Random = "random"
    RandomAcyclic = "random-acyclic"
    ScaleFree = "scale-free"
    SmallWorld = "small-world"
    Eipo = "eipo"
    RandomModular = "random-modular"
    EipoModular = "eipo-modular"


class Perturbation(str, Enum):
    Knockout = "knockout"
    Knockdown = "knockdown"
    Overexpression = "overexpression"
    Mixed = "mixed"


class FromRealGenerateDatabase(str, Enum):
    TFLink = "TFLink"
    RegulonDB = "RegulonDB"
    RegNetwork = "RegNetwork"
    BioGrid = "BioGrid"
    GRNdb = "GRNdb"


real_networks_dict = {
    "TFLink": [
        "Caenorhabditis_elegans",
        "Drosophila_melanogaster",
        "Rattus_norvegicus",
        "Saccharomyces_cerevisiae",
    ],
    "RegulonDB": ["Escherichia_coli"],
    "RegNetwork": ["human", "mouse"],
    "BioGrid": [
        "Human_papillomavirus_5",
        "Human_papillomavirus_6b",
        "Bacillus_subtilis_168",
        "Bos_taurus",
        "Macaca_mulatta",
        "Middle-East_Respiratory_Syndrome-related_Coronavirus",
        "Canis_familiaris",
        "Chlamydomonas_reinhardtii",
        "Chlorocebus_sabaeus",
        "Neurospora_crassa_OR74A",
        "Cricetulus_griseus",
        "Danio_rerio",
        "Oryctolagus_cuniculus",
        "Oryza_sativa_Japonica",
        "Emericella_nidulans_FGSC_A4",
        "Plasmodium_falciparum_3D7",
        "Gallus_gallus",
        "Glycine_max",
        "Simian_Immunodeficiency_Virus",
        "Human_Herpesvirus_1",
        "Simian_Virus_40",
        "Human_Herpesvirus_4",
        "Human_Herpesvirus_5",
        "Streptococcus_pneumoniae_ATCCBAA255",
        "Strongylocentrotus_purpuratus",
        "Sus_scrofa",
        "Human_Herpesvirus_8",
        "Vaccinia_Virus",
        "Human_Immunodeficiency_Virus_2",
        "Xenopus_laevis",
        "Human_papillomavirus_16",
        "Zea_mays",
    ],
    "GRNdb": [
        "Fetal-Brain",
        "Fetal-Thymus",
        "Adult-Pancreas",
        "Adult-Muscle",
        "Adult-Adipose",
        "Adult-Ascending-Colon",
        "Adult-Lung",
        "Adult-Liver",
        "Fetal-Calvaria",
        "Adult-Epityphlon",
        "Adult-Rectum",
    ],
}


class Database(str, Enum):
    DREAM3 = "DREAM3"
    DREAM4 = "DREAM4"
    DREAM5 = "DREAM5"
    SynTReN = "SynTReN"
    Rogers = "Rogers"
    GeneNetWeaver = "GeneNetWeaver"
    IRMA = "IRMA"


class EvalDatabase(str, Enum):
    DREAM3 = "DREAM3"
    DREAM4 = "DREAM4"
    DREAM5 = "DREAM5"


class Technique(str, Enum):
    ARACNE = "ARACNE"
    BC3NET = "BC3NET"
    C3NET = "C3NET"
    CLR = "CLR"
    GENIE3_RF = "GENIE3_RF"
    GRNBOOST2 = "GRNBOOST2"
    GENIE3_ET = "GENIE3_ET"
    MRNET = "MRNET"
    MRNETB = "MRNETB"
    PCIT = "PCIT"
    TIGRESS = "TIGRESS"
    KBOOST = "KBOOST"
    MEOMI = "MEOMI"
    JUMP3 = "JUMP3"
    NARROMI = "NARROMI"
    CMI2NI = "CMI2NI"
    RSNET = "RSNET"
    PCACMI = "PCACMI"
    LOCPCACMI = "LOCPCACMI"
    PLSNET = "PLSNET"
    PIDC = "PIDC"
    PUC = "PUC"
    GRNVBEM = "GRNVBEM"
    LEAP = "LEAP"
    NONLINEARODES = "NONLINEARODES"
    INFERELATOR = "INFERELATOR"


class CutOffCriteria(str, Enum):
    MinConf = "MinConf"
    NumLinksWithBestConf = "NumLinksWithBestConf"
    PercLinksWithBestConf = "PercLinksWithBestConf"


class Challenge(str, Enum):
    D3C4 = "D3C4"
    D4C2 = "D4C2"
    D5C4 = "D5C4"


class NodesDistribution(str, Enum):
    Spring = "Spring"
    Circular = "Circular"
    Kamada_kawai = "Kamada_kawai"


class Mode(str, Enum):
    Static2D = "Static2D"
    Interactive2D = "Interactive2D"
    Compare2D = "Compare2D"
    Interactive3D = "Interactive3D"


class Algorithm(str, Enum):
    GA = "GA"
    NSGAII = "NSGAII"
    NSGAIIExternalFile = "NSGAIIExternalFile"
    SMPSO = "SMPSO"


class MemeticDistanceType(str, Enum):
    all = "all"
    some = "some"
    one = "one"


class SimpleConsensusCriteria(str, Enum):
    MeanWeights = "MeanWeights"
    MedianWeights = "MedianWeights"
    RankAverage = "RankAverage"
    BayesianFusion = "BayesianFusion"
