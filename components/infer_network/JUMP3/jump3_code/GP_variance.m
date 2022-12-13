function c = GP_variance(params,nStep)

lambda = params.lambda;
sigma = params.sysNoise;

time_points = 0:nStep;

expTerm = exp(-2*lambda*time_points);

c = (sigma/(2*lambda))*(1-expTerm);


