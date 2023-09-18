## NAME

Optimize Ensemble

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

This component is responsible for reading different trust lists and creating an optimal consensus network from them by applying an evolutionary algorithm.

# DOCKER

## Build

```
<<<<<<< HEAD
docker build -t adriansegura99/geneci_optimize-ensemble:1.0.0 -f components/optimize_ensemble/Dockerfile .
=======
docker build -t adriansegura99/geneci_optimize-ensemble:2.0.0 -f components/optimize_ensemble/Dockerfile .
>>>>>>> dev
```

## Run

```
docker run -v $(pwd)/tmp:/usr/local/src/tmp/ adriansegura99/geneci_optimize-ensemble tmp/dream4_010_01_exp/ 0.9 3 0.1 0.1 StandardizationRepairer 100 25000 MinConfDist 0.5 Quality;DegreeDistribution NSGAII 8 false
```
