## NAME

Draw Network

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

This component is responsible for drawing gene regulatory networks from confidence lists.

# DOCKER

## Build

```
<<<<<<< HEAD
docker build -t adriansegura99/geneci_draw-network:4.0.0 -f components/draw_network/Dockerfile .
=======
docker build -t adriansegura99/geneci_draw-network:4.0.0 -f components/draw_network/Dockerfile .
>>>>>>> dev
```

## Run

```
docker run -v $(pwd)/tmp:/usr/local/src/tmp/ adriansegura99/geneci_draw-network --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_ARACNE.csv --output-folder network_graphics
```
