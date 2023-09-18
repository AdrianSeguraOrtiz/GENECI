function [A,n,ng,np] = read_edge_list(path)
%
% Help for function: read_edge_list.m
%
% A = read_edge_list(path)
%
% This function reads a text file where each row indicates a regulatory
% relationship between genes.
% G16   G23     1
% means that gene 16 regulates (activates or inhibits) gene 23.
%
% The input variable is:
% - path (path of the network text file)
%
% The output variable is:
% - A (directed and signed network)

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

% Open and scan the text file
fid = fopen(path,'r');
% SysGenSIM up to 1.0.1 inserted a header line, skip it if present
first_row = textscan(fid, '%s', 1, 'Delimiter', '\r\n');
if ~strcmp(char(first_row{1}), sprintf('Gene\tTarget\tEdge'))
    frewind(fid)
end
C = textscan(fid,'%c%f %c%f %f');
fclose(fid);

% Check signs
if any(isnan(C{5})) && ~all(isnan(C{5}))
    error('You must specify all edge signs or no edge sign!')
end

% Size of gene network
IGa = C{1}=='G';
IGb = C{3}=='G';
ng = max(max(C{2}(IGa)),max(C{4}(IGb)));

% Number of phenotype nodes
IPa = find(C{1}=='P');
IPb = find(C{3}=='P');
if isempty(IPa) && isempty(IPb)
    np = 0;
elseif isempty(IPa) && ~isempty(IPb)
    np = max(C{4}(IPb));
elseif ~isempty(IPa) && isempty(IPb)
    np = max(C{2}(IPa));
elseif ~isempty(IPa) && ~isempty(IPb)
    np = max(max(C{2}(IPa)),max(C{4}(IPb)));
end

% Add ng to phenotype nodes
C{2}(IPa) = C{2}(IPa) + ng;
C{4}(IPb) = C{4}(IPb) + ng;

% Size of the gene + phenotype network
n = ng + np;

% Generate the network adjacency matrix
A = sparse(C{2},C{4},sign(C{5}),n,n);