install:
	@poetry install

build:
	@poetry build

clean:
	@find . -type d -name '.mypy_cache' -exec rm -rf {} +
	@find . -type d -name '__pycache__' -exec rm -rf {} +

black:
	@poetry run isort --profile black geneci
	@poetry run black geneci

build-images:
	@mvn -f ./EAGRN-JMetal/pom.xml clean compile assembly:single
	@docker build -t adriansegura99/geneci_extract-data_dream3:5.0.0 -f components/extract_data/DREAM3/Dockerfile .
	@docker build -t adriansegura99/geneci_extract-data_dream4-expgs:5.0.0 -f components/extract_data/DREAM4/EXPGS/Dockerfile .
	@docker build -t adriansegura99/geneci_extract-data_dream4-eval:5.0.0 -f components/extract_data/DREAM4/EVAL/Dockerfile .
	@docker build -t adriansegura99/geneci_extract-data_dream5:5.0.0 -f components/extract_data/DREAM5/Dockerfile .
	@docker build -t adriansegura99/geneci_extract-data_grndata:5.0.0 -f components/extract_data/GRNDATA/Dockerfile .
	@docker build -t adriansegura99/geneci_extract-data_irma:5.0.0 -f components/extract_data/IRMA/Dockerfile .
	@cd components/generate_data/SysGenSIM && matlab -nodisplay -nodesktop -r "run build.m" && cd adriansegura99/geneci_generate-data_sysgensimdocker && sed -i '4,8d' Dockerfile && docker build -t adriansegura99/geneci_generate-data_sysgensim:5.0.0 . && cd ../../../../..
	@docker build -t adriansegura99/geneci_infer-network_aracne:5.0.0 -f components/infer_network/ARACNE/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_bc3net:5.0.0 -f components/infer_network/BC3NET/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_c3net:5.0.0 -f components/infer_network/C3NET/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_clr:5.0.0 -f components/infer_network/CLR/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_genie3:5.0.0 -f components/infer_network/GENIE3/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_mrnet:5.0.0 -f components/infer_network/MRNET/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_mrnetb:5.0.0 -f components/infer_network/MRNETB/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_pcit:5.0.0 -f components/infer_network/PCIT/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_tigress:5.0.0 -f components/infer_network/TIGRESS/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_kboost:5.0.0 -f components/infer_network/KBOOST/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_meomi:5.0.0 -f components/infer_network/MEOMI/Dockerfile .
	@cd components/infer_network/JUMP3/ && matlab -nodisplay -nodesktop -r "run build.m" && cd adriansegura99/geneci_infer-network_jump3docker && sed -i '4,8d' Dockerfile && docker build -t adriansegura99/geneci_infer-network_jump3:5.0.0 . && cd ../../../../..
	@cd components/infer_network/NARROMI/ && matlab -nodisplay -nodesktop -r "run build.m" && cd adriansegura99/geneci_infer-network_narromidocker && sed -i '4,8d' Dockerfile && docker build -t adriansegura99/geneci_infer-network_narromi:5.0.0 . && cd ../../../../..
	@cd components/infer_network/CMI2NI/ && matlab -nodisplay -nodesktop -r "run build.m" && cd adriansegura99/geneci_infer-network_cmi2nidocker && sed -i '4,8d' Dockerfile && docker build -t adriansegura99/geneci_infer-network_cmi2ni:5.0.0 . && cd ../../../../..
	@cd components/infer_network/RSNET/ && matlab -nodisplay -nodesktop -r "run build.m" && cd adriansegura99/geneci_infer-network_rsnetdocker && sed -i '4,8d' Dockerfile && docker build -t adriansegura99/geneci_infer-network_rsnet:5.0.0 . && cd ../../../../..
	@cd components/infer_network/PCACMI/ && matlab -nodisplay -nodesktop -r "run build.m" && cd adriansegura99/geneci_infer-network_pcacmidocker && sed -i '4,8d' Dockerfile && docker build -t adriansegura99/geneci_infer-network_pcacmi:5.0.0 . && cd ../../../../..
	@bash components/infer_network/LOCPCACMI/build.sh
	@cd components/infer_network/PLSNET/ && matlab -nodisplay -nodesktop -r "run build.m" && cd adriansegura99/geneci_infer-network_plsnetdocker && sed -i '4,8d' Dockerfile && docker build -t adriansegura99/geneci_infer-network_plsnet:5.0.0 . && cd ../../../../..
	@docker build -t adriansegura99/geneci_infer-network_pidc:5.0.0 -f components/infer_network/PIDC/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_puc:5.0.0 -f components/infer_network/PUC/Dockerfile .
	@cd components/infer_network/GRNVBEM/ && matlab -nodisplay -nodesktop -r "run build.m" && cd adriansegura99/geneci_infer-network_grnvbemdocker && sed -i '4,8d' Dockerfile && docker build -t adriansegura99/geneci_infer-network_grnvbem:5.0.0 . && cd ../../../../..
	@docker build -t adriansegura99/geneci_infer-network_leap:5.0.0 -f components/infer_network/LEAP/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_nonlinearodes:5.0.0 -f components/infer_network/NONLINEARODES/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_inferelator:5.0.0 -f components/infer_network/INFERELATOR/Dockerfile .
	@docker build -t adriansegura99/geneci_optimize-ensemble:5.0.0 -f components/optimize_ensemble/Dockerfile .
	@docker build -t adriansegura99/geneci_apply-cut:5.0.0 -f components/apply_cut/Dockerfile .
	@docker build -t adriansegura99/geneci_evaluate_generic-prediction:5.0.0 -f components/evaluate/generic_prediction/Dockerfile .
	@docker build -t adriansegura99/geneci_evaluate_dream-prediction:5.0.0 -f components/evaluate/dream_prediction/Dockerfile .
	@docker build -t adriansegura99/geneci_draw-network:5.0.0 -f components/draw_network/Dockerfile .
	@docker build -t adriansegura99/geneci_weighted-confidence:5.0.0 -f components/weighted_confidence/Dockerfile .
	@docker build -t adriansegura99/geneci_cluster-network:5.0.0 -f components/cluster_network/Dockerfile .

push-images:
	@docker push adriansegura99/geneci_extract-data_dream3:5.0.0
	@docker push adriansegura99/geneci_extract-data_dream4-expgs:5.0.0
	@docker push adriansegura99/geneci_extract-data_dream4-eval:5.0.0
	@docker push adriansegura99/geneci_extract-data_dream5:5.0.0
	@docker push adriansegura99/geneci_extract-data_grndata:5.0.0
	@docker push adriansegura99/geneci_extract-data_irma:5.0.0
	@docker push adriansegura99/geneci_generate-data_sysgensim:5.0.0
	@docker push adriansegura99/geneci_infer-network_aracne:5.0.0
	@docker push adriansegura99/geneci_infer-network_bc3net:5.0.0
	@docker push adriansegura99/geneci_infer-network_c3net:5.0.0
	@docker push adriansegura99/geneci_infer-network_clr:5.0.0
	@docker push adriansegura99/geneci_infer-network_genie3:5.0.0
	@docker push adriansegura99/geneci_infer-network_mrnet:5.0.0
	@docker push adriansegura99/geneci_infer-network_mrnetb:5.0.0
	@docker push adriansegura99/geneci_infer-network_pcit:5.0.0
	@docker push adriansegura99/geneci_infer-network_tigress:5.0.0
	@docker push adriansegura99/geneci_infer-network_kboost:5.0.0
	@docker push adriansegura99/geneci_infer-network_meomi:5.0.0
	@docker push adriansegura99/geneci_infer-network_jump3:5.0.0
	@docker push adriansegura99/geneci_infer-network_narromi:5.0.0
	@docker push adriansegura99/geneci_infer-network_cmi2ni:5.0.0
	@docker push adriansegura99/geneci_infer-network_rsnet:5.0.0
	@docker push adriansegura99/geneci_infer-network_pcacmi:5.0.0
	@docker push adriansegura99/geneci_infer-network_locpcacmi:5.0.0
	@docker push adriansegura99/geneci_infer-network_plsnet:5.0.0
	@docker push adriansegura99/geneci_infer-network_pidc:5.0.0
	@docker push adriansegura99/geneci_infer-network_puc:5.0.0
	@docker push adriansegura99/geneci_infer-network_grnvbem:5.0.0
	@docker push adriansegura99/geneci_infer-network_leap:5.0.0
	@docker push adriansegura99/geneci_infer-network_nonlinearodes:5.0.0
	@docker push adriansegura99/geneci_infer-network_inferelator:5.0.0
	@docker push adriansegura99/geneci_optimize-ensemble:5.0.0
	@docker push adriansegura99/geneci_apply-cut:5.0.0
	@docker push adriansegura99/geneci_evaluate_generic-prediction:5.0.0
	@docker push adriansegura99/geneci_evaluate_dream-prediction:5.0.0
	@docker push adriansegura99/geneci_draw-network:5.0.0
	@docker push adriansegura99/geneci_weighted-confidence:5.0.0
	@docker push adriansegura99/geneci_cluster-network:5.0.0

pull-images:
	@docker pull adriansegura99/geneci_extract-data_dream3:5.0.0
	@docker pull adriansegura99/geneci_extract-data_dream4-expgs:5.0.0
	@docker pull adriansegura99/geneci_extract-data_dream4-eval:5.0.0
	@docker pull adriansegura99/geneci_extract-data_dream5:5.0.0
	@docker pull adriansegura99/geneci_extract-data_grndata:5.0.0
	@docker pull adriansegura99/geneci_extract-data_irma:5.0.0
	@docker pull adriansegura99/geneci_generate-data_sysgensim:5.0.0
	@docker pull adriansegura99/geneci_infer-network_aracne:5.0.0
	@docker pull adriansegura99/geneci_infer-network_bc3net:5.0.0
	@docker pull adriansegura99/geneci_infer-network_c3net:5.0.0
	@docker pull adriansegura99/geneci_infer-network_clr:5.0.0
	@docker pull adriansegura99/geneci_infer-network_genie3:5.0.0
	@docker pull adriansegura99/geneci_infer-network_mrnet:5.0.0
	@docker pull adriansegura99/geneci_infer-network_mrnetb:5.0.0
	@docker pull adriansegura99/geneci_infer-network_pcit:5.0.0
	@docker pull adriansegura99/geneci_infer-network_tigress:5.0.0
	@docker pull adriansegura99/geneci_infer-network_kboost:5.0.0
	@docker pull adriansegura99/geneci_infer-network_meomi:5.0.0
	@docker pull adriansegura99/geneci_infer-network_jump3:5.0.0
	@docker pull adriansegura99/geneci_infer-network_narromi:5.0.0
	@docker pull adriansegura99/geneci_infer-network_cmi2ni:5.0.0
	@docker pull adriansegura99/geneci_infer-network_rsnet:5.0.0
	@docker pull adriansegura99/geneci_infer-network_pcacmi:5.0.0
	@docker pull adriansegura99/geneci_infer-network_locpcacmi:5.0.0
	@docker pull adriansegura99/geneci_infer-network_plsnet:5.0.0
	@docker pull adriansegura99/geneci_infer-network_pidc:5.0.0
	@docker pull adriansegura99/geneci_infer-network_puc:5.0.0
	@docker pull adriansegura99/geneci_infer-network_grnvbem:5.0.0
	@docker pull adriansegura99/geneci_infer-network_leap:5.0.0
	@docker pull adriansegura99/geneci_infer-network_nonlinearodes:5.0.0
	@docker pull adriansegura99/geneci_infer-network_inferelator:5.0.0
	@docker pull adriansegura99/geneci_optimize-ensemble:5.0.0
	@docker pull adriansegura99/geneci_apply-cut:5.0.0
	@docker pull adriansegura99/geneci_evaluate_generic-prediction:5.0.0
	@docker pull adriansegura99/geneci_evaluate_dream-prediction:5.0.0
	@docker pull adriansegura99/geneci_draw-network:5.0.0
	@docker pull adriansegura99/geneci_weighted-confidence:5.0.0
	@docker pull adriansegura99/geneci_cluster-network:5.0.0

release:
	@echo Bump version to v$$(poetry version --short)
	@git tag v$$(poetry version --short)
	@git push origin v$$(poetry version --short)
