function print_topological_properties(p,path)

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

% Find network components
[LSCC,IN,OUT,DN,TENin,TENout,TUB,~] = network_components(p.A);

% Union of in- and out-tendrils
TEN = union_wr(TENin,TENout);

% Assign a code to each group
G = zeros(1,p.n);
G(LSCC) = 1;
G(IN) = 2;
G(OUT) = 3;
G(TEN) = 4;
G(TUB) = 5;
G(DN) = 6;

% In-degree and out-degree for each node
in_degree = sum(abs(p.A),1);
out_degree = sum(abs(p.A),2);

% Find the strongly connected component for each node
[~,C] = my_conncomp(p.A);

% Open the output file
fid = fopen(path,'wt');

% Print the header
fprintf(fid,'Node\tIn-degree\tOut-degree\tGroup\tSCC\n\n');

% Print a line for each node
for i = 1 : p.n
    % Gene or phenotype node
    if i <= p.ng
        fprintf(fid,'G%d\t',i);
    else
        fprintf(fid,'P%d\t',i-p.ng);
    end
    % In-degree
    fprintf(fid,'%d\t',full(in_degree(i)));
    % Out-degree
    fprintf(fid,'%d\t',full(out_degree(i)));
    % Group
    switch G(i)
        case 1
            fprintf(fid,'LSCC\t');
        case 2
            fprintf(fid,'IN\t');
        case 3
            fprintf(fid,'OUT\t');
        case 4
            fprintf(fid,'TEN\t');
        case 5
            fprintf(fid,'TUB\t');
        case 6
            fprintf(fid,'DN\t');
        otherwise
            fprintf(fid,'ERROR\t');
    end
    % Strongly connected component
    fprintf(fid,'%d\n',C(i));    
end

% Close the output file
fclose(fid);

% Print to screen
fprintf('- Topological properties saved in file "%s"!\n',path);
