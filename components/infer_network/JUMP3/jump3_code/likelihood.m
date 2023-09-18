function L = likelihood(data,mObs,invK,L_init)
%function L = likelihood(data,mObs,invK,L_init)


nTS = length(data);

L = L_init;

for k=1:nTS

    fitTerm = data{k}-mObs{k};
    L = L - 0.5*fitTerm*invK{k}*fitTerm';
    
end
