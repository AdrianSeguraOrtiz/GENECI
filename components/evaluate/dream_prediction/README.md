## NAME

Evaluate Dream Challenges

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

This component is responsible for evaluating the accuracy with which networks belonging to the DREAM challenges are predicted.

# DOCKER

## Build

```
docker build -t eagrn-inference/evaluate/dream_prediction -f components/evaluate/dream_prediction/Dockerfile .
```

## Run

```
docker run -v $(pwd)/tmp:/usr/local/src/tmp/ eagrn-inference/evaluate/dream_prediction --challenge D4C2 --network-id 10_1 synapse-folder input_data/DREAM4/EVAL --confidence-list ./tmp/final_list.csv
```
