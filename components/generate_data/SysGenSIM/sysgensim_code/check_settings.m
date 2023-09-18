function [] = check_settings(p)

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


% Gene network

% Available networks
available_networks = {'random','random-acyclic','random-modular','eipo','eipo-modular','small-world','scale-free','load_gn','load_gpn'};
if ~ismember_wr(p.network,available_networks)
    error('The network to be generated is not correctly specified!');
end

% Number of genes
if ~isposint(p.ng)
    error('The size of the network must be a positive integer!');
end
if p.ng < 10
    fprintf('Warning! The size of the network should be at least 10!\n');
end

% Number of macroscopic phenotypes
if ~isnnint(p.np)
    error('The number of macroscopic phenotypes is not correctly specified!');
end

% Sign probability
if ~isprobability(p.positive_sign_probability)
    error('The positive sign probability must be in the [0,1] interval!');
end

% Average node degree
load_networks = {'load_gn','load_gpn'};
if ~ismember_wr(p.network,load_networks)
    if isempty(p.average_degree)
        error('The average node degree must be specified!');
    elseif p.average_degree <= 0
        error('The average node degree must be positive!');
    end
end

% Modular networks
modular_networks = {'random-modular','eipo-modular'};
if ismember_wr(p.network,modular_networks)
    if isempty(p.modules)
        error('The size of network modules must be specified!');
    end
    if ~isposint(p.modules)
        error('The number or the size of network modules must be a positive integer!');
    end
    if numel(p.modules) > 1 && sum(p.modules) ~= p.ng
        error('The sum of module sizes must be equal to the size of the network!');
    end
    if numel(p.average_degree) > 1 && numel(p.modules) > 1 && numel(p.average_degree) ~= numel(p.modules)
        error('The number of elements of the average_degree array must be equal to the number of modules!');
    elseif numel(p.average_degree) > 1 && numel(p.modules) == 1 && numel(p.average_degree) ~= p.modules
        error('The number of elements of the average_degree array must be equal to the number of modules!');
    end
end

% Rewiring probability
if ismember_wr(p.network,modular_networks) || strcmp(p.network,'small-world')
    if ~isprobability(p.rewiring_probability)
        error('The re-wiring probability must be in the [0,1] interval!');
    end
end

% Custom network file
if ismember_wr(p.network,load_networks)
    if exist(p.user_network,'file') ~= 2
        error('The custom network file does not exist in the specified path!');
    end
end


% Genotype parameters

if p.sg_simulation == 1
    % Genes per chromosome and genetic distances
    if strcmp(p.genotype,'generate')
        if p.markers_per_chromosome_mean < 1
            error('The number of genes per chromosome must be larger than 1!');
        elseif p.markers_per_chromosome_std < 0
            error('The standard deviation for the genes per chromosome cannot be negative!');
        elseif p.distance_mean < 0
            error('The distance (in cM) between genes cannot be negative!');
        elseif p.distance_std < 0
            error('The standard deviation for the distance between chromosomes cannot be negative!');
        end
    end
    
    % Other parameters
    if ~isprobability(0.01*p.cis_effect_probability)
        error('The cis-effect percentage must be in the [0 100] interval!');
    elseif ~isprobability(0.01*p.genotype_error_rate)
        error('The genotype error rate must be in the [0 100] interval!');
    elseif p.Zl > p.Zu
        error('The Z lower bound cannot be larger than the Z upper bound!');
    elseif ~isprobability(p.Zl)
        error('The Z lower bound must be in the [0 1] interval!');
    elseif ~isprobability(p.Zu)
        error('The Z upper bound must be in the [0 1] interval!');
    end
    
    % Custom genetic map
    if strcmp(p.genotype,'load')
        if exist(p.input_genetic_map,'file') ~= 2
            error('The custom genetic map file does not exist in the specified path!');
        end
    end
end


% Experimental perturbations

if p.gp_simulation == 1
    
    switch p.perturbation_type
        
        case 'knockout'
            if strcmp(p.knockout_modality,'pct') && (p.ko_pct < 0) && (p.ko_pct > 100)
                error('The percentage of knocked-out genes must be in the [0 100] interval!');
            end
            
        case 'knockdown'
            if strcmp(p.knockdown_modality,'pct') && (p.kd_pct < 0) && (p.kd_pct > 100)
                error('The percentage of knocked-down genes must be in the [0 100] interval!');
            end
            if isempty(p.kd_lower_range) || isempty(p.kd_upper_range)
                error('The lower and the upper boundaries in the knockdown intensity range must be defined!');
            end
            if p.kd_lower_range < 0
                error('The lower boundary in the knockdown intensity range must be non negative!');
            elseif p.kd_upper_range > 1
                error('The upper boundary in the knockdown intensity range must be not larger than 1!');
            elseif p.kd_lower_range >= p.kd_upper_range
                error('The lower boundary in the knockdown intensity range must be smaller than the upper boundary!');
            end                
            
        case 'overexpression'
            if strcmp(p.overexpression_modality,'pct') && (p.oe_pct < 0) && (p.oe_pct > 100)
                error('The percentage of over-expressed genes must be in the [0 100] interval!');
            end
            if isempty(p.oe_lower_range) || isempty(p.oe_upper_range)
                error('The lower and the upper boundaries in the overexpression intensity range must be defined!');
            end
            if p.oe_lower_range < 1
                error('The lower boundary in the overexpression intensity range must be larger than 1!');
            elseif p.oe_lower_range >= p.oe_upper_range
                error('The lower boundary in the overexpression intensity range must be smaller than the upper boundary!');
            end
            
        case 'mixed'
            if strcmp(p.knockout_modality,'pct') && (p.ko_pct < 0) && (p.ko_pct > 100)
                error('The percentage of knocked-out genes must be in the [0 100] interval!');
            end
            if strcmp(p.knockdown_modality,'pct') && (p.kd_pct < 0) && (p.kd_pct > 100)
                error('The percentage of knocked-down genes must be in the [0 100] interval!');
            end
            if strcmp(p.overexpression_modality,'pct') && (p.oe_pct < 0) && (p.oe_pct > 100)
                error('The percentage of over-expressed genes must be in the [0 100] interval!');
            end
            if isempty(p.kd_lower_range) || isempty(p.kd_upper_range)
                error('The lower and the upper boundaries in the knockdown intensity range must be defined!');
            end
            if p.kd_lower_range < 0
                error('The lower boundary in the knockdown intensity range must be non negative!');
            elseif p.kd_upper_range > 1
                error('The upper boundary in the knockdown intensity range must be not larger than 1!');
            elseif p.kd_lower_range >= p.kd_upper_range
                error('The lower boundary in the knockdown intensity range must be smaller than the upper boundary!');
            end
            if isempty(p.oe_lower_range) || isempty(p.oe_upper_range)
                error('The lower and the upper boundaries in the overexpression intensity range must be defined!');
            end
            if p.oe_lower_range < 1
                error('The lower boundary in the overexpression intensity range must be larger than 1!');
            elseif p.oe_lower_range >= p.oe_upper_range
                error('The lower boundary in the overexpression intensity range must be smaller than the upper boundary!');
            end
            
    end
end


% Kinetic and noise parameters

available_distributions = {'constant','uniform','gamma','gaussian'};

if ~ismember_wr(p.K_distribution,available_distributions)
    error('The distribution for parameter K is not correctly specified!');
end
if ~ismember_wr(p.h_distribution,available_distributions)
    error('The distribution for parameter h is not correctly specified!');
end
if ~ismember_wr(p.V_distribution,available_distributions)
    error('The distribution for parameter V is not correctly specified!');
end
if ~ismember_wr(p.lambda_distribution,available_distributions)
    error('The distribution for parameter lambda is not correctly specified!');
end
if ~ismember_wr(p.synthesis_bv_distribution,available_distributions)
    error('The distribution for parameter theta_syn is not correctly specified!');
end
if ~ismember_wr(p.degradation_bv_distribution,available_distributions)
    error('The distribution for parameter theta_deg is not correctly specified!');
end
if ~ismember_wr(p.measurement_noise_distribution,available_distributions)
    error('The distribution for parameter measurement noise is not correctly specified!');
end


% Number of repetitions
if ~isposint(p.repeat)
    error('The number of experiment repetitions must be a positive integer!');
end
