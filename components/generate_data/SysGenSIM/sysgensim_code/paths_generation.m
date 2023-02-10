function [path] = paths_generation(p,i)

% Copyright © 2011-2013 CRS4 Srl. http://www.crs4.it/
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

fprintf('Generating simulation paths...\n');

% Simulation repeat
i_string = num2str(i);

% Path to save the output in a Matlab file
path.matlab = [p.output_dir filesep 'Sim_' p.date_str '_Exp_' i_string '.mat'];

% Path of custom user network
load_networks = {'load_gn','load_gpn'};
if ismember_wr(p.network,load_networks)
    path.network = p.user_network;
else
    path.network = '';
end

% Path of custom genetic map
if strcmp(p.genotype,'load_m-map') || strcmp(p.genotype,'load_mg-map')
    path.input_genetic_map = p.genetic_map;
else
    path.input_genetic_map = '';
end

% Path to print the genotype matrix
path.genotype_matrix = [p.output_dir filesep 'Sim_' p.date_str '_Exp_' i_string '_genotype_matrix.tsv'];

% Path to print the gene expression matrix
path.gene_expression_matrix = [p.output_dir filesep 'Sim_' p.date_str '_Exp_' i_string '_gene_expression_matrix.tsv'];

% Path to print the phenotype matrix
path.phenotype_matrix = [p.output_dir filesep 'Sim_' p.date_str '_Exp_' i_string '_phenotype_matrix.tsv'];

% Path to print the genetic map
path.genetic_map = [p.output_dir filesep 'Sim_' p.date_str '_Exp_' i_string '_genetic_map.tsv'];

% Path to print the edge list
path.edge_list = [p.output_dir filesep 'Sim_' p.date_str '_Exp_' i_string '_edge_list.tsv'];

% Path to print the Pajek network file
path.pajek_network_file = [p.output_dir filesep 'Sim_' p.date_str '_Exp_' i_string '_Pajek_network_file.net'];

% Path to print the module list
path.module_list = [p.output_dir filesep 'Sim_' p.date_str '_Exp_' i_string '_module_list.tsv'];

% Path to print the topological properties
path.topological_properties = [p.output_dir filesep 'Sim_' p.date_str '_Exp_' i_string '_topological_properties.tsv'];

% Path to print the genotype information
path.genotype_information = [p.output_dir filesep 'Sim_' p.date_str '_Exp_' i_string '_genotype_information.tsv'];

% Path to print the perturbation list
path.perturbation_list = [p.output_dir filesep 'Sim_' p.date_str '_Exp_' i_string '_perturbation_list.tsv'];

% Path to print the simulation summary
path.simulation_summary = [p.output_dir filesep 'Sim_' p.date_str '_Exp_' i_string '_simulation_summary.txt'];

% Path to print the correlation statistics
path.correlation_statistics = [p.output_dir filesep 'Sim_' p.date_str '_Exp_' i_string '_correlation_statistics.txt'];

% Path to plot the node degree distributions
path.node_degree_distributions = [p.output_dir filesep 'Sim_' p.date_str '_Exp_' i_string '_node_degree_distributions.fig'];

% Path to plot the parameter distributions
path.parameter_distributions = [p.output_dir filesep 'Sim_' p.date_str '_Exp_' i_string '_parameter_distributions.fig'];

% Path to plot the heritability distribution
path.heritability_distribution = [p.output_dir filesep 'Sim_' p.date_str '_Exp_' i_string '_heritability_distribution.fig'];

% Path to plot the gene expression distribution
path.gene_expression_distribution = [p.output_dir filesep 'Sim_' p.date_str '_Exp_' i_string '_gene_expression_distribution.fig'];

% Path to plot the correlation distributions
path.correlation_distributions = [p.output_dir filesep 'Sim_' p.date_str '_Exp_' i_string '_correlation_distributions.fig'];

% Path to plot the degree distributions of co-expression networks
path.coexpression_networks = [p.output_dir filesep 'Sim_' p.date_str '_Exp_' i_string '_coexpression_networks.fig'];

fprintf('... Done!\n\n');