function K = GP_covariance(params,obsTimes)

lambda = params.lambda;
sysNoise = params.sysNoise;
nTS = params.nTS;
nsamples = params.nsamples;
obsTimes_all = params.obsTimes_all;

Nall = length(obsTimes_all);
Kall = zeros(Nall,Nall);

for i=1:Nall

    t1 = obsTimes_all(i);

    for j=i:Nall

        t2 = obsTimes_all(j);

        expTerm = exp(-lambda*(t1+t2));

        Kvalue = (sysNoise/(2*lambda)) * (exp(-lambda*abs(t1-t2)) - expTerm);
        Kall(i,j) = Kvalue;
        Kall(j,i) = Kvalue;
    end
end


K = cell(1,nTS);

for k=1:nTS
    
    obsTimes_k = obsTimes{k};    
    obsTimes2 = zeros(1,nsamples(k));
    
    for i=1:nsamples(k)
        obsTimes2(i) = find(obsTimes_all==obsTimes_k(i));
    end
    
    K{k} = Kall(obsTimes2,obsTimes2);
    
    
end



