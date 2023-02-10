function [A,nm,Kdm,perw,r,Q] = modular_network(n,m,prw,Kdn,network)

% Copyright © 2011 CRS4 Srl. http://www.crs4.it/
% Created by:
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

% Size of modules is not specified and common average degree is set
if numel(m) == 1 && numel(Kdn) == 1
    if rem(m,1) ~= 0 || m < 3 || m >= n
        error('The number of modules m must be an integer larger than 2 and smaller than n!');
    end
    % Number of nodes for each module
    nm = module_sizes(m,n);
    % Number of between-module edges
    bme = round(prw*Kdn*n);
    % Desired average degree for each module
    Kdm = Kdn*ones(1,m);
    
% Size of modules is not specified and average degree is set for each module
elseif numel(m) == 1 && numel(Kdn) == m
    % Number of nodes for each module
    nm = module_sizes(m,n);
    % Number of between-module edges (weighted on each module)
    bme = ceil(prw*sum(Kdn.*nm));
    % Desired average degree for each module
    Kdm = Kdn;
    
% Size of modules is specified and common average degree is set
elseif numel(m) > 1 && numel(Kdn) == 1
    if sum(m) ~= n
        error('Sum of nodes in modules is not consistent with n!');
    end
    nm = m;
    m = numel(nm);
    if rem(m,1) ~= 0 || m < 3 || m >= n
        error('The number of modules m must be an integer larger than 2 and smaller than n!');
    end
    % Number of between-module edges
    bme = round(prw*Kdn*n);
    % Desired average degree for each module
    Kdm = Kdn*ones(1,m);
    
% Size of modules is specified and average degree is set for each module
elseif numel(m) > 1 && numel(Kdn) > 1
    if sum(m) ~= n
        error('Sum of nodes in modules is not consistent with n!');
    end
    if numel(Kdn) ~= numel(m)
        error('Number of desired average degrees is not consistent with the number of modules!');
    end
    nm = m;
    m = numel(nm);
    if rem(m,1) ~= 0 || m < 3 || m >= n
        error('The number of modules m must be an integer larger than 2 and smaller than n!');
    end
    % Number of between-module edges (weighted on each module)
    bme = ceil(prw*sum(Kdn.*nm));
    % Desired average degree for each module
    Kdm = Kdn;
    
else
    error('Check the input variables!');
end




% Build singular modules
B = cell(m);
for i = 1 : m
    for j = 1 : m
        if i == j
            if strcmp(network,'random-modular')
                B{i,j} = random_network(nm(i),Kdm(i));
            elseif strcmp(network,'eipo-modular')
                B{i,j} = exp_in_pow_out_network(nm(i),Kdm(i));
            else
                error('Check the name of the modular network!');
            end
        else
            B{i,j} = zeros(nm(i),nm(j));
        end
    end
end


% Generate the list of modules to be connected
ml = zeros(bme,1);
% Assign the probability, for each module, to be chosen in the list
Pm = Kdm.*nm;
Pc = Pm;
for j = 2 : numel(Pc)
    Pc(j) = Pc(j-1) + Pm(j);
end
Pc = Pc / max(Pc);
% Assignment of the first module
ml(1) = find(Pc>=rand(1),1,'first');
% Assignment of the remaining modules
for i = 2 : bme
    ml(i) = find(Pc>=rand(1),1,'first');
    while ml(i) == ml(i-1)
        ml(i) = find(Pc>=rand(1),1,'first');
    end
end
% Possible re-assignment of the last module
while ml(1) == ml(bme) || ml(bme-1) == ml(bme)
    ml(bme) = find(Pc>=rand(1),1,'first');
end




% Select the between-module edges
Nout = zeros(bme,1);
Nin = zeros(bme,1);
for k = 1 : bme
    % Find all the existing edges in the current modules
    [I,J] = find(B{ml(k),ml(k)});
    % Permute all the nodes with outgoing edges
    R = randperm(numel(I));
    % Identify the source (tail) node and the receiver (head) node
    if ml(k) == 1
        Nout(k) = I(R(1));
        Nin(k) = J(R(1));
    else
        Nout(k) = I(R(1)) + sum(nm(1:(ml(k)-1)));
        Nin(k) = J(R(1)) + sum(nm(1:(ml(k)-1)));
    end
    % Remove the current inner-module edge
    B{ml(k),ml(k)}(I(R(1)),J(R(1))) = 0;
    
end


% Assembling the final network
A = zeros(n);
kj = 1;
for j = 1 : m
    ki = 1;
    for i = 1 : m
        A(ki:nm(i)+ki-1,kj:nm(j)+kj-1) = B{i,j};
        ki = ki + nm(i);
    end
    kj = kj + nm(j);
end
% Connecting the between-module edges
for k = 1 : (bme-1)
    A(Nout(k),Nin(k+1)) = 1;
end
A(Nout(bme),Nin(1)) = 1;
% Sparsifying the network and sign assignment of edges
A = sparse(remove_diag(A));


% Assortativity
r = assortativity(abs(A));

% Modularity
Q = modularity(abs(A),nm);

% Effective percentage of rewired edges
perw = 100*bme/nnz(A);