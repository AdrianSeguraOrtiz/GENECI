function [zetaA,p] = generate_perturbation_parameters_oe(p)

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

switch p.overexpression_modality
    
    case 'all'
        p.m_oe = p.ng;
        p.R_OE = 1 : p.ng;
        OE_coef = generate_parameters('uniform',[p.m_oe,1],p.oe_lower_range,p.oe_upper_range,[]);
        zetaA = ones(p.ng,p.m_oe);
        for i = 1 : p.m_oe
            zetaA(i,i) = OE_coef(i);
        end
        
    case 'TFs'
        p.m_oe = p.n_TF;
        p.R_OE = p.TF;
        OE_coef = generate_parameters('uniform',[p.m_oe,1],p.oe_lower_range,p.oe_upper_range,[]);
        zetaA = ones(p.ng,p.m_oe);
        for i = 1 : p.m_oe
            zetaA(p.R_OE(i),i) = OE_coef(i);
        end
        
    case 'pct'
        p.m_oe = round(0.01 * p.oe_pct * p.ng);
        OE_coef = generate_parameters('uniform',[p.m_oe,1],p.oe_lower_range,p.oe_upper_range,[]);
        R_OE = randperm(p.ng);
        p.R_OE = sort(R_OE(1:p.m_oe),'ascend');
        zetaA = ones(p.ng,p.m_oe);
        for i = 1 : p.m_oe
            zetaA(p.R_OE(i),i) = OE_coef(i);
        end
        
    case 'idx'
        p.m_oe = numel(p.oe_idx);
        p.oe_idx = intersect_wr(p.oe_idx,1:p.ng);
        p.R_OE = sort(p.oe_idx,'ascend');
        OE_coef = generate_parameters('uniform',[p.m_oe,1],p.oe_lower_range,p.oe_upper_range,[]);
        zetaA = ones(p.ng,p.m_oe);
        for i = 1 : p.m_oe
            zetaA(p.R_OE(i),i) = OE_coef(i);
        end
        
end