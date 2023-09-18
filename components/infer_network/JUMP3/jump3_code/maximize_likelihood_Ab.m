function [L,regSign] = maximize_likelihood_Ab(data,lambda_terms,dm_AObs,params,obsTimes,m_init)

% Parameter optimization
paramsOpt = optimize_params_Ab(dm_AObs,lambda_terms,params);

% Sign of regulation (i.e. sign of A)
if paramsOpt.A >= 0
    regSign = 1;
else
    regSign = -1;
end

% Mean of GP
m = GP_mean(dm_AObs,lambda_terms.dm_bObs,paramsOpt,m_init,obsTimes);

% Likelihood
L = likelihood(data,m,lambda_terms.invKObs,lambda_terms.L_init);
