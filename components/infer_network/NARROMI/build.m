res = compiler.build.standaloneApplication('narromi_code/main.m')
opts = compiler.package.DockerOptions(res,'ImageName','adriansegura99/geneci_infer-network_narromi','ExecuteDockerBuild','off')
compiler.package.docker(res, 'Options', opts)
exit