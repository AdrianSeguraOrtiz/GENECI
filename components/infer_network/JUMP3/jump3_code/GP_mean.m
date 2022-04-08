function m = GP_mean(dm_A,dm_b,params,m_init,time_points)

A = params.A;
b = params.b;
lambda = params.lambda;

nTS = length(m_init);

if nargin > 4

    m = cell(1,nTS);

    for k=1:nTS
        m{k} = m_init(k)*exp(-lambda*time_points{k}) + A*dm_A{k} + b*dm_b{k};
    end
    
else

    nStep = size(dm_A,2)-1;
    m = zeros(nTS,nStep+1);
    
    time_points = 0:nStep;

    for k=1:nTS
        m(k,:) = m_init(k)*exp(-lambda*time_points) + A*dm_A(k,:) + b*dm_b;
    end
    
end
    
