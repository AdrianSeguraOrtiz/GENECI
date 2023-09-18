function qM_new = extendStates(qM,obsTimes,nStep)
%function qM_new = extendStates(qM,obsTimes,nStep)

qM_new = zeros(1,nStep+1);

for t=1:length(obsTimes)-1
    qM_new(obsTimes(t)+1:obsTimes(t+1)) = qM(t);
end

qM_new(obsTimes(t+1)+1:end) = qM(end);