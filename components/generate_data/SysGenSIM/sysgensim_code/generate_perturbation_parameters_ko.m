function [zetaA,p] = generate_perturbation_parameters_ko(p)

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

switch p.knockout_modality
    
    case 'all'
        p.m_ko = p.ng;
        p.R_KO = 1 : p.ng;
        zetaA = remove_diag(ones(p.ng,p.m_ko));
        
    case 'TFs'
        p.m_ko = p.n_TF;
        p.R_KO = p.TF;
        zetaA = ones(p.ng,p.m_ko);
        for i = 1 : p.n_TF
            zetaA(p.R_KO(i),i) = 0;
        end
        
    case 'pct'
        p.m_ko = round(0.01 * p.ko_pct * p.ng);
        R_KO = randperm(p.ng);
        p.R_KO = sort(R_KO(1:p.m_ko),'ascend');
        zetaA = ones(p.ng,p.m_ko);
        for i = 1 : p.m_ko
            zetaA(p.R_KO(i),i) = 0;
        end
        
    case 'idx'
        p.m_ko = numel(p.ko_idx);
        p.ko_idx = intersect_wr(p.ko_idx,1:p.ng);
        p.R_KO = sort(p.ko_idx,'ascend');
        zetaA = ones(p.ng,p.m_ko);
        for i = 1 : p.m_ko
            zetaA(p.R_KO(i),i) = 0;
        end
        
end