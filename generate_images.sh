## Data extraction
docker build -t adriansegura99/geneci_extract-data_dream3 -f components/extract_data/DREAM3/Dockerfile .
docker build -t adriansegura99/geneci_extract-data_dream4-expgs -f components/extract_data/DREAM4/EXPGS/Dockerfile .
docker build -t adriansegura99/geneci_extract-data_dream4-eval -f components/extract_data/DREAM4/EVAL/Dockerfile .
docker build -t adriansegura99/geneci_extract-data_dream5 -f components/extract_data/DREAM5/Dockerfile .
docker build -t adriansegura99/geneci_extract-data_grndata -f components/extract_data/GRNDATA/Dockerfile .
docker build -t adriansegura99/geneci_extract-data_irma -f components/extract_data/IRMA/Dockerfile .

## Network inference
docker build -t adriansegura99/geneci_infer-network_aracne -f components/infer_network/ARACNE/Dockerfile .
docker build -t adriansegura99/geneci_infer-network_bc3net -f components/infer_network/BC3NET/Dockerfile .
docker build -t adriansegura99/geneci_infer-network_c3net -f components/infer_network/C3NET/Dockerfile .
docker build -t adriansegura99/geneci_infer-network_clr -f components/infer_network/CLR/Dockerfile .
docker build -t adriansegura99/geneci_infer-network_genie3 -f components/infer_network/GENIE3/Dockerfile .
docker build -t adriansegura99/geneci_infer-network_mrnet -f components/infer_network/MRNET/Dockerfile .
docker build -t adriansegura99/geneci_infer-network_mrnetb -f components/infer_network/MRNETB/Dockerfile .
docker build -t adriansegura99/geneci_infer-network_pcit -f components/infer_network/PCIT/Dockerfile .
docker build -t adriansegura99/geneci_infer-network_tigress -f components/infer_network/TIGRESS/Dockerfile .
docker build -t adriansegura99/geneci_infer-network_kboost -f components/infer_network/KBOOST/Dockerfile .

## Ensemble optimisation
docker build -t adriansegura99/geneci_optimize-ensemble -f components/optimize_ensemble/Dockerfile .

## Application of cut-off criteria (confidence list -> binary network)
docker build -t adriansegura99/geneci_apply-cut -f components/apply_cut/Dockerfile .

## Network assessment
docker build -t adriansegura99/geneci_evaluate_generic-prediction -f components/evaluate/generic_prediction/Dockerfile .
docker build -t adriansegura99/geneci_evaluate_dream-prediction -f components/evaluate/dream_prediction/Dockerfile .

## Graphical representation of networks
docker build -t adriansegura99/geneci_draw-network -f components/draw_network/Dockerfile .