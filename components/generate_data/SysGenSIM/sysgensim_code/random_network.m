function A = random_network(n,avg_degree)
%random_network Directed random network.
%   random_network(N,AVG_DEGREE) returns the adjacency matrix of a loopless
%   directed random network of N nodes with average degree AVG_DEGREE.

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

if nargin < 2
    error('2 arguments required')
end

if ~isscalar(n) || ~isreal(n) || ischar(n) || rem(n, 1) ~= 0 || n < 0
	error('n must be a scalar integer >= 0')
end
if ~isscalar(avg_degree) || ~isreal(avg_degree) || ischar(avg_degree) || avg_degree < 0 || avg_degree > (n - 1) * 2
	error('avg_degree must be a scalar real >= 0 and <= (n - 1) * 2')
end

% Link probability for random networks =
% n_edges / n_possible_edges =
% (avg_degree * n / 2) / (n * (n-1))
p = avg_degree/(2*(n-1));

% Edge probability matrix
R = rand(n);
% Directed and unsigned matrix
A = sparse(remove_diag(R<p));