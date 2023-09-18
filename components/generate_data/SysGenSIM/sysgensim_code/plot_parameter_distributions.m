function plot_parameter_distributions(p,path)

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

[~,~,p.K] = find(p.K);
[~,~,p.h] = find(p.h);

h = figure;

subplot(2,3,1)
hist(p.V(:),sqrt(size(p.V,1)*size(p.V,2)))
xlabel('Basal transcription rate')
ylabel('Frequency')

subplot(2,3,2)
hist(p.K,sqrt(size(p.K,1)*size(p.K,2)))
xlabel('Interaction strength')
ylabel('Frequency')

subplot(2,3,3)
hist(p.h(:),sqrt(size(p.h,1)*size(p.h,2)))
xlabel('Cooperativity coefficient')
ylabel('Frequency')

subplot(2,3,4)
hist(p.lambda(:),sqrt(size(p.lambda,1)*size(p.lambda,2)))
xlabel('Basal degradation rate')
ylabel('Frequency')

subplot(2,3,5)
hist(p.synthesis_bv(:),sqrt(size(p.synthesis_bv,1)*size(p.synthesis_bv,2)))
xlabel('Variance in synthesis')
ylabel('Frequency')

subplot(2,3,6)
hist(p.degradation_bv(:),sqrt(size(p.degradation_bv,1)*size(p.degradation_bv,2)))
xlabel('Variance in degradation')
ylabel('Frequency')


% Save figure
saveas(h,path,'fig');

% Print to screen
fprintf('- Parameter distribution figure saved in file "%s"!\n',path);