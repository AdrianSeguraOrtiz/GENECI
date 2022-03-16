function X = load_dream_network(file)
% this function strips-off the "G" characters from the gene identifiers

d = importdata(file);

x = d.textdata;
y = d.data;

for ii = 1:size(x,1)

	source = x{ii,1};
	target = x{ii,2};
	
	%% remove letter G
	a = strrep(source,'G','');
	b = strrep(target,'G','');

	%% remove letter g
	a = strrep(a,'g','');
	b = strrep(b,'g','');

	%% convert to number
	A = str2num(a);
	B = str2num(b);
	
	%% remember
	X(ii,:) = [ A B y(ii) ];

end

