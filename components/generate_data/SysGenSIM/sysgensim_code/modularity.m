function Q = modularity(A,nm)

% Copyright © 2011 CRS4 Srl. http://www.crs4.it/
% Created by:
% Andrea Pinna <andrea.pinna@crs4.it>
% Nicola Soranzo <soranzo@crs4.it>
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

% Undirecting the network
A = uu_network(A);

% Number of nodes of the network
n = length(A);

% Number of edges in the undirected network
m = nnz(A)/2;

% Modules for each node
c = zeros(1,n);
for i = 1 : numel(nm)
    c( 1+sum(nm(1:i-1)) : sum(nm(1:i)) ) = i;
end

% Degrees for each node
K = sum(logical(A),2);

% Modularity
S = 0;
% Kronecker delta: C(i,j) = 1 when nodes i and j belong to the same module
C = ones(n,1)*c == c'*ones(1,n);
B = zeros(n);
for j = 1 : n
    B(:,j) = A(:,j) - ( K(:) * K(j) ) / (2*m) ;
end
D = B.*C;
% Edges are counted only once
[I,J] = find(tril(D));
for i = 1 : numel(I)
    S = S + D(I(i),J(i));
end
Q = S / (2*m);