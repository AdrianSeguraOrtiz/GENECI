function [] = main(network_file, topology, network_size, perturbation_type, output_folder)

% Parse network size parameter to num
network_size = str2num(network_size);

% Custom parameters
if network_file
    p.user_network = network_file;
    p.network = "load_gn";
    % Required for run but not read
    p.ng = 10;
    p.modules = 3;
else
    p.user_network = "";
    p.network = topology;
    p.ng = network_size;
    p.modules = max(3, round(network_size * 0.05));
end
p.perturbation_type = perturbation_type;

% Default parameters
% 1. Simulation type
p.sg_simulation = 0;
p.gp_simulation = 1;
p.simulation = 'gp';
p.repeat = 1;

% 2. Gene Network
p.sign_assignment = "node-wise";
p.positive_sign_probability = 0.5;
p.average_degree = 8;
p.rewiring_probability = 0.1;
p.np = 5;
p.ph_in_mean = 10;
p.ph_in_std = 2;
p.ph_out_mean = 10;
p.ph_out_std = 2;

% Perturbation
p.knockout_modality = 'all';
p.knockdown_modality = 'all';
p.kd_lower_range = 0.25;
p.kd_upper_range = 0.75;
p.overexpression_modality = 'all';
p.oe_lower_range = 1.25;
p.oe_upper_range = 4;

% Model parameters
p.V_distribution = 'constant';
p.V_par1 = 1;
p.V_par2 = 0;

p.K_distribution = 'constant';
p.K_par1 = 1;
p.K_par2 = 0;

p.h_distribution = 'gamma';
p.h_par1 = 1;
p.h_par2 = 1.67;

p.lambda_distribution = 'constant';
p.lambda_par1 = 1;
p.lambda_par2 = 0;

p.synthesis_bv_distribution = 'gaussian';
p.sbv_par1 = 1;
p.sbv_par2 = 0.1;

p.degradation_bv_distribution = 'gaussian';
p.dbv_par1 = 1;
p.dbv_par2 = 0.1;

p.measurement_noise_distribution = 'gaussian';
p.mn_par1 = 1;
p.mn_par2 = 0.1;

% Output
p.edge_list = true;
p.pajek_network_file = false;
p.module_list = false;
p.topological_properties = true;
p.genotype_information = false;
p.genotype_matrix = false;
p.gene_expression_matrix = true;
p.phenotype_matrix = false;
p.print_genetic_map = false;
p.perturbation_list = false;
p.simulation_summary = false;
p.node_degree_distributions = false;
p.parameter_distributions = false;
p.heritability_distribution = false;
p.gene_expression_distribution = false;
p.correlation_distributions = false;

% Required for run
p.genotype = 'generate';
p.gene_positions = 'at_markers';
p.RILs = 'selfing';
p.mapping = 'haldane';
p.chromosomes = 1;
p.markers_per_chromosome_mean = 1;
p.markers_per_chromosome_std = 1;
p.distance_mean = 1;
p.distance_std = 1;
p.cis_effect_probability = 1;
p.genotype_error_rate = 1;
p.Zl = 1;
p.Zu = 1;
p.genetic_map = "";
p.m_sg = 1;

% Date string in the format "yyyymmdd_hhmmss"
p.date_str = date_string();

% Save the random number default stream and the internal state of its generator.
% Use getDefaultStream if using a pre-2011 version of MATLAB
if verLessThan('matlab', '7.12')
    p.RandStream = RandStream.getDefaultStream;
else
% Use getGlobalStream if using a post-2010 version of MATLAB
    p.RandStream = RandStream.getGlobalStream;
end
p.RandStream_State = get(p.RandStream,'State');

% Set directory to save the output files
p.output_dir = output_folder;

% Run SysGenSIM
sysgensim(p);

end

