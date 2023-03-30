install:
	@poetry install

build:
	@poetry build

clean:
	@find . -type d -name '.mypy_cache' -exec rm -rf {} +
	@find . -type d -name '__pycache__' -exec rm -rf {} +

black:
	@poetry run isort --profile black geneci/main.py
	@poetry run black geneci/main.py

build-images:
	@mvn -f ./EAGRN-JMetal/pom.xml clean compile assembly:single
	@docker build -t adriansegura99/geneci_extract-data_dream3:1.0.0 -f components/extract_data/DREAM3/Dockerfile .
	@docker build -t adriansegura99/geneci_extract-data_dream4-expgs:1.0.0 -f components/extract_data/DREAM4/EXPGS/Dockerfile .
	@docker build -t adriansegura99/geneci_extract-data_dream4-eval:1.0.0 -f components/extract_data/DREAM4/EVAL/Dockerfile .
	@docker build -t adriansegura99/geneci_extract-data_dream5:1.0.0 -f components/extract_data/DREAM5/Dockerfile .
	@docker build -t adriansegura99/geneci_extract-data_grndata:1.0.0 -f components/extract_data/GRNDATA/Dockerfile .
	@docker build -t adriansegura99/geneci_extract-data_irma:1.0.0 -f components/extract_data/IRMA/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_aracne:1.0.0 -f components/infer_network/ARACNE/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_bc3net:1.0.0 -f components/infer_network/BC3NET/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_c3net:1.0.0 -f components/infer_network/C3NET/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_clr:1.0.0 -f components/infer_network/CLR/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_genie3:1.0.0 -f components/infer_network/GENIE3/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_mrnet:1.0.0 -f components/infer_network/MRNET/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_mrnetb:1.0.0 -f components/infer_network/MRNETB/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_pcit:1.0.0 -f components/infer_network/PCIT/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_tigress:1.0.0 -f components/infer_network/TIGRESS/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_kboost:1.0.0 -f components/infer_network/KBOOST/Dockerfile .
	@docker build -t adriansegura99/geneci_optimize-ensemble:1.0.0 -f components/optimize_ensemble/Dockerfile .
	@docker build -t adriansegura99/geneci_apply-cut:1.0.0 -f components/apply_cut/Dockerfile .
	@docker build -t adriansegura99/geneci_evaluate_generic-prediction:1.0.0 -f components/evaluate/generic_prediction/Dockerfile .
	@docker build -t adriansegura99/geneci_evaluate_dream-prediction:1.0.0 -f components/evaluate/dream_prediction/Dockerfile .
	@docker build -t adriansegura99/geneci_draw-network:1.0.0 -f components/draw_network/Dockerfile .

push-images:
	@docker push adriansegura99/geneci_extract-data_dream3:1.0.0
	@docker push adriansegura99/geneci_extract-data_dream4-expgs:1.0.0
	@docker push adriansegura99/geneci_extract-data_dream4-eval:1.0.0
	@docker push adriansegura99/geneci_extract-data_dream5:1.0.0
	@docker push adriansegura99/geneci_extract-data_grndata:1.0.0
	@docker push adriansegura99/geneci_extract-data_irma:1.0.0
	@docker push adriansegura99/geneci_infer-network_aracne:1.0.0
	@docker push adriansegura99/geneci_infer-network_bc3net:1.0.0
	@docker push adriansegura99/geneci_infer-network_c3net:1.0.0
	@docker push adriansegura99/geneci_infer-network_clr:1.0.0
	@docker push adriansegura99/geneci_infer-network_genie3:1.0.0
	@docker push adriansegura99/geneci_infer-network_mrnet:1.0.0
	@docker push adriansegura99/geneci_infer-network_mrnetb:1.0.0
	@docker push adriansegura99/geneci_infer-network_pcit:1.0.0
	@docker push adriansegura99/geneci_infer-network_tigress:1.0.0
	@docker push adriansegura99/geneci_infer-network_kboost:1.0.0
	@docker push adriansegura99/geneci_optimize-ensemble:1.0.0
	@docker push adriansegura99/geneci_apply-cut:1.0.0
	@docker push adriansegura99/geneci_evaluate_generic-prediction:1.0.0
	@docker push adriansegura99/geneci_evaluate_dream-prediction:1.0.0
	@docker push adriansegura99/geneci_draw-network:1.0.0

pull-images:
	@docker pull adriansegura99/geneci_extract-data_dream3:1.0.0
	@docker pull adriansegura99/geneci_extract-data_dream4-expgs:1.0.0
	@docker pull adriansegura99/geneci_extract-data_dream4-eval:1.0.0
	@docker pull adriansegura99/geneci_extract-data_dream5:1.0.0
	@docker pull adriansegura99/geneci_extract-data_grndata:1.0.0
	@docker pull adriansegura99/geneci_extract-data_irma:1.0.0
	@docker pull adriansegura99/geneci_infer-network_aracne:1.0.0
	@docker pull adriansegura99/geneci_infer-network_bc3net:1.0.0
	@docker pull adriansegura99/geneci_infer-network_c3net:1.0.0
	@docker pull adriansegura99/geneci_infer-network_clr:1.0.0
	@docker pull adriansegura99/geneci_infer-network_genie3:1.0.0
	@docker pull adriansegura99/geneci_infer-network_mrnet:1.0.0
	@docker pull adriansegura99/geneci_infer-network_mrnetb:1.0.0
	@docker pull adriansegura99/geneci_infer-network_pcit:1.0.0
	@docker pull adriansegura99/geneci_infer-network_tigress:1.0.0
	@docker pull adriansegura99/geneci_infer-network_kboost:1.0.0
	@docker pull adriansegura99/geneci_optimize-ensemble:1.0.0
	@docker pull adriansegura99/geneci_apply-cut:1.0.0
	@docker pull adriansegura99/geneci_evaluate_generic-prediction:1.0.0
	@docker pull adriansegura99/geneci_evaluate_dream-prediction:1.0.0
	@docker pull adriansegura99/geneci_draw-network:1.0.0

release:
	@echo Bump version to v$$(poetry version --short)
	@git tag v$$(poetry version --short)
	@git push origin v$$(poetry version --short)