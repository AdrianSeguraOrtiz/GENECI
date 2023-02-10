function [Zc,Zt,X,X2Z,CT,gmG,gmD] = generate_Zs(p,path)

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

[Z,X,X2Z,gmG,gmD] = generate_single_Z(p,path);


if isempty(p.cis_effect_probability)
    
    Zc = ones(p.ng,p.m);
    Zt = ones(p.ng,p.m);
    X = [];
    X2Z = [];
    CT = [];
    gmG = [];
    
elseif p.cis_effect_probability == 0
    
    Zc = ones(p.ng,p.m);
    Zt = Z;
    CT = ones(1,p.ng); % all trans-
    
elseif p.cis_effect_probability == 100
    
    Zc = Z;
    Zt = ones(p.ng,p.m);
    CT = zeros(1,p.ng); % all cis-
    
elseif p.cis_effect_probability > 0 && p.cis_effect_probability < 100
    
    % Randomly select the nodes
    R = randperm(p.ng);
    r = round(0.01*p.cis_effect_probability*p.ng);
    % Cis- genes
    Nc = R(1:r);
    % Trans- genes
    Nt = R(r+1:p.ng);
    % Cis- and trans- genes
    CT = zeros(1,p.ng);
    CT(Nt) = 1; % cis- genes are 0, trans- genes are 1
    
    % Set to 1 the Zc of the genes with trans-effect
    Zc = Z;
    Zc(Nt,:) = 1;
    % Set to 1 the Zt of the genes with cis-effect
    Zt = Z;
    Zt(Nc,:) = 1;
    % Remaining Zc and Zt maintain their original values
    
else
    
    error('The cis-effect percentage is smaller than 0 or larger than 100!')
    
end


% Add Zs for the phenotype nodes
if p.np ~= 0
    Zc = [Zc; ones(p.np,p.m)];
    Zt = [Zt; ones(p.np,p.m)];
end