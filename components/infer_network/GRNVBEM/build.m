res = compiler.build.standaloneApplication('grnvbem_code/main.m')
opts = compiler.package.DockerOptions(res,'ImageName','adriansegura99/geneci_infer-network_grnvbem','ExecuteDockerBuild','off')
compiler.package.docker(res, 'Options', opts)
exit