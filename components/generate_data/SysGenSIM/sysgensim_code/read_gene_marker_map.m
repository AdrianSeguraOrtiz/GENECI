function [G,D,mD,nc,Im,Ig] = read_gene_marker_map(path)

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
C = textscan(fid,'C%d %c%d %c%d %f');
fclose(fid);


% Number of distances
nd = numel(C{1});


% Number of chromosomes
nc = max(C{1});
if max(C{1}) ~= numel(unique_wr(C{1}))
    error('At least one chromosome in the genetic map is missing!');
end


% Check whether chromosomes are sorted in ascending order
if ~isequal(C{1},sort(C{1},'ascend'))
    error('Chromosomes are not sorted in ascending order!');
end


% Check whether distances are positive
for i = 1 : nd
    if C{6}(i) < 0
        error('A distance is negative in line %d!',i);
    elseif isinf(C{6}(i))
        error('A distance is infinite in line %d!',i);
    elseif isnan(C{6}(i))
        error('A distance is indefinite in line %d!',i);
    end
end


% Check whether a gene is missing or appears more than once per column
% Rows where a gene is in the first column
IG1 = find(C{2}=='G');
if numel(unique_wr(C{3}(IG1))) ~= numel(C{3}(IG1))
    error('A gene appears more than once in column 1!');
end
% Rows where a gene is in the second column
IG2 = find(C{4}=='G');
if numel(unique_wr(C{5}(IG2))) ~= numel(C{5}(IG2))
    error('A gene appears more than once in column 2!');
end
% Check whether genes are missing
if ~isempty(setdiff_wr(1:max([C{3}(IG1);C{5}(IG2)]),union_wr(C{3}(IG1),C{5}(IG2))))
    I = setdiff_wr(1:max([C{3}(IG1);C{5}(IG2)]),union_wr(C{3}(IG1),C{5}(IG2)));
    if numel(I) == 1
        error('Gene %d is missing!',I);
    else
        error('%d genes are missing!',numel(I));
    end
end


% Check whether a marker is missing or appears more than once per column
% Rows where a marker is in the first column
IM1 = find(C{2}=='M');
if numel(unique_wr(C{3}(IM1))) ~= numel(C{3}(IM1))
    error('A marker appears more than once in column 1!');
end
% Rows where a marker is in the second column
IM2 = find(C{4}=='M');
if numel(unique_wr(C{5}(IM2))) ~= numel(C{5}(IM2))
    error('A marker appears more than once in column 2!');
end
% Check whether markers are missing
if ~isempty(setdiff_wr(1:max([C{3}(IM1);C{5}(IM2)]),union_wr(C{3}(IM1),C{5}(IM2))))
    I = setdiff_wr(1:max([C{3}(IM1);C{5}(IM2)]),union_wr(C{3}(IM1),C{5}(IM2)));
    if numel(I) == 1
        error('Marker %d is missing!',I);
    else
        error('%d markers are missing!',numel(I));
    end
end


% Check whether genes and markers appears correctly in the file
cr = 1;
for i = 1 : nd
    % If i corresponds to the first position of the chromosome
    if i == find(C{1}==cr,1,'first')
        % The gene/marker in the first column must not be found in the second column
        if ismember_wr(i,IG1) && ismember_wr(C{3}(i),C{3}(IG1))
            if ismember_wr(C{3}(i),C{5}(IG2))
                error('Gene in starting position (line %d) appears elsewhere in the chromosomes!',i);
            end
        elseif ismember_wr(i,IM1) && ismember_wr(C{3}(i),C{3}(IM1))
            if ismember_wr(C{3}(i),C{5}(IM2))
                error('Marker in starting position (line %d) appears elsewhere in the chromosomes!',i);
            end
        end
    % If i corresponds to the final position of the chromosome
    elseif i == find(C{1}==cr,1,'last')
        % The gene/marker in the second column must not be found in the first column
        if ismember_wr(i,IG2) && ismember_wr(C{5}(i),C{5}(IG2))
            if ismember_wr(C{5}(i),C{3}(IG1))
                error('Gene in final position (line %d) appears elsewhere in the chromosomes!',i);
            end
        elseif ismember_wr(i,IM2) && ismember_wr(C{5}(i),C{5}(IM2))
            if ismember_wr(C{5}(i),C{3}(IM1))
                error('Marker in final position (line %d) appears elsewhere in the chromosomes!',i);
            end
        end
        % Update the chromosome
        cr = cr + 1;
    % If i corresponds to an intermediate position of the chromosome
    else
        if C{3}(i) ~= C{5}(i-1)
            error('A gene/marker in a chromosome is missing in line %d!',i);
        end
        if C{5}(i) ~= C{3}(i+1)
            error('A gene/marker in a chromosome is missing in line %d!',i);
        end
        if C{2}(i) ~= C{4}(i-1)
            error('Wrong gene/marker label in line %d!',i);
        end
    end
end


% Number of markers per chromosome
G = zeros(1,nc);
for i = 1 : nc
    % Indexes of chromosome i
    I = find(C{1}==i);
    % Indexes of markers in chromosome i
    IM1 = intersect_wr(I,find(C{2}=='M'));
    IM2 = intersect_wr(I,find(C{4}=='M'));
    % Markers in chromosome i
    Ms = union_wr(C{3}(IM1),C{5}(IM2));
    G(i) = numel(Ms);
end


% Set of distances per each chromosome
D = cell(1,nc);
for i = 1 : nc
    D{i}(1) = 0;
    D{i}(2:nnz(C{1}==i)+1) = C{6}(C{1}==i);
end


% Indexes corresponding to genes and to markers
cr = 1;
j = 1;
for i = 1 : nd
    % If i corresponds to the first position of the chromosome
    if i == find(C{1}==cr,1,'first')
        if C{2}(i) == 'M'
            I(j) = 1;
        elseif C{2}(i) == 'G'
            I(j) = 2;
        end
        if C{4}(i) == 'M'
            I(j+1) = 1;
        elseif C{4}(i) == 'G'
            I(j+1) = 2;
        end
        % Update the counter
        j = j + 2;
    % If i corresponds to the final position of the chromosome
    elseif i == find(C{1}==cr,1,'last')
        if C{4}(i) == 'M'
            I(j) = 1;
        elseif C{4}(i) == 'G'
            I(j) = 2;
        end
        % Update the counter
        j = j + 1;
        % Update the chromosome
        cr = cr + 1;
    % If i corresponds to an intermediate position of the chromosome
    else
        if C{4}(i) == 'M'
            I(j) = 1;
        elseif C{4}(i) == 'G'
            I(j) = 2;
        end
        % Update the counter
        j = j + 1;
    end
end

% Indexes corresponding to markers
Im = I==1;
% Indexes corresponding to genes
Ig = I==2;

% Calculate markers distances
mD = cell(1,nc);
nE = zeros(1,nc);
for i = 1 : nc
    % Number of markers/gene in chromosome i
    nE(i) = nnz(C{1}==i) + 1;
    % Indexes of markers in chromosome i
    fI = find(Im(sum(nE(1:i-1))+1:sum(nE(1:i))));
    % Distances between markers
    mD{i}(1) = 0;
    for j = 2 : numel(fI)
        mD{i}(j) = sum(D{i}(fI(j-1)+1:fI(j)));
    end
end
