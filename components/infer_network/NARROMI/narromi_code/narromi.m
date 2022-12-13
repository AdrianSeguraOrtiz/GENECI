% Function NARROMI.M for inferring gene regulatory networks from expression
% data.
% Input: 
%     y: Expression of target gene;
%     X: Expressions of regulators(TFs);
%     lamda: Regulization parameter for optimization;
%     alpha: Parameter for filtering genes with low MI correlations;
%     beta: Parameter for filtering genes with low  regulatory strength for RO;
%     t: Parameter for the interation of MI and RO;
% Output:
%     net: Inferred sparse network;
%     net_value: Inferred network with regulatory strength;
%     sig: Inferred network with statistic significance;
% Version Data: 2012-03-18
% ZHANG X. @ SHU && UA.

function [net,net_value,sig]=narromi(y,X,lamda,alpha, beta,t)
% y is a column vector/gene, row are samples;
% X is a matrix with column are genes, rows are samples.
net = zeros(1,size(X,2));net_value = net; G1 = net; 
for i=1:size(X,2)
    G1(1,i) = cmi(y,X(:,i)); 
end 
  net_value = G1';
  index = find(abs(G1)>=alpha);
  X1 = X(:,index);
  [J_sparse,J_value] = reoptim(y',X1',lamda,beta) ;
  net(index)= J_sparse'  ;
  net_value(index) = J_value' ; net_value1 = net_value;
  
  net_value = sign(net_value).*(abs(net_value).*t + G1'.*(1-t));
  
  z = (abs(net_value1));  
  z = (z-min(z))./(max(z)-min(z));  z = 0.5.*log2((1+z)./(1-z));  z(z==max(z)) = max(z(z~=max(z)));
  mu = mean(z);sigma = var(z);
 sig1=1-normcdf(z,mu,sigma);
 
  z = (abs(G1'));
  z = (z-min(z))./(max(z)-min(z));  z = 0.5.*log2((1+z)./(1-z));  z(z==max(z)) = max(z(z~=max(z)));
  mu = mean(z);sigma = var(z); 
 
sig2=1-normcdf(z,mu,sigma);  
 
 sig = sqrt(sig1.^2 + sig2.^2);
 
 sig(sig<1.0e-32)=1.0e-32;

end

%% compute conditional mutual information of x and y
function cmiv=cmi(v1,v2,vcs)
 if  nargin==2
        c1=det(cov(v1));
        c2=det(cov(v2));
        c3=det(cov(v1,v2));
        cmiv=0.5*log(c1*c2/c3); 
        
     elseif  nargin==3
        c1=det(cov([v1;vcs]'));
        c2=det(cov([v2;vcs]'));
        c3=det(cov(vcs'));
        c4=det(cov([v1;v2;vcs]'));
        cmiv=0.5*log((c1*c2)/(c3*c4));       
 end
     cmiv=abs(cmiv);
     if cmiv==inf
         cmiv=1.0e+01;
     end
end

function [J_sparse,J_value] = reoptim(y,X,lamda,alpha)
 [J]=LP_TGN(y,X,lamda); % y=Y', X=Phi'
 J_sparse = zeros(size(J)); J_value = J_sparse;
 
 index =  find(abs(J)>=alpha); index_c = find(abs(J)<alpha) ;
 
J_sparse(index) = J(index); J_value(index_c) = J(index_c); 
 while (~isempty(index_c))
 
     [J1]=LP_TGN(y,X(index,:),lamda) ;
     index1 = find(abs(J1)>=alpha);index1_c = find(abs(J1)<alpha);
     index_c = index(index1_c); index = index(index1);
     J_sparse(index) = J1(index1); J_sparse(index_c) = 0;
     J_value(index_c) = J1(index1_c);
 
 end
 
 J_value = J_sparse + J_value;
  
end
 
% function LP_TGN_infer 
 
function [J]=LP_TGN(Y,X,lamda)
[n,m]=size(Y);
[p,q]=size(X);
 
c=n*m; h=n*p;
f=[ones(1,2*c),lamda*ones(1,2*h)]';
Y_1=Y';
beq=Y_1(:);
A1=sparse(1:c,1:c,ones(1,c),c,c);
A2=sparse(1:c,1:c,-ones(1,c),c,c);
Z=X';
Z_1=Z;
for i=1:n-1
    Z_1=blkdiag(Z_1,Z);
    Z_1=sparse(Z_1);
 
end
Z_2=-Z_1;
Aeq=[A1,A2,Z_1,Z_2];
Aeq=sparse(Aeq);
clear A1 A2 Z_1 Z_2 Z Y_1;
lb=zeros(2*(c+h),1);
options = optimoptions('linprog','Display','none');
x=linprog(f,[],[],Aeq,beq,lb,[],options);
x=x';
s=zeros(n,p);
s=sparse(s);
t=zeros(n,p);
t=sparse(t);
J=zeros(n,p);
J=sparse(J);
for i=1:n
    for k=1:p
        s(i,k)=x(2*n*m+(i-1)*p+k);
        t(i,k)=x(2*n*m+n*p+(i-1)*p+k);
    end
end
 
J=s-t;
 
J=full(J);
 
end
 