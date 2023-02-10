function plot_correlation_distributions(p,G,path1,path2,path3)

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

% Compute correlation
C = corr(G);

% Gene-gene correlation entries
Cggm = C(1:p.ng,1:p.ng);
Cgg = Cggm(triu(Cggm,1)~=0);

% Gene-gene correlation of adjacencies
Agg = uu_network(p.A(1:p.ng,1:p.ng));
Cgga = Cggm(triu(Agg,1));

% Gene-gene distributions
[Fgg,Vgg] = hist(Cgg,sqrt(numel(Cgg)));
[Fgga,Vgga] = hist(Cgga,sqrt(numel(Cgga)));
Fgg = Fgg / numel(Vgg);
Fgga = Fgga / numel(Vgga);


if p.np > 0
    % Gene-phenotype correlation entries
    Cgpm = C(:,p.ng+1:p.n);
    Cgp = Cgpm(triu(Cgpm,-p.ng+1)~=0);
    
    % Gene-phenotype correlation of adjacencies
    Agp = uu_network(p.A);
    Agp = Agp(:,p.ng+1:p.n);
    Cgpa = Cgpm(triu(Agp,-p.ng+1));
    
    % Gene-phenotype distributions
    [Fgp,Vgp] = hist(Cgp,sqrt(numel(Cgp)));
    [Fgpa,Vgpa] = hist(Cgpa,sqrt(numel(Cgpa)));
    Fgp = Fgp / numel(Vgp);
    Fgpa = Fgpa / numel(Vgpa);
end

% Plot correlation distributions
h1 = figure;

if p.np > 0
    
    % Plot gene-gene correlations
    subplot(2,1,1)
    plot(Vgg,Fgg,'b-',Vgga,Fgga,'r-')
    title('Distribution of gene-gene correlations')
    xlabel('Values')
    ylabel('Frequency')
    legend('All correlations','Adjacent correlations','Location','NE')
    
    % Plot gene-phenotype correlations
    subplot(2,1,2)
    plot(Vgp,Fgp,'b-',Vgpa,Fgpa,'r-')
    title('Distribution of gene-phenotype correlations')
    xlabel('Values')
    ylabel('Frequency')
    legend('All correlations','Adjacent correlations','Location','NE')
    
else
    
    % Plot gene-gene correlations
    plot(Vgg,Fgg,'b-',Vgga,Fgga,'r-')
    title('Distribution of gene-gene correlations')
    xlabel('Values')
    ylabel('Frequency')
    legend('All correlations','Adjacent correlations','Location','NE')
    
end


% Select correlation thresholds for co-expression networks
v = [ 0.8 0.7 0.6 0.5 ];

% Initialize cells
N = cell(1,numel(v));
K = cell(1,numel(v));
Fn = cell(1,numel(v));
Bn = cell(1,numel(v));

% Plot figure
h2 = figure;

% Iterate for each threshold
for i = 1 : numel(v)
    % Find network
    N{i} = remove_diag( abs(C(1:p.ng,1:p.ng)) > v(i) );
    % Find degree for each node
    K{i} = sum(N{i},1);
    % Frequencies of nodes with the same degree
    [Fn{i},Bn{i}] = hist(K{i},0:p.ng-1);
    % Plot degree distribution
    subplot(2,2,i)
    loglog(Bn{i},Fn{i},'b*')
    title(sprintf('Node degree distribution at t = %1.1f',v(i)))
    xlabel('Node degree')
    ylabel('Frequency')
    legend(sprintf('K = %1.2f',nnz(N{i})/p.ng),'Location','NE')
end


% Save figure of correlation distributions
saveas(h1,path1,'fig');

% Print to screen
fprintf('- Correlation distribution figure saved in file "%s"!\n',path1);

% Save figure of co-expression networks
saveas(h2,path2,'fig');

% Print to screen
fprintf('- Co-expression networks figure saved in file "%s"!\n',path2);


% Open the file to print the correlation statistics
fid = fopen(path3,'wt');

% Print statistics on gene-gene correlation values
fprintf(fid,'Some statistics on gene-gene correlation values.\n');
fprintf(fid,'Minimum: %1.4f\n',min(Cgg));
fprintf(fid,'1st quantile: %1.4f\n',quantile(Cgg,0.25));
fprintf(fid,'Mean: %1.4f\n',mean(Cgg));
fprintf(fid,'Median: %1.4f\n',median(Cgg));
fprintf(fid,'3rd quantile: %1.4f\n',quantile(Cgg,0.75));
fprintf(fid,'Maximum: %1.4f',max(Cgg));

% Close the output file
fclose(fid);

% Print to screen
fprintf('- Gene-gene correlation statistics saved in file "%s"!\n',path3);