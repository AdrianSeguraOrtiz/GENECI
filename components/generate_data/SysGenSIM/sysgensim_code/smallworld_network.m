function Y = smallworld_network(n, avg_degree, p)
%smallworld_network Directed small-world random network.
%   smallworld_network(N,AVG_DEGREE,P) returns the adjacency matrix of a
%   loopless directed small-world random network of N nodes with average
%   node degree AVG_DEGREE using a Watts-Strogatz model [1] with P as the
%   probability of link rewiring.
%
%   [1] Watts, D.J., Strogatz, S.H. - Collective dynamics of
%   'small-world' networks - Nature 393(6684) - pp. 440–442 - 1998

% Copyright © 2006 Ginestra Bianconi <g.bianconi@neu.edu>
% Copyright © 2006,2007 Nicola Soranzo <soranzo@crs4.it>
%
% Copyright © 2011 CRS4 Srl. http://www.crs4.it/
% Modified by:
% Andrea Pinna <andrea.pinna@crs4.it>
% Nicola Soranzo <soranzo@crs4.it>
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

if nargin < 3
    error('3 arguments required')
end
if ~isscalar(n) || ~isreal(n) || ischar(n) || rem(n, 1) ~= 0 || n < 0
	error('n must be a scalar integer >= 0')
end
if ~isscalar(avg_degree) || ~isreal(avg_degree) || ischar(avg_degree) || avg_degree < 0 || avg_degree > (n - 1) * 2
	error('avg_degree must be a scalar real >= 0 and <= (n - 1) * 2')
end
if ~isscalar(p) || ~isreal(p) || ischar(p) || p < 0 || p > 1
	error('p must be a scalar real >= 0 and <= 1')
end

Y = zeros(n);
% Double-connect each node to its ~(avg_degree/4) right nearest neighbours.
% So, the total number of added edges is ~= n * avg_degree/4 * 2 = n *
% avg_degree / 2 and the average node degree is n_edges * 2 / n ~=
% avg_degree
right_outdegrees = truncated_randn(avg_degree/4,0.1,floor(avg_degree/4),ceil(avg_degree/4),[n,1]);
for i = 1:n
    for count = 1:round(right_outdegrees(i))
        j = mod(i+count-1, n) + 1; % ensure j is in 1:n
        Y(i, j) = 1;
        Y(j, i) = 1;
    end
end

% Rewire edges
for i = 1:n
    for j = find(Y(i,:))
        if (rand(1) <= p)
            % find a new destination node
            new_j = j;
            Y(i, j) = 0;
            while new_j == i || Y(i, new_j) == 1
                new_j = ceil(rand(1) * n);
            end
            Y(i, new_j) = 1;
        end
    end
end

% Sparsify the network matrix
Y = sparse(Y);