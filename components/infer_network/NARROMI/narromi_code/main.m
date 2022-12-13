function main(expFile, outputFolder)

    lamda = 1;
    alpha = 0.05;
    beta = 0.05;
    t = 0.6;

    csv_table = importdata(expFile, ',');
    genes = csv_table.textdata(2:end, 1);
    data = csv_table.data;

    network = zeros(size(genes, 1), size(genes, 1));
    network_v = network;
    netsig = network;

    for i = 1:size(genes, 1)
        y = data(i, :);
        X = [data(1:i - 1, :); data(i + 1:size(data, 1), :)];
        [net, net_value, sig] = narromi(y', X', lamda, alpha, beta, t);
        network(i, 1:i - 1) = net(1:i - 1); network(i, i + 1:size(data, 1)) = net(i:end);
        network_v(i, 1:i - 1) = net_value(1:i - 1); network_v(i, i + 1:size(data, 1)) = net(i:end);
        netsig(i, 1:i - 1) = sig(1:i - 1); netsig(i, i + 1:size(data, 1)) = sig(i:end);
    end

    % Output the network
    significance = 0.05;
    network_sig = zeros(size(netsig));
    network_sig(netsig <= significance) = 1;
    network_sig(logical(eye(size(network_sig)))) = 0;
    [testfile_network] = Connect_for_cytoscape_pvalue(network_sig', network_v', netsig', genes, genes);
    
    a = testfile_network';
    v = cell2mat(a(3, :));
    v = abs(v);
    v = (v - min(v)) / (max(v) - min(v));
    a(3, :) = num2cell(v);

    [~,idx] = sort(v, 'descend');
    cnt = 0;
    for i=idx(end:-1:1)
        if v(i) ~= 0
            break;
        end
        cnt = cnt + 1;
    end
    
    fid = fopen(strcat(outputFolder, '/GRN_NARROMI.csv'), 'w');
    fprintf(fid, '%s,%s,%.6f\n', a{1:3, idx(1:(end-cnt))});
    fclose(fid);

end
