## Data extraction
docker build -t eagrn-inference/extract_data/dream3 -f components/extract_data/DREAM3/Dockerfile .
docker build -t eagrn-inference/extract_data/dream4/expgs -f components/extract_data/DREAM4/EXPGS/Dockerfile .
docker build -t eagrn-inference/extract_data/dream4/eval -f components/extract_data/DREAM4/EVAL/Dockerfile .
docker build -t eagrn-inference/extract_data/dream5 -f components/extract_data/DREAM5/Dockerfile .
docker build -t eagrn-inference/extract_data/grndata -f components/extract_data/GRNDATA/Dockerfile .
docker build -t eagrn-inference/extract_data/irma -f components/extract_data/IRMA/Dockerfile .

## Network inference
docker build -t eagrn-inference/infer_network/aracne -f components/infer_network/ARACNE/Dockerfile .
docker build -t eagrn-inference/infer_network/bc3net -f components/infer_network/BC3NET/Dockerfile .
docker build -t eagrn-inference/infer_network/c3net -f components/infer_network/C3NET/Dockerfile .
docker build -t eagrn-inference/infer_network/clr -f components/infer_network/CLR/Dockerfile .
docker build -t eagrn-inference/infer_network/genie3 -f components/infer_network/GENIE3/Dockerfile .
docker build -t eagrn-inference/infer_network/mrnet -f components/infer_network/MRNET/Dockerfile .
docker build -t eagrn-inference/infer_network/mrnetb -f components/infer_network/MRNETB/Dockerfile .
docker build -t eagrn-inference/infer_network/pcit -f components/infer_network/PCIT/Dockerfile .
docker build -t eagrn-inference/infer_network/tigress -f components/infer_network/TIGRESS/Dockerfile .
docker build -t eagrn-inference/infer_network/kboost -f components/infer_network/KBOOST/Dockerfile .

## Ensemble optimisation
docker build -t eagrn-inference/optimize_ensemble -f components/optimize_ensemble/Dockerfile .

## Application of cut-off criteria (confidence list -> binary network)
docker build -t eagrn-inference/apply_cut -f components/apply_cut/Dockerfile .

## Network assessment
docker build -t eagrn-inference/evaluate/generic_prediction -f components/evaluate/generic_prediction/Dockerfile .
docker build -t eagrn-inference/evaluate/dream_prediction -f components/evaluate/dream_prediction/Dockerfile .

## Graphical representation of networks
docker build -t eagrn-inference/draw_network -f components/draw_network/Dockerfile .