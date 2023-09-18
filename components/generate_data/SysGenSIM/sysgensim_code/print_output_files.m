function print_output_files(p,i,G,path)

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

fprintf('Generating output files...\n');

% Genotype matrix
if p.genotype_matrix == 1
    print_genotype_matrix(p,path.genotype_matrix);
end

% Gene expression matrix
if p.gene_expression_matrix == 1
    print_gene_expression(p,G,path.gene_expression_matrix);
end

% Phenotype matrix
if p.phenotype_matrix == 1
    print_phenotype_matrix(p,G,path.phenotype_matrix);
end

% Genetic map
if p.print_genetic_map == 1
    print_genetic_map(p,path.genetic_map);
end

% Edge list
if p.edge_list == 1
    print_edge_list(p,path.edge_list);
end

% Pajek network file
if p.pajek_network_file == 1
    print_pajek_network_file(p,path.pajek_network_file);
end

% Module list
if p.module_list == 1 && ismember_wr(p.network,{'random-modular','eipo-modular'})
    print_module_list(p,path.module_list);
end

% Topological properties
if p.topological_properties == 1
    print_topological_properties(p,path.topological_properties);
end

% Genotype information
if p.genotype_information == 1
    print_genotype_information(p,path.genotype_information);
end

% Perturbation list
if p.perturbation_list == 1
    print_perturbation_list(p,path.perturbation_list);
end

% Simulation summary
if p.simulation_summary == 1
    print_simulation_summary(p,i,path.simulation_summary);
end

fprintf('... Done!\n\n');