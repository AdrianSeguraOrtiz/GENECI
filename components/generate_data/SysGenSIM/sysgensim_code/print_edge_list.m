function print_edge_list(p,path)

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

% Open the file to print the edge list
fid = fopen(path,'wt');

% Find row and column index of edges from the transposed adjacency matrix
[I,J] = find(p.A');

for i = 1 : numel(J)
    if J(i) <= p.ng && I(i) <= p.ng
        fprintf(fid,'G%d\tG%d\t%d\n',J(i),I(i),full(p.A(J(i),I(i))));
    elseif J(i) > p.ng && I(i) <= p.ng
        fprintf(fid,'P%d\tG%d\t%d\n',J(i)-p.ng,I(i),full(p.A(J(i),I(i))));
    elseif J(i) <= p.ng && I(i) > p.ng
        fprintf(fid,'G%d\tP%d\t%d\n',J(i),I(i)-p.ng,full(p.A(J(i),I(i))));
    else
        fprintf(fid,'P%d\tP%d\t%d\n',J(i)-p.ng,I(i)-p.ng,full(p.A(J(i),I(i))));
    end
end

% Close the file
fclose(fid);

% Print to screen
fprintf('- Edge list saved in file "%s"!\n',path);
