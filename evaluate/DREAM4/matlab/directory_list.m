function filenames = directory_list(varargin)
%% filenames = directory_list('.','README.txt')

%% set location
if nargin < 1
	there = '.'
else
	there = varargin{1};
end

filenames = {};
directory = dir(there);
j = 1;
for i = 1:size(directory,1)
	entry = directory(i).name;
	if isempty(regexp(entry, '^\.'))
		%% the first char is not a dot "."
  		filenames{j} = entry;
  		j = j+1;
	end
end

%% ignore some files
if nargin > 1
	ignore_list = varargin{2};

	%% strip the files that we want to ignore
	idx = 1:length(filenames);
	ignoreme = [];
	for i = 1:length(ignore_list)
		ignoreme = [ ignoreme strmatch(ignore_list{i},filenames) ];
	end
	keepers = setdiff(idx,ignoreme);
	filenames = filenames(keepers);
end	
	