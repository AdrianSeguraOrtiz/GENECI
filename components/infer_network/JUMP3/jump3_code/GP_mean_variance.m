function [exprMean,exprVar,kinParamsOpt,kinParamsOptVar] = GP_mean_variance(promState,lambda_terms,params,obsTimes,m_init)

nTS = params.nTS;
nStep = params.nStep;

%% Variance
exprVar = GP_variance(params,nStep);

%% Derivatives of the mean of GP w.r.t parameters A and b
[dm_A,dm_AObs] = mean_derivative_A(promState,params.lambda,obsTimes);

dm_b = mean_derivative_b(params.lambda,nStep,nTS);

%% Parameter optimization
[paramsOpt,kinParamsOptVar] = optimize_params_Ab(dm_AObs,lambda_terms,params);
kinParamsOpt.A = paramsOpt.A;
kinParamsOpt.b = paramsOpt.b;
kinParamsOpt.lambda = paramsOpt.lambda;

%% Mean of GP
exprMean = GP_mean(dm_A,dm_b,paramsOpt,m_init);
