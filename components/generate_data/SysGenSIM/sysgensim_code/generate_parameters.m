function parameter = generate_parameters(distribution,parameter_size,parameter_1,parameter_2,h)

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

switch distribution
    
    case 'constant'
        parameter = parameter_1 * ones(parameter_size);
        
    case 'uniform'
        parameter = parameter_1 + ( parameter_2 - parameter_1 ) * rand(parameter_size);
    
    case 'gaussian'
%             parameter = parameter_1 + parameter_2 * randn(parameter_size);
%             parameter(parameter<0.1) = 0.1;
            parameter = truncated_randn(parameter_1,parameter_2,0.1,Inf,parameter_size);
        
    case 'gamma'
        if isempty(h)
            parameter = gamrnd(parameter_1,parameter_2,parameter_size);
        elseif h == 1
            parameter = gamrnd(parameter_1,parameter_2,parameter_size) + 1;
%         else
%             parameter = zeros(parameter_size);
%             for j = 1 : parameter_size(2)
%                 for i = 1 : parameter_size(1)
%                     while parameter(i,j) < 1
%                         parameter(i,j) = gamrnd(parameter_1,parameter_2);
%                     end
%                 end
%             end
        end
        
    case 'exponential'
        parameter = exprnd(parameter_1,parameter_size);
        
end