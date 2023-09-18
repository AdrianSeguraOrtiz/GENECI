function main(expFile, outputFolder)

time_step = 50;
csv_table = importdata(expFile, ',');

% Get data and obsTimes cell arrays
data = {};
data{1} = csv_table.data;
obsTimes = {};
[~,ncols] = size(csv_table.data);
obsTimes{1} = time_step * (0:(ncols-1));

% get genes
genes = csv_table.textdata(2:end, 1);

noiseVar.obsNoise = cell(1,1);

% A dynamic noise is used for the observation noise
noiseVar.obsNoise{1} = (data{1}/10).^2;
% Replace zero values with a small number to avoid numerical errors
noiseVar.obsNoise{1}(noiseVar.obsNoise{1}==0) = 1e-6;

noiseVar.sysNoise = 1e-4;
tfidx = 1:length(genes);

[w,~,~,~,~,~,~] = ...
jump3(data,obsTimes,noiseVar,tfidx,length(tfidx),100);
nw = (w - min(w(:))) ./ (max(w(:)) - min(w(:)));

getLinkList(nw,(1:length(genes)),genes,0,strcat(outputFolder,"/GRN_JUMP3.csv"));

end
