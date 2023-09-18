function A = acyclic_random_network(n,avg_degree)
%acyclic_random_network Directed acyclic random network.
%   acyclic_random_network(N,AVG_DEGREE) returns the adjacency matrix of a
%   directed acyclic random network of N nodes with average degree
%   AVG_DEGREE.

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

% Algorithm idea: a graph is acyclic if and only if its adjacency matrix
% can be rearranged in upper triangular form.

if nargin < 2
    error('2 arguments required')
end
if ~isscalar(avg_degree) || ~isreal(avg_degree) || ischar(avg_degree) || avg_degree < 0 || avg_degree > (n - 1)
	error('avg_degree must be a scalar real >= 0 and <= (n - 1)')
end

% Create a random network with doubled desired average degree
A = random_network(n,2*avg_degree);

% Set the lower triangular matrix to zero, i.e. make the graph acyclic
A = triu(A);