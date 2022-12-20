res = compiler.build.standaloneApplication('pcacmi_code/main.m')
opts = compiler.package.DockerOptions(res,'ImageName','adriansegura99/geneci_infer-network_pcacmi','ExecuteDockerBuild','off')
compiler.package.docker(res, 'Options', opts)
exit