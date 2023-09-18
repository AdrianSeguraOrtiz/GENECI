function main(expFile, outputFolder)
    %% Randomnes control
    seed = 0;
    RandStream.setGlobalStream(RandStream('mt19937ar', 'Seed', seed));
    randn('seed', seed);
    rand('seed', seed);

    %% Loading the data
    tic;
    csv_table = importdata(expFile, ',');
    genes = csv_table.textdata(2:end, 1);
    data = csv_table.data;
    Y = double(data);
    G = size(Y, 1);

    %% Variables and parameters initialization
    % Performance parameters
    model = 'AR1MA1'; % observational model
    epsilon = 1e-10; % converge criteria threshold
    delta = 0.5; % binary detection threshold
    % Output initialization
    X = nan(G);
    W = nan(G);
    GRN = cell(0, 5);
    % Uninformative priors
    m_x = 0.5 * ones(G, 1);
    S_x = 0.25 * eye(G);
    m_w = zeros(G, 1);
    S_w = eye(G);
    a = 2;
    b = 1 / a;
    % Posterior hyperparameters initialization
    mu_x = cell(G, 1);
    SIGMA_x = cell(G, 1);
    mu_w = cell(G, 1);
    SIGMA_w = cell(G, 1);
    alpha = cell(G, 1);
    beta = cell(G, 1);

    %% Hyperparameters learning
    toc; disp(char(10));
    for i = 1:G

        disp(strjoin([' - ', genes(i)], ''));
        [mu_x{i}, SIGMA_x{i}, mu_w{i}, SIGMA_w{i}, alpha{i}, beta{i}] = HYPERPARAMETERS(model, epsilon, Y, i, m_x, S_x, m_w, S_w, a, b);

    end %for

    %% GRN inference
    toc; disp(char(10));
    for i = 1:G
        probability = POSTERIOR(mu_x{i}, SIGMA_x{i});
        parents = find(probability >= delta);

        if (sum(parents) > 0)
            X(parents, i) = 1;
            W(parents, i) = mu_w{i}(parents);

            for j = 1:numel(parents)

                if (mu_w{i}(parents(j)) < 0)
                    GRN = [GRN; {genes{parents(j)} '-|' genes{i} mu_w{i}(parents(j)) probability(parents(j))}];
                else
                    GRN = [GRN; {genes{parents(j)} '->' genes{i} mu_w{i}(parents(j)) probability(parents(j))}];
                end %if

            end %for

        end %if

    end %for

    %% Output file (extended SIF)
    for k = 1:size(GRN, 1)
        if strcmp(GRN(k, 1), GRN(k, 3))
            GRN{k, 6} = 0;
        else
            GRN{k, 6} = abs(GRN{k, 4} * GRN{k, 5} / max(abs(prod(cell2mat(GRN(:, 4:5)), 2))));
        end
    end %for

    v = cell2mat(GRN(:, 6));
    v = (v - min(v)) / (max(v) - min(v));
    GRN(:, 6) = num2cell(v);

    [~, idx] = sort(v, 'descend');
    cnt = 0;
    for i=length(idx):-1:1
        if v(idx(i)) ~= 0
            break;
        end
        cnt = cnt + 1;
    end

    output_file = strcat(outputFolder, "/GRN_GRNVBEM.csv");
    fid = fopen(output_file, 'w');
    for l = 1:(length(idx)-cnt)
        fprintf(fid, '%s,%s,%f\n', GRN{idx(l), [1, 3, 6]});
    end
    fclose(fid);

end
