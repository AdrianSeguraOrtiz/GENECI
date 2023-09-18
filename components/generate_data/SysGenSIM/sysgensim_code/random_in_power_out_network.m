function [A] = random_in_power_out_network(n,avg_degree)

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
    error('The number of nodes must be a non-negative integer scalar')
end
if ~isscalar(avg_degree) || ~isreal(avg_degree) || ischar(avg_degree) || avg_degree < 0 || avg_degree > 2*n-2
    error('The average degree must be a real scalar between 0 and 2*(n-1)')
end

avg_outdegree = avg_degree / 2;

% Estimate gamma
gamma = find_gamma(n,avg_outdegree);

% Calculate P(k) for all possible outdegrees (0:n-1)
% Pk(i) contains P(k=i-1)
Pk = (1:n) .^ -gamma;
Pk = Pk ./ sum(Pk);

cumsum_Pk = cumsum(Pk);
r = rand(1,n);
outdegree = zeros(1,n);
rows = [];
cols = [];
for i = 1:n
    outdegree(i) = find(r(i) <= cumsum_Pk, 1) - 1;% The - 1 is because Pk(i) contains P(k=i-1)
    possible_targets = [1:i-1 i+1:n];
    permuted_possible_targets = possible_targets(randperm(n-1));
    rows = [rows i * ones(1,outdegree(i))];
    cols = [cols permuted_possible_targets(1:outdegree(i))];
end
A = sparse(rows,cols,1,n,n);
end