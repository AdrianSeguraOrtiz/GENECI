function [dm_A_new,dm_AObs_new] = mean_derivative_A_update(qM_new,qM_old,dm_A_old,lambda,obsTimes)
%
%Updates the derivative of the mean of GP with respect to A.

nTS = size(qM_new,1);
nStep = size(qM_new,2)-1;

dm_A_new = zeros(nTS,nStep+1);

expLambda = exp(-lambda);

for k=1:nTS

    qM_diff = qM_new(k,:) - qM_old(k,:);
    
    idx_start = 2;
    
    while (idx_start <= nStep+1) && (qM_diff(idx_start) == 0)
        dm_A_new(k,idx_start) = dm_A_old(k,idx_start);
        idx_start = idx_start + 1;
    end
    
    if sum(qM_new(k,1:idx_start-1)) == 0
        
        while (idx_start <= nStep+1) && (qM_new(k,idx_start) == 0)
            idx_start = idx_start + 1;
        end
        
    end
       
    for t=idx_start:nStep+1
        dm_A_new(k,t) = expLambda*dm_A_new(k,t-1) + qM_new(k,t);
    end
         
end



if nargin > 4
    
    dm_AObs_new = cell(1,nTS);
    for k=1:nTS
        dm_AObs_new{k} = [0 dm_A_new(k,obsTimes{k}(2:end)+1)];   
    end
    
end



