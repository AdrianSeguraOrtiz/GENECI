function VIM = plsnet(expr_matrix,input_idx,nfac,K,T)

% expr_matrix is a matrix containing expression values. Each line 
%corresponds to an experiment and each column corresponds to a gene. 

% p is the number of genes

%VIM is a matrix of size p x p. VIM(i,j) is the weight of edge directed 
%from the ith gene of expr_matrix to the jth gene. VIM(i,i) is set to zero
%for all i.

%input_idx is a vector of length <= p. VIM(i,:) such that i is not in 
%input_idx is set to zero. The default vector contains the indexes of all 
%genes in expr_matrix.

% nfac is the number of components. The default value is 5.

% K is the number of candidate regulatory genes. 

% T is the number of iterations. The default value is 1000.


%%
tic;

nb_genes = size(expr_matrix,2);
nb_sample = size(expr_matrix,1);
nb_k = size (input_idx,2);
VIM = zeros(nb_genes,nb_genes);

%% resampling

for j = 1:T
    vv = zeros(nb_genes,nb_genes);
    bb = randperm(nb_k);
    ipdx = bb(1:K);
    cc = randsample(nb_sample,nb_sample,1);
%     dd = randperm(100);
%     cc = dd(1:80);
    expr_matrix1 = expr_matrix(cc,:);

    for i=1:nb_genes
        
       vv(i,:) = plsnet_single(expr_matrix1,i,ipdx,nfac);   %feature selection 
          
    end
    VIM = VIM + vv;
%     toc;
end
VIM = VIM';
%% refined the network
theta = var(VIM,0,2);
theta = theta(:,ones(nb_genes,1));
VIM = VIM.*theta;

toc;











