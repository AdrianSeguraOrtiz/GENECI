function print_module_list(p,path)

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

% Open the file to print the module list
fid = fopen(path,'wt');

% For each module
for j = 1 : numel(p.modules)
    % Take into account the size of the visited modules
    S = sum(p.modules(1:j));
    % For each node of the current module
    for i = 1 : p.modules(j)
        % Find the position of the node after the permutation
        J = find(p.R==(i+S-p.modules(j)));
        % Print the node and the module it belongs to
        fprintf(fid,'G%d\t%d\n',J,j);
    end
end

% Close the file
fclose(fid);

% Print to screen
fprintf('- Module list saved in file "%s"!\n',path);