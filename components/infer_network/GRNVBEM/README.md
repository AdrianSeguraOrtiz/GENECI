## NAME

GRNVBEM

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

Given a CSV file with time series of gene expression data, this component infers its gene regulatory network by applying the GRNVBEM technique.

# DOCKER

## Build

```
cd components/infer_network/GRNVBEM/ && matlab -nodisplay -nodesktop -r "run build.m" && cd adriansegura99/geneci_infer-network_grnvbemdocker && sed -i '4,8d' Dockerfile && docker build -t adriansegura99/geneci_infer-network_grnvbem:2.5.1 . && cd ../../../../..
```

## Run

```
docker run -v $(pwd)/tmp:/tmp/.X11-unix/tmp adriansegura99/geneci_infer-network_grnvbem tmp/.X11-unix/tmp/InSilicoSize10-Ecoli1-trajectories_exp.csv tmp/.X11-unix/tmp
```
