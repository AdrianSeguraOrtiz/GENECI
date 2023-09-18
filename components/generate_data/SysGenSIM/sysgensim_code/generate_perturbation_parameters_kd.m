function [zetaA,p] = generate_perturbation_parameters_kd(p)

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

switch p.knockdown_modality
    
    case 'all'
        p.m_kd = p.ng;
        p.R_KD = 1 : p.ng;
        KD_coef = generate_parameters('uniform',[p.m_kd,1],p.kd_lower_range,p.kd_upper_range,[]);
        zetaA = ones(p.ng,p.m_kd);
        for i = 1 : p.m_kd
            zetaA(i,i) = KD_coef(i);
        end
        
    case 'TFs'
        p.m_kd = p.n_TF;
        p.R_KD = p.TF;
        KD_coef = generate_parameters('uniform',[p.m_kd,1],p.kd_lower_range,p.kd_upper_range,[]);
        zetaA = ones(p.ng,p.m_kd);
        for i = 1 : p.m_kd
            zetaA(p.R_KD(i),i) = KD_coef(i);
        end
        
    case 'pct'
        p.m_kd = round(0.01 * p.kd_pct * p.ng);
        KD_coef = generate_parameters('uniform',[p.m_kd,1],p.kd_lower_range,p.kd_upper_range,[]);
        R_KD = randperm(p.ng);
        p.R_KD = sort(R_KD(1:p.m_kd),'ascend');
        zetaA = ones(p.ng,p.m_kd);
        for i = 1 : p.m_kd
            zetaA(p.R_KD(i),i) = KD_coef(i);
        end
        
    case 'idx'
        p.m_kd = numel(p.kd_idx);
        p.kd_idx = intersect_wr(p.kd_idx,1:p.ng);
        p.R_KD = sort(p.kd_idx,'ascend');
        KD_coef = generate_parameters('uniform',[p.m_kd,1],p.kd_lower_range,p.kd_upper_range,[]);
        zetaA = ones(p.ng,p.m_kd);
        for i = 1 : p.m_kd
            zetaA(p.R_KD(i),i) = KD_coef(i);
        end
        
end