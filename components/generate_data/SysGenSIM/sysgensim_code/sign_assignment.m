function A = sign_assignment(A,method,positive_sign_probability)

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

fprintf('Adding signs to network edges...\n');

n = length(A);

switch method

    case 'edge-wise'

        A = A.*sign(rand(n)+positive_sign_probability-1);

    case 'node-wise'

        A = A.*repmat(sign(rand(n,1)+positive_sign_probability-1),1,n);

    otherwise

        error('Sign assignment method not specified!');

end

fprintf('... Done!\n\n');