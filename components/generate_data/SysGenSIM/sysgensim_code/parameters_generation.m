function p = parameters_generation(p,path)

% Copyright © 2011-2013 CRS4 Srl. http://www.crs4.it/
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

if strcmp(p.simulation,'sg')
    
    fprintf('Generating model and genetical genomics parameters...\n');
    p.m = p.m_sg;
    [p.Zc,p.Zt,p.X,p.X2Z,p.CT,p.gmG,p.gmD] = generate_Zs(p,path);
    
elseif strcmp(p.simulation,'gp')
    
    fprintf('Generating model and gene perturbation parameters...\n');
    % Gene perturbation parameters
    p = generate_perturbation_parameters(p);
    
end

% Size of variables
p.V_size = [p.n 1];
p.K_size = [p.n p.n];
p.h_size = [p.n p.n];
p.lambda_size = [p.n 1];
p.sbv_size = [p.n p.m];
p.dbv_size = [p.n p.m];
p.mn_size = [p.n p.m];

% Model parameters
p.V = generate_parameters(p.V_distribution,p.V_size,p.V_par1,p.V_par2,[]);
p.K = generate_parameters(p.K_distribution,p.K_size,p.K_par1,p.K_par2,[]);
p.K = sparse(p.K.*abs(p.A));
p.h = generate_parameters(p.h_distribution,p.h_size,p.h_par1,p.h_par2,1);
p.h = sparse(p.h.*abs(p.A));
p.lambda = generate_parameters(p.lambda_distribution,p.lambda_size,p.lambda_par1,p.lambda_par2,[]);
p.measurement_noise = generate_parameters(p.measurement_noise_distribution,p.mn_size,p.mn_par1,p.mn_par2,[]);

% Experiment parameters
p.synthesis_bv = generate_parameters(p.synthesis_bv_distribution,p.sbv_size,p.sbv_par1,p.sbv_par2,[]);
p.degradation_bv = generate_parameters(p.degradation_bv_distribution,p.dbv_size,p.dbv_par1,p.dbv_par2,[]);

fprintf('... Done!\n\n');