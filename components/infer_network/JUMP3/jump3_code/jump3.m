function [w,exprMean,exprVar,promState,kinParams,kinParamsVar,trees] = jump3(data,obsTimes,noiseVar,tfidx,K,ntrees)
%
% Network inference using the jump3 method, described in:
% Huynh-Thu V. A. and Sanguinetti G. (2015) Combining tree-based and
% dynamical systems for the inference of gene regulatory networks.
% Bioinformatics, 31(10):1614-1622.
%
%
%[w,exprMean,exprVar,promState,kinParams,kinParamsVar,trees] =
%jump3(data,obsTimes,noiseVar) runs the algorithm. 
%The mandatory input arguments are:
%
%- data: 1-by-S cell array, where S is the number of perturbation time
%series. data{k} is a p-by-N_k matrix containing observed gene expression
%levels. p is the number of genes in the network and N_k is the number of
%observations in the k-th time series. The ordering of the p genes must be
%the same in all the data matrices. 
%- obsTimes: 1-by-S cell array. obsTimes{k} is a vector of length N_k
%containing observation time points. The time points must be integers, and
%the first time point in each time series must be 0.
%- noiseVar: structure array with two fields:
%   noiseVar.sysNoise is the variance of the intrinsic noise.
%   noiseVar.obsNoise is a 1-by-S cell array. noiseVar.obsNoise{k} is a
%   p-by-N_k matrix containing the observation noise variances
%   (corresponding to the observations in data{k}).
%
%[w,exprMean,exprVar,promState,kinParams,kinParamsVar,trees] =
%jump3(data,obsTimes,noiseVar,tfidx) only uses as candidate regulators the
%genes whose index (as ordered in the data matrices) is in tfidx. tfidx is
%a vector of length <= p. The default vector contains the indices of all
%the genes.
%
%[w,exprMean,exprVar,promState,kinParams,kinParamsVar,trees] =
%jump3(data,obsTimes,noiseVar,tfidx,K) specifies the number K of randomly
%selected candidate regulators at each node of one tree. K must be an
%integer between 1 and n, where n is the number of candidate regulators
%(i.e. length of vector tfidx). By default, K = n.
%
%[w,exprMean,exprVar,promState,kinParams,kinParamsVar,trees] =
%jump3(data,obsTimes,noiseVar,tfidx,K,ntrees) specifies the number of trees
%grown in an ensemble. Default value: 100.
%
%
%Outputs:
%
%- w: weights of regulatory links. w(i,j) is the weight of the link
%directed from gene j to gene i.
%- exprMean: means of gene expressions over time interval [0,N], where N is
%the highest time point.
%- exprVar: variances of gene expressions over [0,N].
%- promState: promoter states over [0,N].
%- kinParams: estimated values of kinetic parameters A, b and lambda for
%each gene.
%- kinParamsVar: variances of kinetic parameters A and b for each gene.
%- trees: ensembles of decision trees predicting the promoter state of each
%gene respectively.


tic

%% Check input arguments
narginchk(3,6);

if ~iscell(data)
    error('Input argument data must be a cell array. Type ''help jump3'' for more information.')
end

nTS = length(data);
ngenes = size(data{1},1);
data_flag = 0;
for k=2:nTS
    if size(data{k},1) ~= ngenes
        data_flag = 1;
    end
end
if data_flag
    error('The number of genes/rows in each data matrix must be the same. Type ''help jump3'' for more information.')
end

if ~iscell(obsTimes)
    error('Input argument obsTimes must be a cell array. Type ''help jump3'' for more information.')
end

if length(obsTimes) ~= nTS
    error('Input arguments data and obsTimes must both be a 1-by-S cell array, where S is the number of time series.')
end

obsTimes_flag = 0;
for k=1:nTS
    if obsTimes{k}(1) ~= 0
        obsTimes_flag = 1;
    end
end
if obsTimes_flag
    error('In input argument obsTimes, the first time point of each time series must be 0.')
end

obsTimes_flag = 0;
for k=1:nTS
    if length(obsTimes{k}) ~= size(data{k},2)
        obsTimes_flag = 1;
    end
end
if obsTimes_flag
    error('The number of time series in obsTimes must be the same as in data.')
end

if ~isstruct(noiseVar) || ~isfield(noiseVar,'sysNoise') || ~isfield(noiseVar,'obsNoise')
    error('Input argument noiseVar must be a structure array with two fields: ''sysNoise'' and ''obsNoise''')
end

if ~iscell(noiseVar.obsNoise) || length(noiseVar.obsNoise) ~= nTS
    error('Input argument noiseVar.obsNoise must be a 1-by-S cell array, where S is the number of time series.')
end

noise_flag = 0;
for k=1:nTS
    if (size(data{k},1) ~= size(noiseVar.obsNoise{k},1)) || (size(data{k},2) ~= size(noiseVar.obsNoise{k},2))
        noise_flag = 1;
    end
end
if noise_flag
    error('Matrix noiseVar.obsNoise{k} must be of the same size as matrix data{k}.')
end

if nargin > 3 && sum(ismember(tfidx,1:ngenes)) ~= length(tfidx)
    error('Input argument tfidx must be a vector containing integers between 1 and p, where p is the total number of genes.')
end

if nargin > 4 && (~isnumeric(K) || K < 1 || K > length(tfidx))
    error('Input argument K must be an integer between 1 and n, where n is the number of candidate regulators.')
end

if nargin > 5 && (~isnumeric(ntrees) || ntrees < 0)
    error('Input argument ntrees must be a positive integer.')
end


%% Default input parameters
if nargin < 4
    tfidx = 1:ngenes;
end

if nargin < 5
    K = length(tfidx);
end

if nargin < 6
    ntrees = 100;
end

    
%% Initialisation

nsamples = zeros(1,nTS);
nStep = 0;
for k=1:nTS
    nStep = max(nStep,obsTimes{k}(end));
    nsamples(k) = length(obsTimes{k});
end

exprMean = cell(1,nTS);
exprVar = zeros(ngenes,nStep+1);
promState = cell(1,nTS);
w = zeros(ngenes,ngenes);

for k=1:nTS
    exprMean{k} = zeros(ngenes,nStep+1);
    promState{k} = zeros(ngenes,nStep+1);
end

kinParams = cell(1,ngenes);
kinParamsVar = cell(1,ngenes);
trees = cell(1,ngenes);

%% Run hybrid approach for each gene

for i=1:ngenes
    fprintf('Gene %d...\n',i)
    
    tfidx_target = setdiff(tfidx,i);
    
    allX = cell(1,nTS);
    Y = cell(1,nTS);
    params_target.nStep = nStep;
    params_target.nTS = nTS;
    params_target.sysNoise = noiseVar.sysNoise;
    params_target.obsNoise = cell(1,nTS);
    params_target.tfidx = tfidx_target;
    params_target.nsamples = nsamples;
    
    for k=1:nTS
        allX{k} = data{k}(tfidx_target,:);
        Y{k} = data{k}(i,:);
        params_target.obsNoise{k} = noiseVar.obsNoise{k}(i,:);
    end
    
    [exprMean_target,exprVar(i,:),promState_target,varimp,kinParams{i},kinParamsVar_tmp,trees{i}] = ET_learnEnsemble(allX,Y,obsTimes,params_target,K,ntrees);
    
    w(i,tfidx_target) = varimp;
    
    for k=1:nTS
        exprMean{k}(i,:) = exprMean_target(k,:);
        promState{k}(i,:) = promState_target(k,:);
    end
    
    kinParamsVar{i}.A = kinParamsVar_tmp(1);
    kinParamsVar{i}.b = kinParamsVar_tmp(2);
end


toc