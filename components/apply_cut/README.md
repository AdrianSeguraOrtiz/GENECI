## NAME

Apply Cut

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

This component is in charge of converting confidence lists into binary matrices by applying several criteria.

# DOCKER

## Build

```
<<<<<<< HEAD
docker build -t adriansegura99/geneci_apply-cut:4.0.0 -f components/apply_cut/Dockerfile .
=======
docker build -t adriansegura99/geneci_apply-cut:4.0.0 -f components/apply_cut/Dockerfile .
>>>>>>> dev
```

## Run

```
docker run -v $(pwd)/tmp:/usr/local/src/tmp/ adriansegura99/geneci_apply-cut inferred_networks/dream4_010_01_exp/lists/GRN_ARACNE.csv inferred_networks/dream4_010_01_exp/gene_names.txt inferred_networks/dream4_010_01_exp/networks/GRN_ARACNE.csv MinConfidence 0.1
```
