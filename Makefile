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
	@docker build -t adriansegura99/geneci_extract-data_dream3 -f components/extract_data/DREAM3/Dockerfile .
	@docker build -t adriansegura99/geneci_extract-data_dream4-expgs -f components/extract_data/DREAM4/EXPGS/Dockerfile .
	@docker build -t adriansegura99/geneci_extract-data_dream4-eval -f components/extract_data/DREAM4/EVAL/Dockerfile .
	@docker build -t adriansegura99/geneci_extract-data_dream5 -f components/extract_data/DREAM5/Dockerfile .
	@docker build -t adriansegura99/geneci_extract-data_grndata -f components/extract_data/GRNDATA/Dockerfile .
	@docker build -t adriansegura99/geneci_extract-data_irma -f components/extract_data/IRMA/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_aracne -f components/infer_network/ARACNE/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_bc3net -f components/infer_network/BC3NET/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_c3net -f components/infer_network/C3NET/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_clr -f components/infer_network/CLR/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_genie3 -f components/infer_network/GENIE3/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_mrnet -f components/infer_network/MRNET/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_mrnetb -f components/infer_network/MRNETB/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_pcit -f components/infer_network/PCIT/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_tigress -f components/infer_network/TIGRESS/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_kboost -f components/infer_network/KBOOST/Dockerfile .
	@docker build -t adriansegura99/geneci_optimize-ensemble -f components/optimize_ensemble/Dockerfile .
	@docker build -t adriansegura99/geneci_apply-cut -f components/apply_cut/Dockerfile .
	@docker build -t adriansegura99/geneci_evaluate_generic-prediction -f components/evaluate/generic_prediction/Dockerfile .
	@docker build -t adriansegura99/geneci_evaluate_dream-prediction -f components/evaluate/dream_prediction/Dockerfile .
	@docker build -t adriansegura99/geneci_draw-network -f components/draw_network/Dockerfile .

push-images:
	@docker push adriansegura99/geneci_extract-data_dream3 
	@docker push adriansegura99/geneci_extract-data_dream4-expgs 
	@docker push adriansegura99/geneci_extract-data_dream4-eval 
	@docker push adriansegura99/geneci_extract-data_dream5 
	@docker push adriansegura99/geneci_extract-data_grndata 
	@docker push adriansegura99/geneci_extract-data_irma 
	@docker push adriansegura99/geneci_infer-network_aracne 
	@docker push adriansegura99/geneci_infer-network_bc3net 
	@docker push adriansegura99/geneci_infer-network_c3net 
	@docker push adriansegura99/geneci_infer-network_clr 
	@docker push adriansegura99/geneci_infer-network_genie3 
	@docker push adriansegura99/geneci_infer-network_mrnet 
	@docker push adriansegura99/geneci_infer-network_mrnetb 
	@docker push adriansegura99/geneci_infer-network_pcit 
	@docker push adriansegura99/geneci_infer-network_tigress 
	@docker push adriansegura99/geneci_infer-network_kboost 
	@docker push adriansegura99/geneci_optimize-ensemble 
	@docker push adriansegura99/geneci_apply-cut 
	@docker push adriansegura99/geneci_evaluate_generic-prediction 
	@docker push adriansegura99/geneci_evaluate_dream-prediction 
	@docker push adriansegura99/geneci_draw-network

pull-images:
	@docker pull adriansegura99/geneci_extract-data_dream3 
	@docker pull adriansegura99/geneci_extract-data_dream4-expgs 
	@docker pull adriansegura99/geneci_extract-data_dream4-eval 
	@docker pull adriansegura99/geneci_extract-data_dream5 
	@docker pull adriansegura99/geneci_extract-data_grndata 
	@docker pull adriansegura99/geneci_extract-data_irma 
	@docker pull adriansegura99/geneci_infer-network_aracne 
	@docker pull adriansegura99/geneci_infer-network_bc3net 
	@docker pull adriansegura99/geneci_infer-network_c3net 
	@docker pull adriansegura99/geneci_infer-network_clr 
	@docker pull adriansegura99/geneci_infer-network_genie3 
	@docker pull adriansegura99/geneci_infer-network_mrnet 
	@docker pull adriansegura99/geneci_infer-network_mrnetb 
	@docker pull adriansegura99/geneci_infer-network_pcit 
	@docker pull adriansegura99/geneci_infer-network_tigress 
	@docker pull adriansegura99/geneci_infer-network_kboost 
	@docker pull adriansegura99/geneci_optimize-ensemble 
	@docker pull adriansegura99/geneci_apply-cut 
	@docker pull adriansegura99/geneci_evaluate_generic-prediction 
	@docker pull adriansegura99/geneci_evaluate_dream-prediction 
	@docker pull adriansegura99/geneci_draw-network

release:
	@echo Bump version to v$$(poetry version --short)
	@git tag v$$(poetry version --short)
	@git push origin v$$(poetry version --short)