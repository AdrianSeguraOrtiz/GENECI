res = compiler.build.standaloneApplication('plsnet_code/main.m')
opts = compiler.package.DockerOptions(res,'ImageName','adriansegura99/geneci_infer-network_plsnet','ExecuteDockerBuild','off')
compiler.package.docker(res, 'Options', opts)
exit