function [Z,X,X2Z,G,mD] = generate_single_Z(p,path)
%
% Help for function: generate_Zs.m
%

% Copyright © 2011 CRS4 Srl. http://www.crs4.it/
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

% Build genetic map
if strcmp(p.genotype,'load_m-map')
    % Check and load genetic map (markers only)
    [G,mD,p.chromosomes] = read_genetic_map(p.ng,path.input_genetic_map);
elseif strcmp(p.genotype,'generate')
    % Generate chromosome sizes
    G = zeros(1,p.chromosomes);
    while any(G<=0)
        G(1:p.chromosomes-1) = round(p.markers_per_chromosome_mean + p.markers_per_chromosome_std * randn(1,p.chromosomes-1));
        G(p.chromosomes) = round(p.markers_per_chromosome_mean * p.chromosomes) - sum(G(1:p.chromosomes-1));
    end
    % Generate markers distances
    mD = cell(1,p.chromosomes);
    for i = 1 : p.chromosomes
        mD{i} = p.distance_mean + p.distance_std * randn([1 G(i)]);
        mD{i}(1) = 0;
    end
end


% Gene positions
if strcmp(p.genotype,'load_mg-map')
    [G,D,mD,p.chromosomes,Im,Ig] = read_gene_marker_map(p.genetic_map);
elseif strcmp(p.gene_positions,'at_markers')
    D = mD;
elseif strcmp(p.gene_positions,'unif_distr')
    CrL = zeros(1,p.chromosomes);
    SlCr = zeros(1,p.chromosomes);
    for i = 1 : p.chromosomes
        % Length of chromosomes (in cM)
        CrL(i) = sum(mD{i});
        % Slots of 0.1 cM for each chromosome
        SlCr(i) = ceil(CrL(i)*10-1);
    end
    % Total number of available slots
    sSlCr = sum(SlCr);
    % Randomly permute available slots
    Rs = randperm(sSlCr);
    % Select slots to be assigned to genes
    Rs = sort(Rs(1:p.ng),'ascend');
    % Assign to each gene and marker their absolute position
    Map = cell(1,p.chromosomes);
    Gap = cell(1,p.chromosomes);
    for i = 1 : p.chromosomes
        Map{i} = cumsum(mD{i});
        Gap{i} = 0.1*(Rs(Rs>sum(SlCr(1:i-1)) & Rs<=sum(SlCr(1:i)))-sum(SlCr(1:i-1)));
    end
    % Sort markers and genes for each chromosome
    MGap = cell(1,p.chromosomes);
    Iap = cell(1,p.chromosomes);
    for i = 1 : p.chromosomes
        MGap{i} = [Map{i},Gap{i}];
        Iap{i} = [ones(1,numel(Map{i})),2*ones(1,numel(Gap{i}))];
        [MGap{i},I] = sort(MGap{i},'ascend');
        Iap{i} = Iap{i}(I);
    end
    % Find indices corresponding to markers and to genes
    if strcmp(p.gene_positions,'unif_distr')
        I = [];
        for i = 1 : p.chromosomes
            I = [I, Iap{i}];
        end
        Im = I==1;
        Ig = I==2;
    end
    % Generate markers and genes distances
    D = cell(1,p.chromosomes);
    for i = 1 : p.chromosomes
        D{i}(1) = 0;
        D{i}(2:numel(MGap{i})) = MGap{i}(2:numel(MGap{i})) - MGap{i}(1:numel(MGap{i})-1);
    end
end


% Mapping function
R = cell(1,p.chromosomes);
if strcmp(p.mapping,'haldane')
    for i = 1 : p.chromosomes
        R{i} = 0.5 * ( 1 - exp( -2 * 0.01 * D{i} ) );
    end
elseif strcmp(p.mapping,'kosambi')
    for i = 1 : p.chromosomes
        R{i} = 0.5 * ( exp( 4 * 0.01 * D{i} ) - 1 ) ./ ( exp( 4 * 0.01 * D{i} ) + 1 );
    end
else
    error('Mapping function not correctly specified!');
end


% Probabilities
P = cell(1,p.chromosomes);
if strcmp(p.RILs,'selfing')
    for i = 1 : p.chromosomes
        P{i} = 1 ./ ( 1 + 2 * R{i} );
    end
elseif strcmp(p.RILs,'sibling')
    for i = 1 : p.chromosomes
        P{i} = ( 1 + 2 * R{i} ) ./ ( 1 + 6 * R{i} );
    end
else
    error('RILs type not correctly specified!');
end


% Generate genotype
if ~strcmp(p.genotype,'load_mg-map') && strcmp(p.gene_positions,'at_markers')
    X = zeros(p.ng,p.m);
elseif strcmp(p.gene_positions,'unif_distr') || strcmp(p.genotype,'load_mg-map')
    X = zeros(p.ng+sum(G),p.m);
end
for i = 1 : p.m
    X(1,i) = round(rand(1));
    for k = 2 : G(1)
        X(k,i) = round( ( 2 * X(k-1,i) - 1 ) * (P{1}(k) - 0.5) + rand(1) );
    end
    for j = 2 : p.chromosomes
        Gc = sum(G(1:j-1));
        X(Gc+1,i) = round(rand(1));
        for k = 2 : G(j)
            X(Gc+k,i) = round( ( 2 * X(Gc+k-1,i) - 1 ) * (P{j}(k) - 0.5) + rand(1) );
        end
    end
end


% Conversion vector (from X to Z)
X2Z = random('bino',1,0.5,[p.ng,1]);


% Generation of Z values
Z = zeros(p.ng,p.m);
if ~strcmp(p.genotype,'load_mg-map') && strcmp(p.gene_positions,'at_markers')
    Xz = X;
elseif strcmp(p.gene_positions,'unif_distr') || strcmp(p.genotype,'load_mg-map')
    Xz = X(Ig,:);
    % Update X by removing gene-related rows
    X = X(Im,:);
end
for i = 1 : p.m
    for j = 1 : p.ng
        if Xz(j,i) == X2Z(j)
            Z(j,i) = 1;
        else
            Z(j,i) = p.Zl + ( p.Zu - p.Zl ) * rand(1);
        end
    end
end


% Add genotype measurement noise to X
n_flips = round(0.01*p.genotype_error_rate*numel(X));
RX = randperm(numel(X));
X_flips = RX(1:n_flips);
[I,J] = ind2sub(size(X),X_flips);
for i = 1 : numel(I)
    X(I(i),J(i)) = ~X(I(i),J(i));
end