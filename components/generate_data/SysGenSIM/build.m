res = compiler.build.standaloneApplication('sysgensim_code/main.m')
opts = compiler.package.DockerOptions(res,'ImageName','adriansegura99/geneci_generate-data_sysgensim','ExecuteDockerBuild','off')
compiler.package.docker(res, 'Options', opts)
exit