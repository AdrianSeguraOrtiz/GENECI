function r = assortativity(A)

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

% Degrees for each node
Ki = sum(logical(A), 1)';
Ko = sum(logical(A), 2);

% Indices of nodes connected through edges
[K,J] = find(A);

% Number of edges
M = nnz(A);
% Inverse of number of edges
Mi = 1/M;

Sjk = sum( ( Ki(J) - 1 ) .* ( Ko(K) - 1 ) );
Sj = sum( Ki(J) - 1 );
Sk = sum( Ko(K) - 1 );
Sj2 = sum( ( Ki(J) - 1 ) .^2 );
Sk2 = sum( ( Ko(K) - 1 ) .^2 );

% Assortativity
r = ( Sjk - Mi * Sj * Sk ) / sqrt( ( Sj2 - Mi * Sj^2 ) * ( Sk2 - Mi * Sk^2 ) );
