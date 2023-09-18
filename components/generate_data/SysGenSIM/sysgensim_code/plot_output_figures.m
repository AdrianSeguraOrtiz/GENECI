function plot_output_figures(p,path,G,Gh)

% Copyright © 2011 CRS4 Srl. http://www.crs4.it/
% Created by:
% Nicola Soranzo <soranzo@crs4.it>
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


fprintf('Generating output figures...\n');

if p.node_degree_distributions == 1
    plot_node_degree_distributions(p.A,path.node_degree_distributions);
end

if p.parameter_distributions == 1
    plot_parameter_distributions(p,path.parameter_distributions);
end

if p.gene_expression_distribution == 1
    plot_gene_expression_distribution(G(:,1:p.ng),path.gene_expression_distribution);
end

if p.heritability_distribution == 1
    plot_heritability_distribution(G(:,1:p.ng),Gh(:,1:p.ng),path.heritability_distribution);
end

if p.correlation_distributions == 1
    plot_correlation_distributions(p,G,path.correlation_distributions,path.coexpression_networks,path.correlation_statistics);
end

fprintf('... Done!\n\n');
