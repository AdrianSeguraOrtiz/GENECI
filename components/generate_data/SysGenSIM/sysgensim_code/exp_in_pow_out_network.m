function [A,restart] = exp_in_pow_out_network(n,Kd) %,Adas,r_ass,r_das

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

% Degrees vector
Kv = 1 : n;

% Define lambda
lambda = 1 / Kd;

% Find gamma
gamma = find_gamma(n,Kd);

% Calculate probabilities to have certain degrees
[~,Pin] = exponential_distribution(lambda,Kv);
[~,Pout] = power_law_distribution(gamma,Kv);

% Calculate cumulative probabilities to have certain degrees
CPin = cumsum(Pin);
CPout = cumsum(Pout);


% Network generation
restart = 1;
%count_restart = 0;
while restart == 1
    % Assignment of degrees through probability arrays
    [Kin,Kout] = degree_assignment(n,Kd,CPin,CPout);
    %count_restart = count_restart + 1;
    % Sort out-degrees in descending order
    [JK,JI] = sort(Kout,'descend');
    A = zeros(n);
    %count_any = 0;
    %count_numel = 0;
    for j = 1 : nnz(Kout)
        % Indices of nodes with positive in-degree
        I = find(Kin);
        % If the source node is between receiving nodes, then remove it
        Ir = find(I==JI(j),1);
        if ~isempty(Ir)
            I(Ir) = [];
        end
        % Random permutation of such nodes
        R = randperm(numel(I));
        % When current number of indices is smaller than out-degree of
        % node j, restart the network generation process
        %JK(j)
        %[JI(j)*ones(JK(j),1)]'
        %numel(I)
        %[I(R(1:JK(j)))]'
        
        if numel(I) < JK(j)
            restart = 1;
            %count_numel = count_numel + 1;
            %fprintf('NUMEL restarting: %d\n',count_numel);
            break
        elseif any(~(I(R(1:JK(j)))-JI(j)*ones(JK(j),1)))
            restart = 1;
            %count_any = count_any + 1;
            %I(R(1:JK(j))),JI(j)
            %fprintf('ANY restarting: %d\n',count_any);
            break
        else
            restart = 0;
            % Assign edges from node j to nodes in R
            for i = 1 : JK(j)
                A(JI(j),I(R(i))) = 1;
            end
            % Decrease the in-degree of nodes in R
            Kin = Kin - A(JI(j),:)';
        end
        %             if count_any > 0 || count_numel > 0
        %                 restart = 1;
        %                 fprintf('j = %d\n',j);
        %                 break
        %             end
    end
    %fprintf('RESTART restarting: %d\n',count_restart);
end
A = sparse(remove_diag(A));