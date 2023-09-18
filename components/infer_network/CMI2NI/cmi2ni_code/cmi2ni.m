% *************************************************************************
% CMI2NI: Conditional mutual inclusive information(CMI2)-based Network
% Inference method from gene expression data  
% *************************************************************************
% This is matlab code for netwrk inference method CMI2NI. 
% Input:
% 'data' is expression of variable,in which row is varible and column is the sample;
% 'lamda' is the parameter decide the dependence;
% 'order0' is the parameter to end the program when order=order0;
% If nargin==2,the algorithm will be terminated untill there is no change 
% in network toplogy.
% Output: 
% 'G' is the 0-1 network or graph after pc algorithm;
% 'Gval' is the network with strenthness of dependence;
% 'order' is the order of the pc algorithm, here is equal to order0;
% Example:
% 
% Author: Xiujun Zhang.
% Version: Sept.2014.

function [G,Gval,order]=cmi2ni(data,lamda,order0)                                                 
n_gene=size(data,1);
G=ones(n_gene,n_gene);
G=tril(G,-1)'; 
G=G+G';
Gval=G;
order=-1;t=0;
while t==0
     order=order+1;
     if nargin==3
       if order>order0
           order=order-1; % 
           return
       end
     end
    [G,Gval,t]=edgereduce(G,Gval,order,data,t,lamda) ;
 
     if t==0
          disp('No edge is reduce! Algorithm  finished!');
          break;
     else 
          t=0;
     end
end
   order=order-1; % The value of order is the last order of the algorithm 
end

%% edgereduce  
function [G,Gval,t]=edgereduce(G,Gval,order,data,t,lamda)
G0=G;
%[nrow,ncol]=find(G~=0);
if order==0
    for i=1:size(G,1)
        for j=1:size(G,1)
            if G(i,j)~=0
                cmiv=cmi(data(i,:),data(j,:));
                Gval(i,j)=cmiv;  Gval(j,i)=cmiv;
                if cmiv<lamda
                    G(i,j)=0;G(j,i)=0;
                end
            end
        end
    end
          t=t+1;
else
  for i=1:size(G,1)
      for j=1:size(G,1)
          if G(i,j)~=0
              adj=[] ;
              for k=1:size(G,1)
                  if G(i,k)~=0 && G(j,k)~=0
                      adj=[adj,k] ;
                  end
              end
              if size(adj,2)>=order
                   combntnslist=nchoosek(adj,order);
                   combntnsrow=size(combntnslist,1);   
                   cmiv=0;
                   v1=data(i,:);v2=data(j,:);
                   for k=1:combntnsrow   
                     vcs=data(combntnslist(k,:),:);   
                     a=MI2(v1,v2,vcs) ;
                     cmiv=max(cmiv,a);
                   end
                   Gval(i,j)=cmiv; Gval(j,i)=cmiv;
                   if cmiv<lamda
                         G(i,j)=0; G(j,i)=0;
                   end              
                   t=t+1; 
              end
          end
                      
      end
  end 
%   if t~=0 && ((size(G0,1)*size(G0,2))-sum(sum(G==G0))<20)
%   if t~=0 && ((size(G0,1)*size(G0,2))-sum(sum(G==G0))==0)
%       t = 0; 
%   end               
end
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
    % cmiv=abs(cmiv);
     if  cmiv==inf 
            cmiv=1.0e+010;
     end
end

% Conditional mutul inclusive information (CMI2)
function r_dmi = MI2(x,y,z)
r_dmi = (cas(x,y,z) + cas(y,x,z))/2;
end

% x and y are 1*m dimensional vector; z is n1*m dimensional.
function CS = cas(x,y,z)
% x=rand(10,1)';y=rand(10,1)';z=rand(10,2)';
% x,y,z are row vectors;
n1 = size(z,1);
n = n1 +2;

Cov = cov(x);
Covm = cov([x;y;z]');
Covm1 = cov([x;z]');

InvCov = inv(Cov);
InvCovm = inv(Covm);
InvCovm1 = inv(Covm1);

C11 = InvCovm1(1,1);
C12 = 0;
C13 = InvCovm1(1,2:1+n1);
C23 = InvCovm(2,3:2+n1)-InvCovm(1,2) * (1/(InvCovm(1,1)-InvCovm1(1,1)+InvCov(1,1))) * (InvCovm(1,3:2+n1) - InvCovm1(1,2:1+n1)) ;
C22 = InvCovm(2,2)- InvCovm(1,2)^2 * (1/(InvCovm(1,1)-InvCovm1(1,1)+InvCov(1,1)));
C33 = InvCovm(3:2+n1,3:2+n1)- (1/(InvCovm(1,1)-InvCovm1(1,1)+InvCov(1,1))) * ((InvCovm(1,3:2+n1)-InvCovm1(1,2:1+n1))'*(InvCovm(1,3:2+n1)-InvCovm1(1,2:1+n1)));
InvC = [[C11,C12,C13];[C12,C22,C23];[[C13',C23'],C33]];
% C = inv(InvC);  

C0 = Cov(1,1) * (InvCovm(1,1) - InvCovm1(1,1) + InvCov(1,1));
CS = 0.5 * (trace(InvC*Covm)+log(C0)-n) ;
 
end