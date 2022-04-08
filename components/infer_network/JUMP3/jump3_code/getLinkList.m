function getLinkList(w,tfidx,gene_names,maxcount,filename)
%Get the ranked list of (directed) regulatory links
%
%getLinkList(w) writes the ranked list of all putative regulatory links. 
%w is a weighted adjacency matrix. w(j,i) is the weight of edge directed
%from the i-th gene to the j-th gene. Self interactions do not appear in
%the list. Regulatory links with a score equal to 0 are randomly permuted.
%In the ranked list of edges, each line has the following format:
%regulatory gene    target gene    weight of edge
%
%getLinkList(w,tfidx) only writes the links where the index of the
%regulatory gene (as ordered in w) is in tfidx. tfidx is a vector of length
%<= p, where p is the size of w, i.e. the number of genes. The default
%vector contains the indexes of all genes in w.
%
%getLinkList(w,tfidx,gene_names) writes the ranked list with the names of
%the genes that are in gene_names. gene_names is a cell array of strings of
%length p. If gene_names is not provided or is an empty cell, genes are 
%named G1, G2, G3, etc.
%
%getLinkList(w,tfidx,gene_names,maxcount) writes only the first maxcount
%regulatory links of the ranked list. If maxcount is equal to 0, all the
%regulatory links are written.
%
%getLinkList(w,tfidx,gene_names,maxcount,filename) writes the ranked list
%of regulatory links to file filename.

%% Check input arguments
narginchk(1,5);

if size(w,1) ~= size(w,2)
    error('w must be a square matrix.');
end

if nargin > 1 && sum(ismember(tfidx,1:size(w,1))) ~= length(tfidx)
    error('Input argument tfidx must be a vector containing integers between 1 and p, where p is the number of genes in w.')
end

if nargin > 2 && sum(size(gene_names)) ~= (size(w,1)+1) && ~isempty(gene_names)
    error('Input argument gene_names must be a cell of length p, where p is the size of w, or an empty cell.')
end

if nargin > 3 && maxcount < 0
    error('Input argument maxcount must be zero or a positive integer.');
end

if nargin > 4 && ~isa(filename,'char')
    error('Input argument filename must be a string.')
end
    
%% Get the non-ranked list of regulatory links
nb_genes = size(w,1);

% Indexes of input genes
if nargin >= 2
    tfidx = unique(tfidx);
else
    % Default: all genes are putative regulators
    tfidx = 1:nb_genes;
end
    
nb_tfs = length(tfidx);
nb_interactions = nb_tfs * nb_genes - nb_tfs;
interactions = zeros(nb_interactions,3);

k=0;
for i=1:nb_tfs
    for j=1:nb_genes
        if tfidx(i)~=j
            k = k + 1;
            interactions(k,:) = [tfidx(i) j w(j,tfidx(i))];
        end
    end
end

%% Rank the list according to the weights of the edges

[tmp,order] = sort(interactions(:,3),'descend');
scores_sort = interactions(order,:);

%% Random permutation of edges with score equal to 0
idx_zero = find(scores_sort(:,3)==0);
order_zero = randperm(length(idx_zero));
idx_zero_perm = idx_zero(order_zero);
scores_sort(idx_zero,:) = scores_sort(idx_zero_perm,:);

%% Write the ranked list of edges
if nargin > 3 && maxcount > 0 && maxcount < nb_interactions
    nb_interactions = maxcount;
end

if nargin == 5
    fid = fopen(filename,'w');
end

for n=1:nb_interactions
    if nargin == 5
        if nargin > 2 && ~isempty(gene_names)
            fprintf(fid,'%s\t%s\t%f\r\n',gene_names{scores_sort(n,1)},gene_names{scores_sort(n,2)},scores_sort(n,3));
        else
            fprintf(fid,'G%d\tG%d\t%f\r\n',scores_sort(n,1),scores_sort(n,2),scores_sort(n,3));
        end
    else
        if nargin > 2 && ~isempty(gene_names)
            fprintf('%s\t%s\t%f\n',gene_names{scores_sort(n,1)},gene_names{scores_sort(n,2)},scores_sort(n,3));
        else
            fprintf('G%d\tG%d\t%f\n',scores_sort(n,1),scores_sort(n,2),scores_sort(n,3));
        end
        
    end
end

if nargin == 5
    fclose(fid);
end