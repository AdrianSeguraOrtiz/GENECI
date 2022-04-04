## NAME

DREAM4 Measures

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

This component is responsible for calculating the performance values associated with our evolutionary algorithm for the networks from the DREAM4 challenge.

# DOCKER

## Build

```
docker build -t eagrn-inference/dream4_measures -f components/dream4_measures/Dockerfile .
```

## Run

```
docker run -v /mnt/home/adrian/.matlab/R2022a_licenses/license_workstation-15_1071290_R2022a.lic:/licenses/license.lic -e MLM_LICENSE_FILE=/licenses/license.lic eagrn-inference/dream4_measures
```
