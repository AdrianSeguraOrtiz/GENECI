function [gamma] = find_gamma(n, avg_outdegree,precision)

% Copyright © 2011 CRS4 Srl. http://www.crs4.it/
% Created by:
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

if nargin == 2
    precision = 0.001;
end
nodes = 1:n;
diff = Inf;
new_gamma = 0;
new_diff = abs(avg_outdegree - power_law_distribution(new_gamma,nodes));
while new_diff < diff
    gamma = new_gamma;
    diff = new_diff;
    new_gamma = gamma + precision;
    new_diff = abs(avg_outdegree - power_law_distribution(new_gamma,nodes));
end