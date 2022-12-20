function main(adjMatFile, expFile, outputFolder)

    load(adjMatFile);
    lamda = 0.03;

    csv_table = importdata(expFile, ',');
    genes = csv_table.textdata(2:end, 1);
    data = csv_table.data;

    gnum = size(data, 1);
    scoreIdxMatrix = zeros(gnum, gnum, gnum);
    G = zeros(gnum, gnum);

    %% for each subnetwork
    for i = 1:size(adj, 1)

        ntvcsIdx = adj(i, :);

        tvcsIdx = [i find(ntvcsIdx > 0)];

        nvcsIdx = [1:length(tvcsIdx)];

        subdata = data(tvcsIdx, :);

        %% go pca_cmi
        [Gb, Gval, order] = pca_cmi(subdata, lamda);
        GvalSysmetric = triu(Gval, -1) + tril(Gval', 0);

        tGval = zeros(gnum, gnum);

        for m = 1:length(nvcsIdx)

            for n = 1:length(nvcsIdx)
                tGval(tvcsIdx(nvcsIdx(m)), tvcsIdx(nvcsIdx(n))) = GvalSysmetric(m, n);
            end

        end

        scoreIdxMatrix(:, :, i) = tGval;

    end

    for i = 1:gnum

        for j = 1:gnum
            [ii, ~, v] = find(scoreIdxMatrix(i, j, :));
            G(i, j) = mean(v);
        end

    end

    indices = find(isnan(G) == 1);
    G(indices) = 0;

    nw = (G - min(G(:))) ./ (max(G(:)) - min(G(:)));
    getLinkList(nw, (1:length(genes)), genes, 0, strcat(outputFolder, "/GRN_LOCPCACMI.csv"));

end
