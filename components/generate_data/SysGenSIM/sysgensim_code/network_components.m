function [LSCC,IN,OUT,DN,TENin,TENout,TUB,N] = network_components(A)

% Copyright © 2011-2015 CRS4 Srl. http://www.crs4.it/
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

% Remove signs
A = abs(A);

% Size of the network
n = length(A);

% Undirected and unsigned network
Auu = uu_network(A);

% Strongly connected components of the network
[S,C] = my_conncomp(A);

% Weak components of the network
[Suu,Cuu] = my_conncomp(Auu);

% Shortest paths between nodes
D = distances(digraph(A));

% Set of all nodes
ALL = 1 : n;

% Find largest strongly connected component (LSCC)
SCC = cell(S,1);
sSCC = zeros(S,1);
for i = 1 : S
    SCC{i} = find(C == i);
    sSCC(i) = numel(SCC{i});
end
[~,I] = max(sSCC);
LSCC = SCC{I};

% Find disconnected nodes (DN)
SCCuu = cell(Suu,1);
sSCCuu = zeros(Suu,1);
for i = 1 : Suu
    SCCuu{i} = find(Cuu == i);
    sSCCuu(i) = numel(SCCuu{i});
end
[~,I] = max(sSCCuu);


DN = setdiff_wr(ALL,SCCuu{I});

% Find in-component (IN)
I = setdiff_wr(ALL,union_wr(LSCC,DN));
Iin = find(D(:,LSCC(1))~=Inf & D(:,LSCC(1))~=0);
IN = intersect_wr(I,Iin);

% Find out-component (OUT)
I = setdiff_wr(ALL,union_wr(LSCC,union_wr(DN,IN)));
Iout = find(D(LSCC(1),:)~=Inf & D(LSCC(1),:)~=0);
OUT = intersect_wr(I,Iout);

% Find tendrils (TEN)
I = setdiff_wr(ALL,union_wr(LSCC,union_wr(DN,union_wr(IN,OUT))));
Iten = find(isinf(D(:,LSCC(1))));
TEN = intersect_wr(I,Iten);
[~,Itin] = find(D(IN,:)~=Inf);

% Input and output tendrils
TENin = setdiff_wr(unique_wr(Itin),union_wr(LSCC,union_wr(DN,union_wr(IN,OUT))));
TENout = setdiff_wr(TEN,TENin);


% Find tubes (TUB)
TUB = [];
h = 1;
if ~isempty(TENin)
    for i = TENin
        if any(~isinf(D(IN,i))) && any(~isinf(D(i,OUT)))
            TUB(h) = i;
            h = h + 1;
        end
    end
end

TUB = unique_wr(TUB);
TENin = setdiff_wr(TENin,TUB);

% Check
N = numel(LSCC)+numel(DN)+numel(IN)+numel(OUT)+numel(TENin)+numel(TENout)+numel(TUB);
if ~isequal(n,N)
    error('The number of nodes in all groups is NOT consistent with the size of the network!');
end
if ~isequal(1:n,sort([LSCC,DN,IN,OUT,TENin,TENout,TUB]))
    %if ~isequal(1:n,sort([LSCC(:);DN(:);IN(:);OUT(:);TENin(:);TENout(:);TUB(:)]'))
    error('The nodes are NOT correctly selected from those available!');
end
