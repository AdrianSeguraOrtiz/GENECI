function print_simulation_summary(p,i,path)

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

% Open the output file
fid = fopen(path,'wt');

% Experiment settings
fprintf(fid,'EXPERIMENT SETTINGS\n');
fprintf(fid,'Replicate of the experiment: %d of %d\n',i,p.repeat);
if strcmp(p.simulation,'sg')
    fprintf(fid,'Type of experiment: systems genetics\n');
    fprintf(fid,'Population size: %d\n',p.m);
elseif strcmp(p.simulation,'gp')
    fprintf(fid,'Type of experiment: gene perturbations\n');
    fprintf(fid,'Single-gene knockouts: %d\n',p.m_ko);
    fprintf(fid,'Single-gene knockdowns: %d\n',p.m_kd);
    fprintf(fid,'Single-gene overexpressions: %d\n',p.m_oe);
    fprintf(fid,'Total single-gene perturbations: %d\n',p.m);
end


% Gene network parameters
fprintf(fid,'\nGENE NETWORK PARAMETERS\n');
fprintf(fid,'Network: %s\n',p.network);
unimodular_networks = {'random','random-acyclic','eipo','small-world','scale-free'};
modular_networks = {'random-modular','eipo-modular'};
fprintf(fid,'Size of the gene network: %d genes\n',p.ng);
fprintf(fid,'Sign assignment: %s\n',p.sign_assignment);
if ismember_wr(p.network,unimodular_networks) || ...
        ismember_wr(p.network,modular_networks) && numel(p.average_degree) == 1
    fprintf(fid,'Desired node average degree: %1.2f\n',p.average_degree);
elseif ismember_wr(p.network,modular_networks) && numel(p.average_degree) > 1
    fprintf(fid,'Desired node average modular degree:');
    for i = 1 : numel(p.average_degree)
        fprintf(fid,' %1.2f',p.average_degree(i));
    end
    fprintf(fid,'\n');
else
    fprintf(fid,'Desired node average degree: value(s) not specified\n');
end
if ismember_wr(p.network,modular_networks)
    fprintf(fid,'Number of modules: %d\n',numel(p.modules));
    fprintf(fid,'Size of modules:');
    for i = 1 : numel(p.modules)
        fprintf(fid,' %d',p.modules(i));
    end
    fprintf(fid,'\n');
end
if ismember_wr(p.network,modular_networks) || strcmp(p.network,'small-world')
    fprintf(fid,'Re-wiring probability: %1.2f\n',p.rewiring_probability);
end
if strcmp(p.network,'load_gn')
    fprintf(fid,'Gene network loaded from path: ''%s''\n',p.user_network);
end
if strcmp(p.network,'load_gpn')
    fprintf(fid,'Gene-phenotype network loaded from path: ''%s''\n',p.user_network);
end

% Phenotype parameters
fprintf(fid,'\nPHENOTYPE PARAMETERS\n');
if ~strcmp(p.network,'load_gpn')
    fprintf(fid,'Number of phenotype nodes: %d\n',p.np);
    if p.np > 0
        fprintf(fid,'Direct causal genes per phenotype node: mean = %1.2f, stdev = %1.2f\n',p.ph_in_mean,p.ph_in_std);
        fprintf(fid,'Direct reactive genes per phenotype node: mean = %1.2f, stdev = %1.2f\n',p.ph_out_mean,p.ph_out_std);
    end
else
    fprintf(fid,'Phenotype nodes loaded from path: ''%s''\n',p.user_network);
end

% Genotype parameters
if strcmp(p.simulation,'sg')
    fprintf(fid,'\nGENOTYPE PARAMETERS\n');
    if strcmp(p.genotype,'generate')
        fprintf(fid,'Marker positions: %s\n',p.genotype);
        fprintf(fid,'Number of chromosomes: %d\n',p.chromosomes);
        fprintf(fid,'Number of markers per chromosome: mean = %1.2f, stdev = %1.2f\n',p.markers_per_chromosome_mean,p.markers_per_chromosome_std);
        fprintf(fid,'Distances (cM): mean = %1.2f, stdev = %1.2f\n',p.distance_mean,p.distance_std);
    else
        fprintf(fid,'Marker positions loaded from path: ''%s''\n',p.genetic_map);
    end
    fprintf(fid,'Gene positions: %s\n',p.gene_positions);
    fprintf(fid,'Mapping function: %s\n',p.mapping);
    fprintf(fid,'RIL type: %s\n',p.RILs);
    fprintf(fid,'Cis-effect percentage: %1.2f%%\n',p.cis_effect_probability);
    fprintf(fid,'Genotyping error rate: %1.2f%%\n',p.genotype_error_rate);
    fprintf(fid,'Z values: sampled from the [%1.2f, %1.2f] interval\n',p.Zl,p.Zu);
    
% Experimental perturbations    
elseif strcmp(p.simulation,'gp')
    fprintf(fid,'\nGENE PERTURBATION PARAMETERS\n');
    if strcmp(p.perturbation_type,'knockout')
        fprintf(fid,'Perturbation type: knockout\n');
        switch p.knockout_modality
            case 'all',    fprintf(fid,'Knockout modality: all genes\n');
            case 'TFs',    fprintf(fid,'Knockout modality: only TFs\n');
            case 'pct',    fprintf(fid,'Knockout modality: percentage (%1.2f\%)\n',p.ko_pct);
            case 'idx',    fprintf(fid,'Knockout modality: indexes (%d genes)\n',numel(p.ko_idx));
        end
    elseif strcmp(p.perturbation_type,'knockdown')
        fprintf(fid,'Perturbation type: knockdown\n');
        switch p.knockdown_modality
            case 'all',    fprintf(fid,'Knockdown modality: all genes\n');
            case 'TFs',    fprintf(fid,'Knockdown modality: only TFs\n');
            case 'pct',    fprintf(fid,'Knockdown modality: percentage (%1.2f\%)\n',p.kd_pct);
            case 'idx',    fprintf(fid,'Knockdown modality: indexes (%d genes)\n',numel(p.kd_idx));
        end
        fprintf('Knockdown perturbation range: [%1.2f, %1.2f]\n',p.kd_lower_range,p.kd_upper_range);
    elseif strcmp(p.perturbation_type,'overexpression')
        fprintf(fid,'Perturbation type: overexpression\n');
        switch p.overexpression_modality
            case 'all',    fprintf(fid,'Overexpression modality: all genes\n');
            case 'TFs',    fprintf(fid,'Overexpression modality: only TFs\n');
            case 'pct',    fprintf(fid,'Overexpression modality: percentage (%1.2f\%)\n',p.oe_pct);
            case 'idx',    fprintf(fid,'Overexpression modality: indexes (%d genes)\n',numel(p.oe_idx));
        end
        fprintf('Overexpression perturbation range: [%1.2f, %1.2f]\n',p.oe_lower_range,p.oe_upper_range);
    elseif strcmp(p.perturbation_type,'mixed')
        fprintf(fid,'Perturbation type: mixed\n');
        switch p.knockout_modality
            case 'all',    fprintf(fid,'Knockout modality: all genes\n');
            case 'TFs',    fprintf(fid,'Knockout modality: only TFs\n');
            case 'pct',    fprintf(fid,'Knockout modality: percentage (%1.2f\%)\n',p.ko_pct);
            case 'idx',    fprintf(fid,'Knockout modality: indexes (%d genes)\n',numel(p.ko_idx));
        end
        switch p.knockdown_modality
            case 'all',    fprintf(fid,'Knockdown modality: all genes\n');
            case 'TFs',    fprintf(fid,'Knockdown modality: only TFs\n');
            case 'pct',    fprintf(fid,'Knockdown modality: percentage (%1.2f%%)\n',p.kd_pct);
            case 'idx',    fprintf(fid,'Knockdown modality: indexes (%d genes)\n',numel(p.kd_idx));
        end
        fprintf(fid,'Knockdown perturbation range: [%1.2f, %1.2f]\n',p.kd_lower_range,p.kd_upper_range);
        switch p.overexpression_modality
            case 'all',    fprintf(fid,'Overexpression modality: all genes\n');
            case 'TFs',    fprintf(fid,'Overexpression modality: only TFs\n');
            case 'pct',    fprintf(fid,'Overexpression modality: percentage (%1.2f%%)\n',p.oe_pct);
            case 'idx',    fprintf(fid,'Overexpression modality: indexes (%d genes)\n',numel(p.oe_idx));
        end
        fprintf(fid,'Overexpression perturbation range: [%1.2f, %1.2f]\n',p.oe_lower_range,p.oe_upper_range);
    end

    
end

% Model parameters
fprintf(fid,'\nKINETIC and NOISE PARAMETERS\n');
fprintf(fid,'Basal transcription rate: %s (P1 = %1.4f, P2 = %1.4f)\n',p.V_distribution,p.V_par1,p.V_par2);
fprintf(fid,'Interaction strength: %s (P1 = %1.4f, P2 = %1.4f)\n',p.K_distribution,p.K_par1,p.K_par2);
fprintf(fid,'Cooperativity coefficient: %s (P1 = %1.4f, P2 = %1.4f)\n',p.h_distribution,p.h_par1,p.h_par2);
fprintf(fid,'Degradation rate: %s (P1 = %1.4f, P2 = %1.4f)\n',p.lambda_distribution,p.lambda_par1,p.lambda_par2);
fprintf(fid,'Biological variance in transcription: %s (P1 = %1.4f, P2 = %1.4f)\n',p.synthesis_bv_distribution,p.sbv_par1,p.sbv_par2);
fprintf(fid,'Biological variance in degradation: %s (P1 = %1.4f, P2 = %1.4f)\n',p.degradation_bv_distribution,p.dbv_par1,p.dbv_par2);
fprintf(fid,'Measurement noise: %s (P1 = %1.4f, P2 = %1.4f)\n',p.measurement_noise_distribution,p.mn_par1,p.mn_par2);

% Output files
fprintf(fid,'\nOUTPUT FILES\n');
fprintf(fid,'Genotype matrix: ');
if p.genotype_matrix == 1, fprintf(fid,'YES\n'); else fprintf(fid,'NO\n'); end
fprintf(fid,'Gene expression matrix: ');
if p.gene_expression_matrix == 1, fprintf(fid,'YES\n'); else fprintf(fid,'NO\n'); end
fprintf(fid,'Phenotype matrix: ');
if p.phenotype_matrix == 1, fprintf(fid,'YES\n'); else fprintf(fid,'NO\n'); end
fprintf(fid,'Genetic map: ');
if p.print_genetic_map == 1, fprintf(fid,'YES\n'); else fprintf(fid,'NO\n'); end
fprintf(fid,'Edge list: ');
if p.edge_list == 1, fprintf(fid,'YES\n'); else fprintf(fid,'NO\n'); end
fprintf(fid,'Pajek network file: ');
if p.pajek_network_file == 1, fprintf(fid,'YES\n'); else fprintf(fid,'NO\n'); end
fprintf(fid,'Module list: ');
if p.module_list == 1, fprintf(fid,'YES\n'); else fprintf(fid,'NO\n'); end
fprintf(fid,'Topological properties: ');
if p.topological_properties == 1, fprintf(fid,'YES\n'); else fprintf(fid,'NO\n'); end
fprintf(fid,'Genotype information: ');
if p.genotype_information == 1, fprintf(fid,'YES\n'); else fprintf(fid,'NO\n'); end
fprintf(fid,'Perturbation list: ');
if p.perturbation_list == 1, fprintf(fid,'YES\n'); else fprintf(fid,'NO\n'); end
fprintf(fid,'Simulation summary: ');
if p.simulation_summary == 1, fprintf(fid,'YES\n'); else fprintf(fid,'NO\n'); end

% Output figures
fprintf(fid,'\nOUTPUT FIGURES\n');
fprintf(fid,'Node degree distributions: ');
if p.node_degree_distributions == 1, fprintf(fid,'YES\n'); else fprintf(fid,'NO\n'); end
fprintf(fid,'Parameter distributions: ');
if p.parameter_distributions == 1, fprintf(fid,'YES\n'); else fprintf(fid,'NO\n'); end
fprintf(fid,'Gene expression distribution: ');
if p.gene_expression_distribution == 1, fprintf(fid,'YES\n'); else fprintf(fid,'NO\n'); end
fprintf(fid,'Heritability distribution: ');
if p.heritability_distribution == 1, fprintf(fid,'YES\n'); else fprintf(fid,'NO\n'); end
fprintf(fid,'Gene correlation distributions: ');
if p.correlation_distributions == 1, fprintf(fid,'YES\n'); else fprintf(fid,'NO\n'); end

% Close the output file
fclose(fid);

% Print to screen
fprintf('- Simulation summary saved in file "%s"!\n',path);