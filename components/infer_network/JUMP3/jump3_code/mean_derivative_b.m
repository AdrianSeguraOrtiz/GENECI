function dm_b = mean_derivative_b(lambda,nStep,nTS,obsTimes)
%
%Computes derivative of the mean of GP with respect to b.

if nargin > 3
 
    obsTimes_all = zeros(1,nStep);
    for k=1:nTS
        obsTimes_all(obsTimes{k}(2:end)) = 1;
    end
    obsTimes_all = find(obsTimes_all);
    
    dm_b_tmp = zeros(1,nStep);
    dm_b_tmp(obsTimes_all) = (1-exp(-lambda*obsTimes_all))/lambda;
    
    dm_b = cell(1,nTS);
    for k=1:nTS
        dm_b{k} = [0 dm_b_tmp(obsTimes{k}(2:end))]; % first time point is t=0
    end
  
else
   
    time_points = 1:nStep;
    dm_b = [0 (1-exp(-lambda*time_points))/lambda];
    
end
    
    