function [promState,promState_interp,dm_A,L,sample_idx0,sample_idx1,selected_var_idx,regSign,thres] = ET_selectTest(allX,Y,promState_parent,promState_parent_interp,dm_A_parent,sample_idx,obsTimes,params,lambda_terms,K)
%
% Select the input variable yielding the best split (Extra-Trees).
%

nvar = size(allX{1},1);
nTS = params.nTS;

candidate_idx = 1:nvar;

if K < length(candidate_idx)
    idx_rand = randsample(length(candidate_idx),K);
    candidate_idx = candidate_idx(idx_rand);
end

L = -inf;
selected_var_idx = -1;
regSign = 0;
thres = -inf;
promState = promState_parent;
promState_interp = promState_parent_interp;
dm_A = dm_A_parent;
sample_idx0 = cell(1,nTS);
sample_idx1 = cell(1,nTS);


for j=candidate_idx
    
    allX_cand = cell(1,nTS);
    for k=1:nTS
        allX_cand{k} = allX{k}(j,:);
    end

    [promState_tmp,promState_interp_tmp,dm_A_tmp,L_tmp,sample_idx0_tmp,sample_idx1_tmp,regSign_tmp,thres_tmp] = ET_randomSplit(allX_cand,Y,promState_parent,promState_parent_interp,dm_A_parent,sample_idx,obsTimes,params,lambda_terms);

    if L_tmp > L
        L = L_tmp;
        promState = promState_tmp;
        promState_interp = promState_interp_tmp;
        dm_A = dm_A_tmp;
        selected_var_idx = j;
        regSign = regSign_tmp;
        thres = thres_tmp;
        sample_idx0 = sample_idx0_tmp;
        sample_idx1 = sample_idx1_tmp;
    end
end