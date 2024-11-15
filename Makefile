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
	@docker build -t adriansegura99/geneci_extract-data_dream3:2.5.1 -f components/extract_data/DREAM3/Dockerfile .
	@docker build -t adriansegura99/geneci_extract-data_dream4-expgs:2.5.1 -f components/extract_data/DREAM4/EXPGS/Dockerfile .
	@docker build -t adriansegura99/geneci_extract-data_dream4-eval:2.5.1 -f components/extract_data/DREAM4/EVAL/Dockerfile .
	@docker build -t adriansegura99/geneci_extract-data_dream5:2.5.1 -f components/extract_data/DREAM5/Dockerfile .
	@docker build -t adriansegura99/geneci_extract-data_grndata:2.5.1 -f components/extract_data/GRNDATA/Dockerfile .
	@docker build -t adriansegura99/geneci_extract-data_irma:2.5.1 -f components/extract_data/IRMA/Dockerfile .
	@cd components/generate_data/SysGenSIM && matlab -nodisplay -nodesktop -r "run build.m" && cd adriansegura99/geneci_generate-data_sysgensimdocker && sed -i '4,8d' Dockerfile && docker build -t adriansegura99/geneci_generate-data_sysgensim:2.5.1 . && cd ../../../../..
	@docker build -t adriansegura99/geneci_infer-network_aracne:2.5.1 -f components/infer_network/ARACNE/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_bc3net:2.5.1 -f components/infer_network/BC3NET/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_c3net:2.5.1 -f components/infer_network/C3NET/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_clr:2.5.1 -f components/infer_network/CLR/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_genie3:2.5.1 -f components/infer_network/GENIE3/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_mrnet:2.5.1 -f components/infer_network/MRNET/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_mrnetb:2.5.1 -f components/infer_network/MRNETB/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_pcit:2.5.1 -f components/infer_network/PCIT/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_tigress:2.5.1 -f components/infer_network/TIGRESS/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_kboost:2.5.1 -f components/infer_network/KBOOST/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_meomi:2.5.1 -f components/infer_network/MEOMI/Dockerfile .
	@cd components/infer_network/JUMP3/ && matlab -nodisplay -nodesktop -r "run build.m" && cd adriansegura99/geneci_infer-network_jump3docker && sed -i '4,8d' Dockerfile && docker build -t adriansegura99/geneci_infer-network_jump3:2.5.1 . && cd ../../../../..
	@cd components/infer_network/NARROMI/ && matlab -nodisplay -nodesktop -r "run build.m" && cd adriansegura99/geneci_infer-network_narromidocker && sed -i '4,8d' Dockerfile && docker build -t adriansegura99/geneci_infer-network_narromi:2.5.1 . && cd ../../../../..
	@cd components/infer_network/CMI2NI/ && matlab -nodisplay -nodesktop -r "run build.m" && cd adriansegura99/geneci_infer-network_cmi2nidocker && sed -i '4,8d' Dockerfile && docker build -t adriansegura99/geneci_infer-network_cmi2ni:2.5.1 . && cd ../../../../..
	@cd components/infer_network/RSNET/ && matlab -nodisplay -nodesktop -r "run build.m" && cd adriansegura99/geneci_infer-network_rsnetdocker && sed -i '4,8d' Dockerfile && docker build -t adriansegura99/geneci_infer-network_rsnet:2.5.1 . && cd ../../../../..
	@cd components/infer_network/PCACMI/ && matlab -nodisplay -nodesktop -r "run build.m" && cd adriansegura99/geneci_infer-network_pcacmidocker && sed -i '4,8d' Dockerfile && docker build -t adriansegura99/geneci_infer-network_pcacmi:2.5.1 . && cd ../../../../..
	@bash components/infer_network/LOCPCACMI/build.sh
	@cd components/infer_network/PLSNET/ && matlab -nodisplay -nodesktop -r "run build.m" && cd adriansegura99/geneci_infer-network_plsnetdocker && sed -i '4,8d' Dockerfile && docker build -t adriansegura99/geneci_infer-network_plsnet:2.5.1 . && cd ../../../../..
	@docker build -t adriansegura99/geneci_infer-network_pidc:2.5.1 -f components/infer_network/PIDC/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_puc:2.5.1 -f components/infer_network/PUC/Dockerfile .
	@cd components/infer_network/GRNVBEM/ && matlab -nodisplay -nodesktop -r "run build.m" && cd adriansegura99/geneci_infer-network_grnvbemdocker && sed -i '4,8d' Dockerfile && docker build -t adriansegura99/geneci_infer-network_grnvbem:2.5.1 . && cd ../../../../..
	@docker build -t adriansegura99/geneci_infer-network_leap:2.5.1 -f components/infer_network/LEAP/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_nonlinearodes:2.5.1 -f components/infer_network/NONLINEARODES/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_inferelator:2.5.1 -f components/infer_network/INFERELATOR/Dockerfile .
	@docker build -t adriansegura99/geneci_optimize-ensemble:2.5.1 -f components/optimize_ensemble/Dockerfile .
	@docker build -t adriansegura99/geneci_apply-cut:2.5.1 -f components/apply_cut/Dockerfile .
	@docker build -t adriansegura99/geneci_evaluate_generic-prediction:2.5.1 -f components/evaluate/generic_prediction/Dockerfile .
	@docker build -t adriansegura99/geneci_evaluate_dream-prediction:2.5.1 -f components/evaluate/dream_prediction/Dockerfile .
	@docker build -t adriansegura99/geneci_draw-network:2.5.1 -f components/draw_network/Dockerfile .
	@docker build -t adriansegura99/geneci_weighted-confidence:2.5.1 -f components/weighted_confidence/Dockerfile .
	@docker build -t adriansegura99/geneci_cluster-network:2.5.1 -f components/cluster_network/Dockerfile .

push-images:
	@docker push adriansegura99/geneci_extract-data_dream3:2.5.1
	@docker push adriansegura99/geneci_extract-data_dream4-expgs:2.5.1
	@docker push adriansegura99/geneci_extract-data_dream4-eval:2.5.1
	@docker push adriansegura99/geneci_extract-data_dream5:2.5.1
	@docker push adriansegura99/geneci_extract-data_grndata:2.5.1
	@docker push adriansegura99/geneci_extract-data_irma:2.5.1
	@docker push adriansegura99/geneci_generate-data_sysgensim:2.5.1
	@docker push adriansegura99/geneci_infer-network_aracne:2.5.1
	@docker push adriansegura99/geneci_infer-network_bc3net:2.5.1
	@docker push adriansegura99/geneci_infer-network_c3net:2.5.1
	@docker push adriansegura99/geneci_infer-network_clr:2.5.1
	@docker push adriansegura99/geneci_infer-network_genie3:2.5.1
	@docker push adriansegura99/geneci_infer-network_mrnet:2.5.1
	@docker push adriansegura99/geneci_infer-network_mrnetb:2.5.1
	@docker push adriansegura99/geneci_infer-network_pcit:2.5.1
	@docker push adriansegura99/geneci_infer-network_tigress:2.5.1
	@docker push adriansegura99/geneci_infer-network_kboost:2.5.1
	@docker push adriansegura99/geneci_infer-network_meomi:2.5.1
	@docker push adriansegura99/geneci_infer-network_jump3:2.5.1
	@docker push adriansegura99/geneci_infer-network_narromi:2.5.1
	@docker push adriansegura99/geneci_infer-network_cmi2ni:2.5.1
	@docker push adriansegura99/geneci_infer-network_rsnet:2.5.1
	@docker push adriansegura99/geneci_infer-network_pcacmi:2.5.1
	@docker push adriansegura99/geneci_infer-network_locpcacmi:2.5.1
	@docker push adriansegura99/geneci_infer-network_plsnet:2.5.1
	@docker push adriansegura99/geneci_infer-network_pidc:2.5.1
	@docker push adriansegura99/geneci_infer-network_puc:2.5.1
	@docker push adriansegura99/geneci_infer-network_grnvbem:2.5.1
	@docker push adriansegura99/geneci_infer-network_leap:2.5.1
	@docker push adriansegura99/geneci_infer-network_nonlinearodes:2.5.1
	@docker push adriansegura99/geneci_infer-network_inferelator:2.5.1
	@docker push adriansegura99/geneci_optimize-ensemble:2.5.1
	@docker push adriansegura99/geneci_apply-cut:2.5.1
	@docker push adriansegura99/geneci_evaluate_generic-prediction:2.5.1
	@docker push adriansegura99/geneci_evaluate_dream-prediction:2.5.1
	@docker push adriansegura99/geneci_draw-network:2.5.1
	@docker push adriansegura99/geneci_weighted-confidence:2.5.1
	@docker push adriansegura99/geneci_cluster-network:2.5.1

pull-images:
	@docker pull adriansegura99/geneci_extract-data_dream3:2.5.1
	@docker pull adriansegura99/geneci_extract-data_dream4-expgs:2.5.1
	@docker pull adriansegura99/geneci_extract-data_dream4-eval:2.5.1
	@docker pull adriansegura99/geneci_extract-data_dream5:2.5.1
	@docker pull adriansegura99/geneci_extract-data_grndata:2.5.1
	@docker pull adriansegura99/geneci_extract-data_irma:2.5.1
	@docker pull adriansegura99/geneci_generate-data_sysgensim:2.5.1
	@docker pull adriansegura99/geneci_infer-network_aracne:2.5.1
	@docker pull adriansegura99/geneci_infer-network_bc3net:2.5.1
	@docker pull adriansegura99/geneci_infer-network_c3net:2.5.1
	@docker pull adriansegura99/geneci_infer-network_clr:2.5.1
	@docker pull adriansegura99/geneci_infer-network_genie3:2.5.1
	@docker pull adriansegura99/geneci_infer-network_mrnet:2.5.1
	@docker pull adriansegura99/geneci_infer-network_mrnetb:2.5.1
	@docker pull adriansegura99/geneci_infer-network_pcit:2.5.1
	@docker pull adriansegura99/geneci_infer-network_tigress:2.5.1
	@docker pull adriansegura99/geneci_infer-network_kboost:2.5.1
	@docker pull adriansegura99/geneci_infer-network_meomi:2.5.1
	@docker pull adriansegura99/geneci_infer-network_jump3:2.5.1
	@docker pull adriansegura99/geneci_infer-network_narromi:2.5.1
	@docker pull adriansegura99/geneci_infer-network_cmi2ni:2.5.1
	@docker pull adriansegura99/geneci_infer-network_rsnet:2.5.1
	@docker pull adriansegura99/geneci_infer-network_pcacmi:2.5.1
	@docker pull adriansegura99/geneci_infer-network_locpcacmi:2.5.1
	@docker pull adriansegura99/geneci_infer-network_plsnet:2.5.1
	@docker pull adriansegura99/geneci_infer-network_pidc:2.5.1
	@docker pull adriansegura99/geneci_infer-network_puc:2.5.1
	@docker pull adriansegura99/geneci_infer-network_grnvbem:2.5.1
	@docker pull adriansegura99/geneci_infer-network_leap:2.5.1
	@docker pull adriansegura99/geneci_infer-network_nonlinearodes:2.5.1
	@docker pull adriansegura99/geneci_infer-network_inferelator:2.5.1
	@docker pull adriansegura99/geneci_optimize-ensemble:2.5.1
	@docker pull adriansegura99/geneci_apply-cut:2.5.1
	@docker pull adriansegura99/geneci_evaluate_generic-prediction:2.5.1
	@docker pull adriansegura99/geneci_evaluate_dream-prediction:2.5.1
	@docker pull adriansegura99/geneci_draw-network:2.5.1
	@docker pull adriansegura99/geneci_weighted-confidence:2.5.1
	@docker pull adriansegura99/geneci_cluster-network:2.5.1

release:
	@echo Bump version to v$$(poetry version --short)
	@git tag v$$(poetry version --short)
	@git push origin v$$(poetry version --short)