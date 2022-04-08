function [paramsOpt,paramsOptVar] = optimize_params_Ab(dm_A,lambda_terms,params)


%% Misc
nTS = params.nTS;
invKObs = lambda_terms.invKObs;
dm_bObs = lambda_terms.dm_bObs;
optDataTerm = lambda_terms.optDataTerm;
bvar = lambda_terms.bvar;
gradb = lambda_terms.gradb;

%% Hessian matrix and gradient vector
Avar = 0;
AbTerm = 0;
gradA = 0;

for k=1:nTS
    prodA = dm_A{k}*invKObs{k};
    Avar = Avar + prodA*dm_A{k}';
    AbTerm = AbTerm + prodA*dm_bObs{k}';
    gradA = gradA + prodA*optDataTerm{k};
end

H   = [Avar AbTerm ; AbTerm bvar];
H = H + diag([1e-6 1e-6]); % To avoid singular matrix
cov = inv(H);
paramsOptVar = diag(cov);

G = [gradA;gradb];

%% Results

res = -cov*G;

paramsOpt.A = res(1);
paramsOpt.b = res(2);

paramsOpt.lambda = params.lambda;
paramsOpt.sysNoise = params.sysNoise;
paramsOpt.obsNoise = params.obsNoise;