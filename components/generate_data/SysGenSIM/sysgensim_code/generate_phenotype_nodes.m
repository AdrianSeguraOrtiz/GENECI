function p = generate_phenotype_nodes(p)

% Copyright © 2011 CRS4 Srl. http://www.crs4.it/
% Created by:
% Nicola Soranzo <soranzo@crs4.it>
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

if p.np ~= 0
    
    % Add macroscopic phenotypes to the gene network
    p.n = p.ng + p.np;
    % Initialize network (add phenotype nodes)
    p.A(p.ng+1:p.n,p.ng+1:p.n) = 0;
    
    % Iterate for all phenotype nodes
    for i = 1 : p.np
        % Select the input edges to the phenotype node
        Rphin = randperm(p.ng);
        % Rphin(Rphin==p.ng+i) = [];
        Rphin = Rphin(1:round(p.ph_in_mean+p.ph_in_std*randn(1)));
        % Select the output edges from the phenotype node
        Rphout = randperm(p.ng);
        % Rphout(Rphout==p.ng+i) = [];
        Rphout = Rphout(1:round(p.ph_out_mean+p.ph_out_std*randn(1)));
        % Set the input edges to the phenotype node
        p.A(Rphin,p.ng+i) = 1;
        % Set the output edges from the phenotype node
        p.A(p.ng+i,Rphout) = 1;
    end
    
    % Indices of phenotype nodes
    p.Rph = (p.ng+1 : p.n);
    
else
    
    p.n = p.ng;
    p.Rph = [];
    
end