function main(expFile, outputFolder)

    %% Dataset input
    csv_table = importdata(expFile, ',');
    genes = csv_table.textdata(2:end, 1);
    Y = csv_table.data;

    %% Run RSNET method on the data
    lamda = 1;
    alpha = 0.1; % parameter for correlation
    gama = 0.5; % parameter for prior information
    beta = 0.1; % parameter for deleting the noise
    t = 0.5; %  Parameter for the interation of MI and RO;  t:[0,1]

    J_na = zeros(size(Y, 1), size(Y, 1)); J_s = J_na;

    for i = 1:size(Y, 1)

        if mod(i, 50) == 0
            fprintf('Network inferring for gene: i=%d of %d.\n', i, size(Y, 1));
        end

        y = Y(i, :);
        X = [Y(1:i - 1, :); Y(i + 1:size(Y, 1), :)];
        [net, net_value] = RSNET(y', X', lamda, alpha, gama, beta, t);
        J_s(i, 1:i - 1) = net(1:i - 1); J_s(i, i + 1:size(Y, 1)) = net(i:end);
        J_na(i, 1:i - 1) = net_value(1:i - 1); J_na(i, i + 1:size(Y, 1)) = net_value(i:end);
    end

    w = abs(J_na);
    nw = (w - min(w(:))) ./ (max(w(:)) - min(w(:)));

    getLinkList(nw, (1:length(genes)), genes, 0, strcat(outputFolder, "/GRN_RSNET.csv"));

end
