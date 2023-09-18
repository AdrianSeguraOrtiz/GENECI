function print_perturbation_list(p,path)

% Copyright © 2013 CRS4 Srl. http://www.crs4.it/
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

% Print header
fprintf(fid,'Experiment\tPerturbation\tGene\n');

% Print knockout experiments
for i = 1 : p.m_ko
    fprintf(fid,'%d\tKnockout\tG%d\n',i,p.R_KO(i));
end

% Print knockdown experiments
it = i;
for i = 1 : p.m_kd
    it = it + 1;
    fprintf(fid,'%d\tKnockdown\tG%d\n',it,p.R_KD(i));
end

% Print overexpression experiments
for i = 1 : p.m_oe
    it = it + 1;
    fprintf(fid,'%d\tOverexpression\tG%d\n',it,p.R_OE(i));
end

% Check
if it ~= p.m
    error('Number of printed lines different from number of individuals!');
end

% Close the output file
fclose(fid);

% Print to screen
fprintf('- Perturbation list saved in file "%s"!\n',path);