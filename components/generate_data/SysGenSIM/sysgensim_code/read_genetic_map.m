function [G,D,nc] = read_genetic_map(n,path)

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

% Open and scan the text file
fid = fopen(path,'r');
C = textscan(fid,'C%dG%dG%d%f');
fclose(fid);

% Number of distances
nd = numel(C{1});

% Number of chromosomes
nc = n - nd;
if max(C{1}) ~= nc
    error('Chromosomes in the genetic map are not correctly specified!');
end

% Check whether genes are missing and whether distances are negative
for i = 1 : nd
    if C{3}(i) ~= C{2}(i) + 1
        error('A gene in a chromosome is missing in line %d!',i);
    end
    if C{4}(i) < 0
        error('A distance is negative in line %d!',i);
    end
end

% Check uniqueness of genes
if numel(unique_wr(C{2})) ~= numel(C{2})
    error('A gene appears more than once in column 2!');
end
if numel(unique_wr(C{3})) ~= numel(C{3})
    error('A gene appears more than once in column 3!');
end


% Number of genes per chromosome
G = zeros(1,nc);
for i = 1 : nc
    G(i) = nnz(find(C{1}==i)) + 1;
end

% Set of distances per each chromosome
D = cell(1,nc);
for i = 1 : nc
    D{i}(1) = 0;
    D{i}(2:G(i)) = C{4}(C{1}==i);
end