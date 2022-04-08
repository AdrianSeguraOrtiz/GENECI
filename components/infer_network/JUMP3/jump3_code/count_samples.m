function n = count_samples(sample_idx)

n = 0;
for k=1:length(sample_idx)
    n = n + length(sample_idx{k});
end