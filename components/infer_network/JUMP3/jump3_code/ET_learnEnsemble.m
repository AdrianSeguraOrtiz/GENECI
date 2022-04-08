function [exprMean,exprVar,promState,varimp,kinParams,kinParamsVar,trees] = ET_learnEnsemble(allX,Y,obsTimes,params,K,ntrees)


nTS = params.nTS;
nStep = params.nStep;
nsamples = params.nsamples;
m_init = zeros(1,nTS);
for k=1:nTS
    m_init(k) = Y{k}(1);
end

params.m_init = m_init;

%% Lambda estimation
params.lambda = estimate_lambda(Y,obsTimes);

%% Several terms depending on parameter lambda only
lambda_terms = terms_depending_on_lambda(Y,obsTimes,params,m_init);

%%  Initial value of log-likelihood: \mu = 0 --> dm_A = 0
dm_AObs_init = cell(1,nTS);
for k=1:nTS
    dm_AObs_init{k} = zeros(1,nsamples(k));
end
L_init = maximize_likelihood_Ab(Y,lambda_terms,dm_AObs_init,params,obsTimes,m_init);


%% Growing Jump Trees
promState_obs = cell(1,nTS);
for k=1:nTS
    promState_obs{k} = zeros(1,nsamples(k));
end
varimp = zeros(1,length(params.tfidx));
trees = cell(1,ntrees);

for t=1:ntrees
    
    [promState_tree,varimp_tree,Lmax,trees{t}] = ET_learnTree(allX,Y,L_init,obsTimes,params,lambda_terms,K);

    % Normalize importances
    if Lmax > L_init
        varimp_tree = varimp_tree/(Lmax-L_init);
    end   
    
    % Average over trees
    if isstruct(trees{t})
        regSign_tree = trees{t}.regSign;
        for k=1:nTS
            promState_tree_k = promState_tree{k};
            promState_tree_k(promState_tree_k==0) = -1;
            promState_tree_k = promState_tree_k*regSign_tree;
            promState_tree_k(promState_tree_k==-1) = 0;
            promState_obs{k} = promState_obs{k} + promState_tree_k/ntrees;
        end
        varimp = varimp + varimp_tree/ntrees;
    end

end


%% Final mean and variance
promState = zeros(nTS,nStep+1);
for k=1:nTS
    tEnd = obsTimes{k}(end);
    interv = 0:tEnd;
    promState_interp = zeros(nStep+1,1);
    promState_interp(1:tEnd+1) = interp1q(obsTimes{k}',promState_obs{k}',interv');
    promState_interp(tEnd+2:end) = promState_obs{k}(end);
    promState(k,:) = promState_interp';
end
[exprMean,exprVar,kinParams,kinParamsVar] = GP_mean_variance(promState,lambda_terms,params,obsTimes,m_init);

