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
	@cd components/generate_data/SysGenSIM && matlab -nodisplay -nodesktop -r "run build.m" && cd adriansegura99/geneci_generate-data_sysgensimdocker && sed -i '4,8d' Dockerfile && docker build -t adriansegura99/geneci_generate-data_sysgensim . && cd ../../../../..
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
	@docker build -t adriansegura99/geneci_infer-network_meomi -f components/infer_network/MEOMI/Dockerfile .
	@cd components/infer_network/JUMP3/ && matlab -nodisplay -nodesktop -r "run build.m" && cd adriansegura99/geneci_infer-network_jump3docker && sed -i '4,8d' Dockerfile && docker build -t adriansegura99/geneci_infer-network_jump3 . && cd ../../../../..
	@cd components/infer_network/NARROMI/ && matlab -nodisplay -nodesktop -r "run build.m" && cd adriansegura99/geneci_infer-network_narromidocker && sed -i '4,8d' Dockerfile && docker build -t adriansegura99/geneci_infer-network_narromi . && cd ../../../../..
	@cd components/infer_network/CMI2NI/ && matlab -nodisplay -nodesktop -r "run build.m" && cd adriansegura99/geneci_infer-network_cmi2nidocker && sed -i '4,8d' Dockerfile && docker build -t adriansegura99/geneci_infer-network_cmi2ni . && cd ../../../../..
	@cd components/infer_network/RSNET/ && matlab -nodisplay -nodesktop -r "run build.m" && cd adriansegura99/geneci_infer-network_rsnetdocker && sed -i '4,8d' Dockerfile && docker build -t adriansegura99/geneci_infer-network_rsnet . && cd ../../../../..
	@cd components/infer_network/PCACMI/ && matlab -nodisplay -nodesktop -r "run build.m" && cd adriansegura99/geneci_infer-network_pcacmidocker && sed -i '4,8d' Dockerfile && docker build -t adriansegura99/geneci_infer-network_pcacmi . && cd ../../../../..
	@bash components/infer_network/LOCPCACMI/build.sh
	@cd components/infer_network/PLSNET/ && matlab -nodisplay -nodesktop -r "run build.m" && cd adriansegura99/geneci_infer-network_plsnetdocker && sed -i '4,8d' Dockerfile && docker build -t adriansegura99/geneci_infer-network_plsnet . && cd ../../../../..
	@docker build -t adriansegura99/geneci_infer-network_pidc -f components/infer_network/PIDC/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_puc -f components/infer_network/PUC/Dockerfile .
	@cd components/infer_network/GRNVBEM/ && matlab -nodisplay -nodesktop -r "run build.m" && cd adriansegura99/geneci_infer-network_grnvbemdocker && sed -i '4,8d' Dockerfile && docker build -t adriansegura99/geneci_infer-network_grnvbem . && cd ../../../../..
	@docker build -t adriansegura99/geneci_infer-network_leap -f components/infer_network/LEAP/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_nonlinearodes -f components/infer_network/NONLINEARODES/Dockerfile .
	@docker build -t adriansegura99/geneci_infer-network_inferelator -f components/infer_network/INFERELATOR/Dockerfile .
	@docker build -t adriansegura99/geneci_optimize-ensemble -f components/optimize_ensemble/Dockerfile .
	@docker build -t adriansegura99/geneci_apply-cut -f components/apply_cut/Dockerfile .
	@docker build -t adriansegura99/geneci_evaluate_generic-prediction -f components/evaluate/generic_prediction/Dockerfile .
	@docker build -t adriansegura99/geneci_evaluate_dream-prediction -f components/evaluate/dream_prediction/Dockerfile .
	@docker build -t adriansegura99/geneci_draw-network -f components/draw_network/Dockerfile .
	@docker build -t adriansegura99/geneci_weighted-confidence -f components/weighted_confidence/Dockerfile .

push-images:
	@docker push adriansegura99/geneci_extract-data_dream3 
	@docker push adriansegura99/geneci_extract-data_dream4-expgs 
	@docker push adriansegura99/geneci_extract-data_dream4-eval 
	@docker push adriansegura99/geneci_extract-data_dream5 
	@docker push adriansegura99/geneci_extract-data_grndata 
	@docker push adriansegura99/geneci_extract-data_irma 
	@docker push adriansegura99/geneci_generate-data_sysgensim 
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
	@docker push adriansegura99/geneci_infer-network_meomi
	@docker push adriansegura99/geneci_infer-network_jump3
	@docker push adriansegura99/geneci_infer-network_narromi
	@docker push adriansegura99/geneci_infer-network_cmi2ni
	@docker push adriansegura99/geneci_infer-network_rsnet
	@docker push adriansegura99/geneci_infer-network_pcacmi
	@docker push adriansegura99/geneci_infer-network_locpcacmi
	@docker push adriansegura99/geneci_infer-network_plsnet
	@docker push adriansegura99/geneci_infer-network_pidc
	@docker push adriansegura99/geneci_infer-network_puc
	@docker push adriansegura99/geneci_infer-network_grnvbem
	@docker push adriansegura99/geneci_infer-network_leap
	@docker push adriansegura99/geneci_infer-network_nonlinearodes
	@docker push adriansegura99/geneci_infer-network_inferelator
	@docker push adriansegura99/geneci_optimize-ensemble 
	@docker push adriansegura99/geneci_apply-cut 
	@docker push adriansegura99/geneci_evaluate_generic-prediction 
	@docker push adriansegura99/geneci_evaluate_dream-prediction 
	@docker push adriansegura99/geneci_draw-network
	@docker push adriansegura99/geneci_weighted-confidence

pull-images:
	@docker pull adriansegura99/geneci_extract-data_dream3 
	@docker pull adriansegura99/geneci_extract-data_dream4-expgs 
	@docker pull adriansegura99/geneci_extract-data_dream4-eval 
	@docker pull adriansegura99/geneci_extract-data_dream5 
	@docker pull adriansegura99/geneci_extract-data_grndata 
	@docker pull adriansegura99/geneci_extract-data_irma 
	@docker pull adriansegura99/geneci_generate-data_sysgensim
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
	@docker pull adriansegura99/geneci_infer-network_meomi
	@docker pull adriansegura99/geneci_infer-network_jump3
	@docker pull adriansegura99/geneci_infer-network_narromi
	@docker pull adriansegura99/geneci_infer-network_cmi2ni
	@docker pull adriansegura99/geneci_infer-network_rsnet
	@docker pull adriansegura99/geneci_infer-network_pcacmi
	@docker pull adriansegura99/geneci_infer-network_locpcacmi
	@docker pull adriansegura99/geneci_infer-network_plsnet
	@docker pull adriansegura99/geneci_infer-network_pidc
	@docker pull adriansegura99/geneci_infer-network_puc
	@docker pull adriansegura99/geneci_infer-network_grnvbem
	@docker pull adriansegura99/geneci_infer-network_leap
	@docker pull adriansegura99/geneci_infer-network_nonlinearodes
	@docker pull adriansegura99/geneci_infer-network_inferelator
	@docker pull adriansegura99/geneci_optimize-ensemble 
	@docker pull adriansegura99/geneci_apply-cut 
	@docker pull adriansegura99/geneci_evaluate_generic-prediction 
	@docker pull adriansegura99/geneci_evaluate_dream-prediction 
	@docker pull adriansegura99/geneci_draw-network
	@docker pull adriansegura99/geneci_weighted-confidence

release:
	@echo Bump version to v$$(poetry version --short)
	@git tag v$$(poetry version --short)
	@git push origin v$$(poetry version --short)