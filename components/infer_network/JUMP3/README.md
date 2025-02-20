## NAME

JUMP3

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

Given a CSV file with time series of gene expression data, this component infers its gene regulatory network by applying the JUMP3 technique.

# DOCKER

## Build

```
<<<<<<< HEAD
docker build -t adriansegura99/geneci_infer-network_jump3:4.0.0 -f components/infer_network/JUMP3/Dockerfile .
=======
cd components/infer_network/JUMP3/ && matlab -nodisplay -nodesktop -r "run build.m" && cd adriansegura99/geneci_infer-network_jump3docker && sed -i '4,8d' Dockerfile && docker build -t adriansegura99/geneci_infer-network_jump3:4.0.0 . && cd ../../../../..
>>>>>>> dev
```

## Run

```
docker run -v $(pwd)/tmp:/tmp/.X11-unix/tmp adriansegura99/geneci_infer-network_jump3 tmp/.X11-unix/tmp/InSilicoSize10-Ecoli1-trajectories_exp.csv tmp/.X11-unix/tmp
```
