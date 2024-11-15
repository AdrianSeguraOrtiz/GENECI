## NAME

RSNET

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

Given a CSV file with time series of gene expression data, this component infers its gene regulatory network by applying the RSNET technique.

# DOCKER

## Build

```
cd components/infer_network/RSNET/ && matlab -nodisplay -nodesktop -r "run build.m" && cd adriansegura99/geneci_infer-network_rsnetdocker && sed -i '4,8d' Dockerfile && docker build -t adriansegura99/geneci_infer-network_rsnet:2.5.1 . && cd ../../../../..
```

## Run

```
docker run -v $(pwd)/tmp:/tmp/.X11-unix/tmp adriansegura99/geneci_infer-network_rsnet tmp/.X11-unix/tmp/InSilicoSize10-Ecoli1-trajectories_exp.csv tmp/.X11-unix/tmp
```
