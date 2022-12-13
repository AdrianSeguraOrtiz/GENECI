function [promState,promState_interp,dm_A,L,sample_idx0,sample_idx1,regSign,thres] = ET_randomSplit(X,Y,promState_parent,promState_parent_interp,dm_A_parent,sample_idx,obsTimes,params,lambda_terms)
%
% Randomly select a split for an input variable.
%

nTS = params.nTS;
nStep = params.nStep;
m_init = params.m_init;
allX = [];
for k=1:nTS
    allX = [allX X{k}(sample_idx{k})];
end


L = -inf;
promState = promState_parent;
promState_interp = promState_parent_interp;
dm_A = dm_A_parent;
sample_idx0 = cell(1,nTS);
sample_idx1 = cell(1,nTS);
regSign = 0;

new_promState = promState_parent;
new_promState_interp = zeros(nTS,nStep+1);
new_sample_idx0 = cell(1,nTS);
new_sample_idx1 = cell(1,nTS);

% Randomly choose a split
thres = random('unif',min(allX)+1e-6,max(allX),1,1);

% If x < thres --> state = 0, otherwise state = 1

for k=1:nTS    
    sample_idx_k = sample_idx{k};
    X_k = X{k};
    
    bin1 = X_k(sample_idx_k)>=thres;
    
    new_promState{k}(sample_idx_k) = bin1;
    new_promState_interp(k,:) = extendStates(new_promState{k},obsTimes{k},nStep);
    
    new_sample_idx1{k} = sample_idx_k(bin1);
    sample_idx_k(bin1) = [];
    new_sample_idx0{k} = sample_idx_k;
end


[new_dm_A,new_dm_AObs] = mean_derivative_A_update(new_promState_interp,promState_parent_interp,dm_A_parent,params.lambda,obsTimes);
[L_tmp,regSign_tmp] = maximize_likelihood_Ab(Y,lambda_terms,new_dm_AObs,params,obsTimes,m_init);


if L_tmp > L
    L = L_tmp;
    promState = new_promState;
    promState_interp = new_promState_interp;
    dm_A = new_dm_A;
    sample_idx0 = new_sample_idx0;
    sample_idx1 = new_sample_idx1;
    regSign = regSign_tmp;
end

   
