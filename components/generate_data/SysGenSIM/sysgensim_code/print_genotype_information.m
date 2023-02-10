function print_genotype_information(p,path)

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

% Print whether the gene is CIS or TRANS
for i = 1 : p.ng
    fprintf(fid,'G%d\t',i);
    if p.CT(i) == 0
        fprintf(fid,'CIS\t');
    elseif p.CT(i) == 1
        fprintf(fid,'TRANS\t');
    else
        fprintf(fid,'UNDEFINED\t');
    end
    fprintf(fid,'%d\n',p.X2Z(i));
end

% Close the output file
fclose(fid);

% Print to screen
fprintf('- Genotype information saved in file "%s"!\n',path);