function vip =plsrank(trn,ytrn,nfac)
%===============================================
%   PLSrrank - PLS-based feature ranking
%===============================================
% @Input
%  trn  -  training examples
%  ytrn - target gene  
%   nfac - number of components. The default value is 5.
%   trn is a data matrix whose rows correspond to samples(or observations) and whose
%   columns correspond to genes (or features).  trn and ytrn
%   must have the same number of rows.
%
% @Output
%  vip - feature weights with large positive weights assigned to important feature.
%

if nargin<3 || isempty(nfac)
    nfac=length(unique(ytrn));
end

X=trn;
Y=ytrn;

[pctvar,W]=plsreg(X,Y,nfac);
vip=size(X,2)*pctvar(2,:)*(W.^2)'/sum(pctvar(2,:));
end

function [pctVar,W] = plsreg(X,Y,ncomp)
meanX = mean(X,1);
meanY = mean(Y,1);
X0 = bsxfun(@minus, X, meanX);
Y0 = bsxfun(@minus, Y, meanY);
[Xloadings,Yloadings,Weights] = simpls(X0,Y0,ncomp);
pctVar = [sum(Xloadings.^2,1) ./ sum(sum(X0.^2,1));
    sum(Yloadings.^2,1) ./ sum(sum(Y0.^2,1))];
W = Weights;
end

function [Xloadings,Yloadings,Weights] = simpls(X0,Y0,ncomp)
dx = size(X0,2);
dy = size(Y0,2);
outClass = superiorfloat(X0,Y0);
Xloadings = zeros(dx,ncomp,outClass);
Yloadings = zeros(dy,ncomp,outClass);
Weights = zeros(dx,ncomp,outClass);
V = zeros(dx,ncomp);
Cov = X0'*Y0;
for i = 1:ncomp
    [ri,si,ci] = svd(Cov,'econ'); ri = ri(:,1); ci = ci(:,1); si = si(1);
    ti = X0*ri;
    normti = norm(ti); ti = ti ./ normti;
    Xloadings(:,i) = X0'*ti;
    qi = si*ci/normti;
    Yloadings(:,i) = qi;
    Weights(:,i) = ri ./ normti;
    vi = Xloadings(:,i);
    for repeat = 1:2
        for j = 1:i-1
            vj = V(:,j);
            vi = vi - (vi'*vj)*vj;
        end
    end
    vi = vi ./ norm(vi);
    V(:,i) = vi;
    Cov = Cov - vi*(vi'*Cov);
    Vi = V(:,1:i);
    Cov = Cov - Vi*(Vi'*Cov);
end
end