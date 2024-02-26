## NAME

SysGenSIM

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

Simulate time series with gene expression levels using the SysGenSIM simulator. They can be generated from scratch or based on the interactions of a real gene network.

# DOCKER

## Build

```
cd components/generate_data/SysGenSIM && matlab -nodisplay -nodesktop -r "run build.m" && cd adriansegura99/geneci_generate-data_sysgensimdocker && sed -i '4,8d' Dockerfile && docker build -t adriansegura99/geneci_generate-data_sysgensim:3.0.0 . && cd ../../../../..
```

## Run

From scratch:

```
docker run -v $(pwd)/tmp:/tmp/.X11-unix/tmp adriansegura99/geneci_generate-data_sysgensim '' eipo-modular 20 knockout tmp/.X11-unix/tmp/
```

Based on the interactions of a real gene network:

```
docker run -v $(pwd)/tmp:/tmp/.X11-unix/tmp adriansegura99/geneci_generate-data_sysgensim tmp/.X11-unix/tmp/real_network.txt '' '' knockout tmp/.X11-unix/tmp/
```
