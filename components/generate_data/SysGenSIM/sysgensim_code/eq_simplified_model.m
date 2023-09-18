function ret = eq_simplified_model(G,V,A_syn,K_syn,h_syn,lambda,A_deg,K_deg,h_deg,I,ss,wt,heritability,V_im,lambda_im,theta_r)
% eq_simplified_model Evolution of gene expression.
% eq_simplified_model(G,V,A_syn,K_syn,h_syn,lambda,A_deg,K_deg,h_deg,I,ss)
% returns:
% - the steady steate of the gene expression if ss is true
% - the first derivative of the gene expression if ss is false.
% The input variables for the model are:
% - G      vector of the present gene expressions
% - V      vector of the gene transcription rates
% - A_syn  A_syn(j,i) is the maximum possible effect of gene j on the
%          transcription of gene i
% - K_syn  K_syn(j,i) is the expression value at which gene j produces an
%          effect equal to A_syn(j,i)/2 on the transcription of gene i
% - h_syn  h_syn(j,i) is the Hill cooperativity coefficient of A_syn(j,i)
% - lambda vector of the gene degradation rates
% - A_deg  A_deg(j,i) is the maximum possible effect of gene j on the
%          degradation of gene i
% - K_deg  K_deg(j,i) is the expression value at which gene j produces an
%          effect equal to A_deg(j,i)/2 on the degradation of gene i
% - h_deg  h_deg(j,i) is the Hill cooperativity coefficient of A_deg(j,i)
% - I      indices of the genes for which the gene expression has to be
%          calculated

% Copyright © 2011 CRS4 Srl. http://www.crs4.it/
% Created by:
% Nicola Soranzo <soranzo@crs4.it>
% Andrea Pinna <andrea.pinna@crs4.it>
%
% This file is part of SysGenSIM.
% For more information, visit http://sysgensim.sourceforge.net/ .
%
% This program is free software; you can redistribute it and/or modify it
% under the terms of the GNU General Public License as published by the
% Free Software Foundation; either version 2 of the License, or (at your
% option) any later version.
%
% This program is distributed in the hope that it will be useful, but
% WITHOUT ANY WARRANTY; without even the implied warranty of
% MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
% Public License for more details.
%
% You should have received a copy of the GNU General Public License along
% with this program. If not, see <http://www.gnu.org/licenses/>.

% Compute wild-type
if wt
    
    n = length(G);
    prod_syn = ones(n,1);
    prod_deg = ones(n,1);
    
    if nnz(A_syn)
        for i = I
            for j = find(A_syn(:,i))'
                prod_syn(i) = prod_syn(i) * ( 1 + A_syn(j,i) * G(j) ^ h_syn(j,i) / ( G(j) ^ h_syn(j,i) + K_syn(j,i) ^ h_syn(j,i) ) );
            end
        end
    end
    if nnz(A_deg)
        for i = I
            for j = find(A_deg(:,i))'
                prod_deg(i) = prod_deg(i) * ( 1 + A_deg(j,i) * G(j) ^ h_deg(j,i) / ( G(j) ^ h_deg(j,i) + K_deg(j,i) ^ h_deg(j,i) ) );
            end
        end
    end
    
    if ss
        ret = G;
        ret(I) = V(I) .* prod_syn(I) ./ ( lambda(I) .* prod_deg(I) );
    else
        ret = zeros(n,1);
        ret(I) = V(I) .* prod_syn(I) - lambda(I) .* prod_deg(I) .* G(I);
    end
    
    
    % Compute steady states
else
    
    if heritability
        
        n = length(G)/2;
        prod_syn = ones(n,1);
        prod_deg = ones(n,1);
        
        if nnz(A_syn)
            for i = I
                for j = find(A_syn(:,i))'
                    prod_syn(i) = prod_syn(i) * ( 1 + A_syn(j,i) * G(j) ^ h_syn(j,i) / ( G(j) ^ h_syn(j,i) + K_syn(j,i) ^ h_syn(j,i) ) );
                end
            end
        end
        if nnz(A_deg)
            for i = I
                for j = find(A_deg(:,i))'
                    prod_deg(i) = prod_deg(i) * ( 1 + A_deg(j,i) * G(j) ^ h_deg(j,i) / ( G(j) ^ h_deg(j,i) + K_deg(j,i) ^ h_deg(j,i) ) );
                end
            end
        end
        
        if ss
            [m1,m2] = size(G);
            if m2 < m1
                G = G';
            end
            ret = G;
            ret(n+I) = V(I) .* prod_syn(I) ./ ( lambda(I) .* prod_deg(I) ); % without bv
            ret(I) = ret(n+I) .* theta_r(I);
        else
            ret = zeros(2*n,1);
            ret(n+I) = V(I) .* prod_syn(I) - lambda(I) .* prod_deg(I) .* G(n+I); % without bv
            ret(I) = V_im(I) .* prod_syn(I) - lambda_im(I) .* prod_deg(I) .* G(I);
        end
        
        
    else
        
        n = length(G);
        prod_syn = ones(n,1);
        prod_deg = ones(n,1);
        
        if nnz(A_syn)
            for i = I
                for j = find(A_syn(:,i))'
                    prod_syn(i) = prod_syn(i) * ( 1 + A_syn(j,i) * G(j) ^ h_syn(j,i) / ( G(j) ^ h_syn(j,i) + K_syn(j,i) ^ h_syn(j,i) ) );
                end
            end
        end
        if nnz(A_deg)
            for i = I
                for j = find(A_deg(:,i))'
                    prod_deg(i) = prod_deg(i) * ( 1 + A_deg(j,i) * G(j) ^ h_deg(j,i) / ( G(j) ^ h_deg(j,i) + K_deg(j,i) ^ h_deg(j,i) ) );
                end
            end
        end
        
        if ss
            ret = G;
            ret(I) = V_im(I) .* prod_syn(I) ./ ( lambda_im(I) .* prod_deg(I) );
        else
            ret = zeros(n,1);
            ret(I) = V_im(I) .* prod_syn(I) - lambda_im(I) .* prod_deg(I) .* G(I);
        end
        
    end
    
end