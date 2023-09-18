function ret = truncated_randn(m,s,lb,ub,dims)
%truncated_randn Pseudorandom numbers from truncated normal distribution.
%   truncated_randn(M,S,LB,UB,DIMS) returns an array of dimensions DIMS
%   containing pseudorandom values drawn from the truncated normal
%   distribution with mean M, standard deviation S, lower bound LB and
%   upper bound UB.

% Copyright © 2010-2011 CRS4 Srl. http://www.crs4.it/
% Created by:
% Nicola Soranzo <soranzo@crs4.it>
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

if nargin < 5
    error('5 arguments required')
end
if lb > ub
    error('lb must be less than ub')
end
if lb == ub
    ret = ones(dims) * lb;
    return
end
ret = m + s * randn(dims);
idx = ret < lb | ret > ub;
while any(idx(:))
    ret(idx) = m + s * randn(nnz(idx),1);
    idx = ret < lb | ret > ub;
end