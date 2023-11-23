## NAME

Weighted Confidence

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

This component is responsible for calculating the weighted sum of the confidence levels reported in several files based on a given distribution of weights.

# DOCKER

## Build

```
docker build -t adriansegura99/geneci_weighted-confidence:3.0.0 -f components/weighted_confidence/Dockerfile .
```

## Run

```
docker run -v $(pwd)/tmp:/usr/local/src/tmp/ adriansegura99/geneci_weighted-confidence inferred_networks/dream4_010_01_exp/weighted_confidences.csv inferred_networks/dream4_010_01_exp/lists/GRN_ARACNE.csv*0.3 inferred_networks/dream4_010_01_exp/lists/GRN_BC3NET.csv*0.3 inferred_networks/dream4_010_01_exp/lists/GRN_CLR.csv*0.4
```
