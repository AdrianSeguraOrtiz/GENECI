function [dm_A,dm_AObs] = mean_derivative_A(promState,lambda,obsTimes)
%function [dm_A,dm_AObs] = mean_derivative_A(promState,lambda,obsTimes)
%
%Computes derivative of the mean of GP with respect to A.

nTS = size(promState,1);
nStep = size(promState,2)-1;

dm_A = zeros(nTS,nStep+1);

expLambda = exp(-lambda);

for k=1:nTS
     
    idx_start = 2;
    
    % dm_A(k,1:T) = 0 when promState(k,t) = 0 for all t <= T
    while (idx_start <= nStep+1) && (promState(k,idx_start) == 0)
        idx_start = idx_start + 1;
    end

        
    for t=idx_start:nStep+1
        dm_A(k,t) = expLambda*dm_A(k,t-1) + promState(k,t);
    end

end

if nargin > 2
    
    dm_AObs = cell(1,nTS);
    for k=1:nTS
        dm_AObs{k} = [0 dm_A(k,obsTimes{k}(2:end)+1)];   
    end

end

