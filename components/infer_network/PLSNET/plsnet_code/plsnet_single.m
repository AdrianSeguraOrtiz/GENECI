function vi = plsnet_single(expr_matrix,output_idx,input_idx,nfac)

%plsnet_single learns a model fromexpr_matrix and assigns a weight 
%to each edge directed from a putativeregulator to the target gene. 

% expr_matrix is a matrix containing expression values. Each line
%   corresponds to an experiment and each column corresponds to a gene. 

% output_idx is the (column) index of the target gene in expr_matrix.

% vi is a vector of length p, where p is the number of columns in 

%expr_matrix. vi(i) is the weight of edge directed from the ith gene of
%expr_matrix to the target gene. vi(output_idx) is set to zero.


%input_idx is a vector of length <= p. vi(i) such that i is not in 
%input_idx is set to zero. 

% nfac is the number of components. The default value is 5.


%% 

% nb_samples = size(expr_matrix,1); % number of experiments
nb_genes = size(expr_matrix,2); % number of genes

%% Output vector

output = expr_matrix(:,output_idx);

ytrn = zscore(output);


%% Indexes of input genes

input_idx = unique(input_idx);
input_idx = setdiff(input_idx,output_idx);
% nb_inputs = length(input_idx);


%%
trn = zscore(expr_matrix(:,input_idx));
varimp = plsrank(trn,ytrn,nfac);  % PLS-based featrue selection
vi = zeros(1,nb_genes);
vi(input_idx) = varimp;
















