res = compiler.build.standaloneApplication('rsnet_code/main.m')
opts = compiler.package.DockerOptions(res,'ImageName','adriansegura99/geneci_infer-network_rsnet','ExecuteDockerBuild','off')
compiler.package.docker(res, 'Options', opts)
exit