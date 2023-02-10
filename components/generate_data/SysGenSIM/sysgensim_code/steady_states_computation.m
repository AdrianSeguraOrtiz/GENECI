function [Gt,Gwt,el_time,Gh] = steady_states_computation(n,m,A_syn,Zc,Zt,V,K_syn,h_syn,lambda,theta_syn,theta_deg,measurement_noise,heritability)
%
% Help for function: steady_states_cn.m
%
% [Gt,Gwt,el_time] = steady_states_cn(n,m,A,Zc,Zt,V,K,h,lambda,theta_syn,theta_deg,G0,s)
%
% THIS FUNCTION CALCULATES THE GENE ACTIVITY STEADY STATES FOR A CONDENSED
% NETWORK, EMPLOYING DIFFERENT METHODS.
%
% THE INPUT VARIABLES ARE:
% - n (NUMBER OF NODES)
% - m (NUMBER OF EXPERIMENTS / MEASUREMENTS)
% - A (ADJACENCE MATRIX)
% - Zc (polymorphism cis effects)
% - Zt (polymorphism trans effects)
% - V (BASAL TRANSCRIPTION RATE)
% - K (INTERACTION STRENGTH)
% - h (COOPERATIVITY COEFFICIENT)
% - lambda (DEGRADATION RATE)
% - theta_syn (gene- and experiment-specific biological variances in synthesis)
% - theta_deg (gene- and experiment-specific biological variances in degradation)
% - G0 (STARTING VALUES OF THE GENE ACTIVITIES)
% - s (SIMULATION FLAG STRUCTURE)
%
% THE OUTPUT VARIABLES ARE:
% - Gt (m x n MATRIX CONTAINING THE GENE ACTIVITY STEADY STATES)
% - el_time (TIME ELAPSED FOR THE WHOLE SIMULATION)

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

% Set options for ODE solver
options = odeset('InitialStep',0.05,'MaxStep',3.0,'RelTol',10^(-3),'AbsTol',10^(-6));

% Condense the network
[SCC,SCC_heights] = network_condensation(A_syn);
is_SCC_trivial = cellfun('length', SCC) == 1;

% Initialize matrices for m individuals and n genes
Gt = zeros(m,n);
if heritability
    Gh = zeros(m,n);
end

% Set integration interval for ODEs simulations
t1 = [0 5]';

% Sparsify matrices
A_deg = sparse(n,n);
h_deg = sparse(n,n);
K_deg = sparse(n,n);


% Calculate gene activity wild type
fprintf('Calculating the gene activity wild type steady states...\n');
G0 = ones(1,n);
D = 1;
stcr = 10^(-4);
Dcount = 0;
while D > stcr
    [~, G1] = ode45(@(t,G)eq_simplified_model(G,V,A_syn,K_syn,h_syn,lambda,A_deg,K_deg,h_deg,1:n,false,true), t1, G0, options);
    G0 = abs(G1(end,:)); % The wild types are the new starting values
    G_pen = abs(G1(end-1,:));
    D = max(G0-G_pen);
    Dcount = Dcount + 1;
    % fprintf('Count: %d\n',Dcount);
    if Dcount == 100
        stcr = stcr * 10;
        Dcount = 0;
    end
end
Gwt = G0;
fprintf('... Done!\n\n')



% Calculate gene activity steady states of m experimental runs

fprintf('Calculating the gene activity steady states...\n');

tic

max_SCC_heights = max(SCC_heights);
nontrivial_SCCs_at_height = cell(max_SCC_heights, 1);
trivial_SCC_vertices_at_height = cell(max_SCC_heights, 1);
for height = 1:max_SCC_heights
    SCC_is_at_height = SCC_heights == height; % True if the SCC is at this height
    nontrivial_SCCs_at_height{height} = find(SCC_is_at_height & ~is_SCC_trivial)';
    trivial_SCC_vertices_at_height{height} = cell2mat(SCC(SCC_is_at_height & is_SCC_trivial))'; % Indexes of the vertices of all the trivial SCCs at this height
end

for im = 1:m
    
    % Print the progress of the m experimental simulation runs
    string = sprintf('Simulating chip %d of %d...',im,m);
    fprintf('%s',string);
    
    if heritability
        G_im = repmat(G0,1,2);
        V_him = V .* Zc(:,im);
        V_im = V_him .* theta_syn(:,im);
        theta_im = (theta_syn(:,im) ./ theta_deg(:,im))';
    else
        G_im = G0;
        V_him = [];
        V_im = V .* Zc(:,im) .* theta_syn(:,im);
        theta_im = [];
    end
    
    lambda_im = lambda .* theta_deg(:,im);
    A_syn_im = A_syn;
    K_syn_im = K_syn;
    A_deg_im = A_deg;
    K_deg_im = K_deg;
    [rows_syn,cols_syn] = find(A_syn_im);
    [rows_deg,cols_deg] = find(A_deg_im);
    for i = 1:numel(rows_syn)
        K_syn_im(rows_syn(i),cols_syn(i)) = K_syn_im(rows_syn(i),cols_syn(i)) / Zt(rows_syn(i),im);
    end
    for i = 1:numel(rows_deg)
        K_deg_im(rows_deg(i),cols_deg(i)) = K_deg_im(rows_deg(i),cols_deg(i)) / Zt(rows_deg(i),im);
    end
    for height = 1 : max_SCC_heights
        for kk = nontrivial_SCCs_at_height{height} % Iterate over the nontrivial SCCs at this height
            I = SCC{kk}; % Indexes of the vertices of the next SCC
            D = 1;
            stcr = 10^(-4);
            Dcount = 0;
            while D > stcr
                [~, G1] = ode45(@(t,G)eq_simplified_model(G,V_him,A_syn_im,K_syn_im,h_syn,lambda,A_deg_im,K_deg_im,h_deg,I,false,false,heritability,V_im,lambda_im,theta_im), t1, G_im, options);
                G_im = abs(G1(end,:));
                G_pen = abs(G1(end-1,:));
                D = max(G_im-G_pen);
                Dcount = Dcount + 1;
                % fprintf('Count: %d\n',Dcount);
                if Dcount == 100
                    stcr = stcr * 10;
                    Dcount = 0;
                end
            end
        end
        G_im = eq_simplified_model(G_im,V_him,A_syn_im,K_syn_im,h_syn,lambda,A_deg_im,K_deg_im,h_deg,trivial_SCC_vertices_at_height{height},true,false,heritability,V_im,lambda_im,theta_im);
    end
    % Store current values of gene activity G_im in the i-th row of matrix Gt
    Gt(im,:) = G_im(1:n);
    if heritability
        Gh(im,:) = G_im(n+1:2*n);
    end
    
    
    % Remove string characters from command line
        for j = 1 : numel(string)
            fprintf('\b');
        end
    
end


Gt = Gt .* measurement_noise';
if heritability
    Gh = Gh .* measurement_noise';
else
    Gh = [];
end

% Total simulation elapsed time
el_time = toc;

fprintf('... Simulation of %d chips completed in ',m);
display_et(el_time);
fprintf('\n\n');