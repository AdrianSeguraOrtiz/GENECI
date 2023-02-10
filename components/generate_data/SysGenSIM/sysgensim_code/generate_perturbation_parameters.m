function p = generate_perturbation_parameters(p)

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
% with this program. If not, see <http://www.gnu.org/licenses/>

switch p.perturbation_type
    
    case 'no_perturbations'
        zetaA = [];
        p.m_ko = 0;
        p.m_kd = 0;
        p.m_oe = 0;
        p.R_KO = [];
        p.R_KD = [];
        p.R_OE = [];
        
    case 'knockout'
        [zetaA,p] = generate_perturbation_parameters_ko(p);
        p.m_kd = 0;
        p.m_oe = 0;
        p.R_KD = [];
        p.R_OE = [];
        
    case 'knockdown'
        [zetaA,p] = generate_perturbation_parameters_kd(p);
        p.m_ko = 0;
        p.m_oe = 0;
        p.R_KO = [];
        p.R_OE = [];
        
    case 'overexpression'
        [zetaA,p] = generate_perturbation_parameters_oe(p);
        p.m_ko = 0;
        p.m_kd = 0;
        p.R_KO = [];
        p.R_KD = [];
        
    case 'mixed'
        [zetaKO,p] = generate_perturbation_parameters_ko(p);
        [zetaKD,p] = generate_perturbation_parameters_kd(p);
        [zetaOE,p] = generate_perturbation_parameters_oe(p);
        zetaA = [zetaKO, zetaKD, zetaOE];

end

% Total number of experiments
p.m = p.m_ko + p.m_kd + p.m_oe;

% Check the number of experiments
if ~isposint(p.m)
    error('The number of single-gene perturbation experiments must be a positive integer!');
end

% No perturbations on the phenotype nodes
zetaB = ones(p.np,p.m);

% Full perturbation matrix
p.Zc = [zetaA; zetaB];
p.Zt = ones(size(p.Zc));