function display_et(et)

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

if et < 0
    error('Negative elapsed time!');
end

% Years, Months, Days, Hours, Minutes, Seconds
[Y Mo D H Mi S] = datevec(datenum(0,0,0,0,0,round(et)));

% Years
if Y ~= 0
    if Y == 1
        fprintf('%d year, ',Y);
    else
        fprintf('%d years, ',Y);
    end
end

% Months
if Mo ~= 0
    if Mo == 1
        fprintf('%d month, ',Mo);
    else
        fprintf('%d months, ',Mo);
    end
elseif Y ~= 0
    fprintf('%d months, ',Mo);    
end

% Days
if D ~= 0
    if D == 1
        fprintf('%d day, ',D);
    else
        fprintf('%d days, ',D);
    end
elseif Y ~= 0 || Mo ~= 0
    fprintf('%d days, ',D);    
end

% Hours
if H ~= 0
    if H == 1
        fprintf('%d hour, ',H);
    else
        fprintf('%d hours, ',H);
    end
elseif Y ~= 0 || Mo ~= 0 || D ~= 0
    fprintf('%d hours, ',H);
end

% Minutes
if Mi ~= 0
    if Mi == 1 
        fprintf('%d minute, ',Mi);
    else
        fprintf('%d minutes, ',Mi);
    end
elseif Y ~= 0 || Mo ~= 0 || D ~= 0 || H ~= 0
    fprintf('%d minutes, ',Mi);
end

% Seconds
if S ~= 0
    if S == 1
        fprintf('%d second!',S);
    else
        fprintf('%d seconds!',S);
    end
elseif Y ~= 0 || Mo ~= 0 || D ~= 0 || H ~= 0 || Mi ~= 0
    fprintf('%d seconds!',S);
elseif S == 0
    fprintf('less than 1 second!')
end