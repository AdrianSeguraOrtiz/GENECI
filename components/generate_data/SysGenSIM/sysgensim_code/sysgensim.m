function sysgensim(p)
% SysGenSIM main script

% Copyright © 2011-2012 CRS4 Srl. http://www.crs4.it/
% Created by:
% Andrea Pinna <andrea.pinna@crs4.it>
% Nicola Soranzo <soranzo@crs4.it>
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

fprintf('Checking parameters...\n');
% Check settings and parameters
check_settings(p);
fprintf('Parameters OK!\n');
% Check whether directory for output files exists
if exist(p.output_dir,'dir') ~= 7
    mkdir(p.output_dir);
end

% Save settings and parameters
save([p.output_dir filesep 'p_' p.date_str '.mat'],'p')

for i = 1 : p.repeat
    
    fprintf('\nPerforming experiment %d of %d...\n\n',i,p.repeat);
    
    % Generate paths
    path = paths_generation(p,i);
    
    % Generate network
    p = network_generation(p,path);
    
    % Generate parameters
    p = parameters_generation(p,path);
    
    % Simulate gene expression steady states
    [G,~,~,Gh] = steady_states_computation(p.n,p.m,p.A,p.Zc,p.Zt,p.V,...
        p.K,p.h,p.lambda,p.synthesis_bv,p.degradation_bv,...
        p.measurement_noise,p.heritability_distribution);
    
    % Print output files
    print_output_files(p,i,G,path);
    
    % Plot output figures
    plot_output_figures(p,path,G,Gh);
    
    % Save variables
    save(path.matlab);
    
    fprintf('... Experiment %d of %d performed!\n\n',i,p.repeat);
    
end