function plot_node_degree_distributions(A,path)

% Copyright © 2011 CRS4 Srl. http://www.crs4.it/
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


% Make the network unsigned
A = abs(A);

% Size of the network
n = size(A,1);

% In-, out-, total node degree distributions
Kin = sum(A,1);
Kout = sum(A,2);

% Frequency of nodes with the same degree (frequency)
[Din,Bin] = hist(Kin,0:n-1);
[Dout,Bout] = hist(Kout,0:n-1);

% Strings
s_in = sprintf('Average in-degree = %1.2f',mean(Kin+0));
s_out = sprintf('Average out-degree = %1.2f',mean(Kout+0));

% Plot of node in-/out-degree distributions
h = figure;
% In-degree
subplot(2,1,1)
semilogy(Bin,Din,'b*')
title('Log-Lin node in-degree distribution')
xlabel('In-degree')
ylabel('Frequency')
legend(s_in,'Location','NE')
% Out-degree
subplot(2,1,2)
loglog(Bout,Dout,'b*')
title('Log-Log node out-degree distribution')
xlabel('Out-degree')
ylabel('Frequency')
legend(s_out,'Location','NE')

% Save figure
saveas(h,path,'fig')

% Print to screen
fprintf('- Node degree distribution figure saved in file "%s"!\n',path);