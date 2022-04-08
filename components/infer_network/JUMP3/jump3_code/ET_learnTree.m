function [promState,varimp,Lmax,tree] = ET_learnTree(allX,Y,L_init,obsTimes,params,lambda_terms,K)

% Grow jump tree

nTS = params.nTS;
nStep = params.nStep;
nsamples = params.nsamples;
nvar = size(allX{1},1);

sample_idx = cell(1,nTS);
promState = cell(1,nTS);
dm_A = zeros(nTS,nStep+1);

for k=1:nTS
    sample_idx{k} = 1:nsamples(k);
    promState{k} = zeros(1,nsamples(k));
end

promState_interp = zeros(nTS,nStep+1);
varimp = zeros(1,nvar);
Lmax = L_init;
flag = 1;

%% Root node

[promState_tmp,promState_interp_tmp,dm_A_tmp,L,sample_idx0,sample_idx1,selected_var_idx,regSign,thres] = ET_selectTest(allX,Y,promState,promState_interp,dm_A,sample_idx,obsTimes,params,lambda_terms,K);
% if we can not increase the likelihood --> tree = leaf with value 0
if L <= Lmax || selected_var_idx == -1    
    flag = 0;
    tree = 0;
else
    
    promState = promState_tmp;
    promState_interp = promState_interp_tmp;
    dm_A = dm_A_tmp;
    
    tree.regSign = regSign;
    
    score = L - Lmax;
    varimp(selected_var_idx) = varimp(selected_var_idx) + score;
    
    Lmax = L;
    
    tree.gene_idx = params.tfidx(selected_var_idx);
    tree.thres = thres;
    tree.node_left = 0;
    tree.node_right = 1;
    
    candidateSplits.sample_idx = {};
    candidateSplits.paths = {};
    nCandidateSplits = 0;
    
    if count_samples(sample_idx0) > 1
        nCandidateSplits = nCandidateSplits + 1;
        candidateSplits.sample_idx{nCandidateSplits} = sample_idx0;
        candidateSplits.paths{nCandidateSplits} = {'node_left'};
    end
    if count_samples(sample_idx1) > 1
        nCandidateSplits = nCandidateSplits + 1;
        candidateSplits.sample_idx{nCandidateSplits} = sample_idx1;
        candidateSplits.paths{nCandidateSplits} = {'node_right'};
    end
    
end

%% Grow rest of tree

while flag
    
    Lmax_tmp = Lmax;
    best_split_idx = 0;
    
    for i=1:nCandidateSplits
        
        sample_idx = candidateSplits.sample_idx{i};
        [split.promState,split.promState_interp,split.dm_A,split.L,split.sample_idx0,split.sample_idx1,split.selected_var_idx,split.regSign,split.thres] = ET_selectTest(allX,Y,promState,promState_interp,dm_A,sample_idx,obsTimes,params,lambda_terms,K);

        if split.L > Lmax_tmp && split.selected_var_idx ~= -1    
            best_split_idx = i;
            best_split = split;
            Lmax_tmp = split.L;
        end
        
    end
    
    
    if best_split_idx == 0
        % if we can not increase the likelihood --> terminate
        flag = 0;
        
    else
        
        promState = best_split.promState;
        promState_interp = best_split.promState_interp;
        dm_A = best_split.dm_A;
        
        tree.regSign = best_split.regSign;
        
        score = Lmax_tmp - Lmax;
        varimp(best_split.selected_var_idx) = varimp(best_split.selected_var_idx) + score;
        
        Lmax = Lmax_tmp;
        
        path_best = candidateSplits.paths{best_split_idx};
        new_split.gene_idx = params.tfidx(best_split.selected_var_idx);
        new_split.thres = best_split.thres;
        new_split.node_left = 0;
        new_split.node_right = 1;
        tree = setfield(tree,path_best{:},new_split); %add split to tree
        
        candidateSplits.sample_idx(best_split_idx) = [];
        candidateSplits.paths(best_split_idx) = [];
        nCandidateSplits = nCandidateSplits - 1;
        
        if count_samples(best_split.sample_idx0) > 1
            nCandidateSplits = nCandidateSplits + 1;
            candidateSplits.sample_idx{nCandidateSplits} = best_split.sample_idx0;
            new_path0 = [path_best 'node_left'];
            candidateSplits.paths{nCandidateSplits} = new_path0;
        end
        if count_samples(best_split.sample_idx1) > 1
            nCandidateSplits = nCandidateSplits + 1;
            candidateSplits.sample_idx{nCandidateSplits} = best_split.sample_idx1;
            new_path1 = [path_best 'node_right'];
            candidateSplits.paths{nCandidateSplits} = new_path1;
        end
        
    end

end
