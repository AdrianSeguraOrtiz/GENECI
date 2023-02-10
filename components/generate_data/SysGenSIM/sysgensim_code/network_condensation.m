function [SCC,SCC_heights] = network_condensation(A)
%
% Help for function: network_condensation.m
%
% [SCC,SCC_heights] = network_condensation(A)
%
% This function, given a non-acyclic network, yields its condensed version.
%
% The input variable is:
% - A (matrix representing the gene network)
%
% The output variables are
% SCC         cell containing the indices of the nodes belonging to the
%             strongly connected components
% SCC_heights height of each SCC

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

fprintf('Condensing the network...\n')

if isdag(digraph(A)) % Matrix A already represents a directed acyclic graph
    S = length(A);
    SCC = cell(S,1);
    for i = 1 : S
        SCC{i} = i;
    end
    Ac = A;
else % Matrix A does not represent a directed acyclic graph
    [S,C] = my_conncomp(A);
    SCC = cell(S,1);
    for i = 1 : S
        SCC{i} = find(C == i);
    end
    Ac = logical(sparse(S, S)); % condensed network
    [rows,cols] = find(A);
    for i = 1:length(rows)
        Ac(C(rows(i)), C(cols(i))) = true;
    end
    Ac = Ac - diag(diag(Ac));
end

% Topological order to explore nodes of the condensed network
SCC_topo_order = toposort(digraph(Ac));

SCC_heights = ones(S, 1);
Ac_trans = Ac';
for i = SCC_topo_order
    for j = find(Ac_trans(:, i))'
        SCC_heights(j) = max(SCC_heights(j), SCC_heights(i) + 1);
    end
end


fprintf('... Done!\n\n')

end