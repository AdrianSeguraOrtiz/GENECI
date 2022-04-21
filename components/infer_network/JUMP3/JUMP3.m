path(path,'jump3_code')

input_file = '../../../input_data/DREAM4/EXP/dream4_010_01_exp.csv';
time_series_ids = ["perturbation.1", "perturbation.2", "perturbation.3", "perturbation.4"];
time_step = 50;

csv_table = importdata(input_file);

% Get data and obsTimes cell arrays
header = csv_table.textdata(1, 2:end);
data = {};
obsTimes = {};
for i = 1:length(time_series_ids)
    index = find(contains(header, time_series_ids(i)));
    data{i} = csv_table.data(:, index);
    obsTimes{i} = time_step * (0:(length(index)-1));
end

% get genes
genes = csv_table.textdata(2:end, 1);

noiseVar.obsNoise = cell(1,length(data));
for k=1:length(data)
    % A dynamic noise is used for the observation noise
    noiseVar.obsNoise{k} = (data{k}/10).^2;
    % Replace zero values with a small number to avoid numerical errors
    noiseVar.obsNoise{k}(noiseVar.obsNoise{k}==0) = 1e-6;
end

noiseVar.sysNoise = 1e-4;

[w,exprMean,exprVar,promState,kinParams,kinParamsVar,trees] = ...
jump3(data,obsTimes,noiseVar);