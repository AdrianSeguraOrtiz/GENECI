function [p] = network_generation(p,path)
%
% Help for function: network_generation.m
%
% [A,Adu,Auu,n,m] = network_generation(s,n,p,network_path)

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

switch p.network
    case 'load_gn'
        fprintf('Loading a directed gene network...\n');
    case 'load_gpn'
        fprintf('Loading a directed gene-phenotype network...\n');
    otherwise
        fprintf('Generating a directed unsigned network...\n');
end

% Generate directed and unsigned network
switch p.network
    
    % Generate random network
    case 'random'
        A = random_network(p.ng,p.average_degree);
        
        % Generate acyclic random network
    case 'random-acyclic'
        A = acyclic_random_network(p.ng,p.average_degree);
        
        % Generate small-world network
    case 'small-world'
        A = smallworld_network(p.ng,p.average_degree,p.rewiring_probability);
        
        % Generate scale-free network
    case 'scale-free'
        A = random_in_power_out_network(p.ng,p.average_degree);
        
        % Generate exponential in- power-law out- network
    case 'eipo'
        A = exp_in_pow_out_network(p.ng,p.average_degree/2);
        
        % Generate modular exponential in- power-law out- network
    case {'random-modular','eipo-modular'}
        [A,p.modules,p.Kdm,p.perw,p.assor,p.Q] = modular_network(p.ng,p.modules,p.rewiring_probability,p.average_degree/2,p.network);
        
end

if ismember_wr(p.network,{'load_gn','load_gpn'})

    % Load custom network
    [p.A,p.n,p.ng,p.np] = read_edge_list(path.network);
    
    if strcmp(p.network,'load_gn')
        % Add phenotype nodes
        p = generate_phenotype_nodes(p);
    end
    
    fprintf('... Done!\n\n');
    
    if any(isnan(p.A))
        % Was a two-column edge list
        p.A = sign_assignment(p.A~=0,p.sign_assignment,p.positive_sign_probability);
    end
        
else
    
    % Random permutation of nodes
    p.R = randperm(p.ng);
    p.A = A(p.R,p.R);
    
    % Add phenotype nodes
    p = generate_phenotype_nodes(p);
    
    fprintf('... Done!\n\n');
    
    p.A = sign_assignment(p.A,p.sign_assignment,p.positive_sign_probability);
    
end

% Identify transcription factors (no phenotype nodes)
p.TF = find(any(p.A(1:p.ng,1:p.ng),2));
p.n_TF = numel(p.TF);