## NAME

Draw Network

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

This component is responsible for drawing gene regulatory networks from confidence lists.

# DOCKER

## Build

```
docker build -t adriansegura99/geneci_draw-network -f components/draw_network/Dockerfile .
```

## Run

```
docker run -v $(pwd)/tmp:/usr/local/src/tmp/ adriansegura99/geneci_draw-network --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_ARACNE.csv --output-folder network_graphics
```
