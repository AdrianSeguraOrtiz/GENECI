function print_pajek_network_file(p,path)

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

% Open the output file
fid = fopen(path,'wt');

% Find row and column index of edges from the transposed adjacency matrix
[I,J] = find(p.A');

% Print vertices
fprintf(fid,'*Vertices %d\n',p.n);
% Print gene nodes
for i = 1 : p.ng
    fprintf(fid,'%d "G%d"\n',i,i);
end
% Print phenotype nodes
if p.np ~= 0
    for i = 1 : p.np
        fprintf(fid,'%d "P%d"\n',i+p.ng,i);
    end
end

% Print arcs
fprintf(fid,'*Arcs\n');
for i = 1 : numel(J)
    fprintf(fid,'%d %d %d\n',J(i),I(i),full(p.A(J(i),I(i))));
end

% Close the file
fclose(fid);

% Print to screen
fprintf('- Pajek network file saved in file "%s"!\n',path);
