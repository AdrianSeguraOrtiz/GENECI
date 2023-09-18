function print_gene_expression(p,G,path)

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

% Print first row (individuals)
fprintf(fid,'IND%d\t',1:p.m);
fprintf(fid,'\n');

% Print gene expression by gene
for i = 1 : p.ng
    fprintf(fid,'%1.7f\t',G(:,i));
    fprintf(fid,'\n');
end

% Close the output file
fclose(fid);

% Print to screen
fprintf('- Gene expression matrix saved in file "%s"!\n',path);