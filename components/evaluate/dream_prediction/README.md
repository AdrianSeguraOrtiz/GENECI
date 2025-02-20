## NAME

Evaluate Dream Challenges

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

This component is responsible for evaluating the accuracy with which networks belonging to the DREAM challenges are predicted.

# DOCKER

## Build

```
<<<<<<< HEAD
docker build -t adriansegura99/geneci_evaluate_dream-prediction:4.0.0 -f components/evaluate/dream_prediction/Dockerfile .
=======
docker build -t adriansegura99/geneci_evaluate_dream-prediction:4.0.0 -f components/evaluate/dream_prediction/Dockerfile .
>>>>>>> dev
```

## Run

```
docker run -v $(pwd)/tmp:/usr/local/src/tmp/ adriansegura99/geneci_evaluate_dream-prediction --challenge D4C2 --network-id 10_1 synapse-folder input_data/DREAM4/EVAL --confidence-list ./tmp/final_list.csv
```
