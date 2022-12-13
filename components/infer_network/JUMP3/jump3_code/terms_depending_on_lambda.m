function lambda_terms = terms_depending_on_lambda(data,obsTimes,params,m_init)
%function lambda_terms =
%terms_depending_on_lambda(data,obsTimes,params,m_init)
% Computes some terms that depend on parameter lambda only (and not on A
% and b)

%% Misc

nTS = params.nTS;
nStep = params.nStep;
nsamples = params.nsamples;

obsTimes_all = zeros(1,nStep);
for k=1:nTS
    obsTimes_all(obsTimes{k}(2:end)) = 1;
end
obsTimes_all = [0 find(obsTimes_all)];
params.obsTimes_all = obsTimes_all;

%% Covariance matrix
KObs = GP_covariance(params,obsTimes);

%% Invert covariance matrix and computes first part of likelihood
invKObs = cell(1,nTS);
L_init = 0;
for k=1:nTS
    K = KObs{k} + diag(params.obsNoise{k});
    
    % Cholesky decomposition
    Cl = chol(K,'lower');
    Cu = Cl';
    invCu = inv(Cu);
    invKObs{k} = invCu*invCu';

    % First part of Log-likelihood
    L_init = L_init - 0.5*nsamples(k)*log(2*pi) - sum(log(diag(Cl)));
end

%% Derivative of the mean of the Gaussian process w.r.t. parameter b, at
%% the obervation time points
dm_bObs = mean_derivative_b(params.lambda,nStep,nTS,obsTimes);

%% Terms for the quadratic optimization: H_b,b, G_b, optDataTerm
bvar = 0;
gradb = 0;

expmt_tmp = zeros(1,nStep);
expmt_tmp(obsTimes_all(2:end)) = exp(-params.lambda*obsTimes_all(2:end)');

optDataTerm = cell(1,nTS);
for k=1:nTS
    expmt = [1 expmt_tmp(obsTimes{k}(2:end))];
    optDataTerm{k} = m_init(k)*expmt' - data{k}';
    
    prodb = dm_bObs{k}*invKObs{k};
    bvar = bvar + prodb*dm_bObs{k}';    
    gradb = gradb + prodb*optDataTerm{k};
end



%% Put everything in lambda_terms
lambda_terms.KObs = KObs;
lambda_terms.invKObs = invKObs;
lambda_terms.L_init = L_init;
lambda_terms.dm_bObs = dm_bObs;
lambda_terms.bvar = bvar;
lambda_terms.gradb = gradb;
lambda_terms.optDataTerm = optDataTerm;



