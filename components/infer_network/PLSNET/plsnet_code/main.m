function main(expFile, outputFolder)

    lamda = 0.03;

    csv_table = importdata(expFile, ',');
    genes = csv_table.textdata(2:end, 1);
    data = csv_table.data;

    w = plsnet(data', 1:length(genes), 5, length(genes), 1000);
    nw = (w - min(w(:))) ./ (max(w(:)) - min(w(:)));
    getLinkList(nw, (1:length(genes)), genes, 0, strcat(outputFolder, "/GRN_PLSNET.csv"));

end
