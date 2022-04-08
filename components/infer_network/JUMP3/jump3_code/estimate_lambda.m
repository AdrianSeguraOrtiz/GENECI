function lambda = estimate_lambda(data,obsTimes)
%function lambda = estimate_lambda(data,obsTimes)
%
%Estimate value of parameter lambda
%
% We suppose that x decreases according to exp(-lambda*t) between the
% highest and lowest observed expression levels.

nTS = length(data);

lambda = zeros(1,nTS);

for k=1:nTS

    t = double(obsTimes{k});
    x = data{k};
    x(x==0) = 1e-6;

    x_min = min(x);
    x_max = max(x);
    
    idx_min = find(x==x_min,1,'first');
    idx_max = find(x==x_max,1,'first');
    
    lambda(k) = abs(log(x_min)-log(x_max)) / abs(t(idx_min)-t(idx_max));

   
end

lambda = max(lambda);

