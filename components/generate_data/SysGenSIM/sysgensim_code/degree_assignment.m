function [Kin,Kout] = degree_assignment(n,Kd,CPin,CPout)

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

Nin = zeros(n,1);
Nout = zeros(n,1);

Kin = 1;
Kout = 2;

while ( mean(Kout) <= 0.95*Kd  || mean(Kout) >= 1.05*Kd || mean(Kout) > mean(Kin) )
    j = 1;
    Kin = 1;
    Kout = 2;
    while length(Kout) < n
        for i = 1 : n
            Nin(i) = find(CPin>=rand(1),1,'first') - 1;
            Nout(i) = find(CPout>=rand(1),1,'first') - 1;
        end
        % Identify the nodes with at least one ingoing or outgoing edge
        I = find(bitor(Nin,Nout));
        nI = numel(I);
        % Store the in- and out-degrees of such nodes
        Kin(j:(j+nI-1)) = Nin(I);
        Kout(j:(j+nI-1)) = Nout(I);
        j = j + nI;
    end
    Kin = Kin(1:n);
    Kout = Kout(1:n);
    %fprintf('Kin = %1.4f\tKout = %1.4f\tKin - Kout = %d\n',mean(Kin),mean(Kout),sum(Kin)-sum(Kout));
end

Kin = Kin';
Kout = Kout';