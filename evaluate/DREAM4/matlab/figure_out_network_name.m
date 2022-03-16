function network_name = figure_out_network_name(file, varargin)
% helper for determining what network we are working on

if nargin > 1
	parts = varargin{1};
else
	parts = 2;
end

[ temp temp2 temp3 ] = fileparts(file);
fields = lower(strsplit('_',temp2));

if parts==3
	network_name = [ fields{end-2} '_' fields{end-1} '_' fields{end} ];
else 
	network_name = [ fields{end-1} '_' fields{end} ];
end

%% uppercase first letter
network_name = [ upper(network_name(1)) network_name(2:end) ];
