function plot_gene_expression_distribution(G,path)

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

% Compute variance and mean for each gene
G_var = var(G);
G_mean = mean(G);

% Gene expression values
G_exp = G(:);

% Problem size
[m,n] = size(G);

% Compute distributions
[Fvar,Vvar] = hist(G_var,sqrt(n));
[Fmean,Vmean] = hist(G_mean,sqrt(n));
[Fgexp,Vgexp] = hist(G_exp,sqrt(m*n));

% Plot variance, mean and gene expression distributions
h = figure;
loglog(Vgexp,Fgexp,'bs',Vvar,Fvar,'rd',Vmean,Fmean,'k*')
legend('Expression values','Variances','Means','Location','Best')
title('Gene expression distributions')
xlabel('Values')
ylabel('Frequency')

% Save figure
saveas(h,path,'fig');

% Print to screen
fprintf('- Gene expression distribution figure saved in file "%s"!\n',path);