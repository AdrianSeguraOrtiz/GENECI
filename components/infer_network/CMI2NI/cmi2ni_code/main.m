function main(expFile, outputFolder)

    csv_table = importdata(expFile, ',');
    genes = csv_table.textdata(2:end, 1);
    data = csv_table.data;

    lamda = 0.03;
    order0 = round(100 / length(genes) + 1);

    [~, w, ~] = cmi2ni(data, lamda, order0);
    nw = (w - min(w(:))) ./ (max(w(:)) - min(w(:)));
    getLinkList(nw, (1:length(genes)), genes, 0, strcat(outputFolder, "/GRN_CMI2NI.csv"));

end
