## NAME

JUMP3

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

Given a CSV file with differential expression data, this component infers its gene regulatory network by applying the JUMP3 technique.

# DOCKER

## Build

```
docker build -t adriansegura99/geneci_infer-network_jump3 -f components/infer_network/JUMP3/Dockerfile .
```

## Run

```
docker run -v /mnt/home/adrian/.matlab/R2022a_licenses/license_workstation-15_1071290_R2022a.lic:/licenses/license.lic -e MLM_LICENSE_FILE=/licenses/license.lic adriansegura99/geneci_infer-network_jump3 expression_data.csv inferred_networks
```
