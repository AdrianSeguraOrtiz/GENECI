res = compiler.build.standaloneApplication('locpcacmi_code/main.m')
opts = compiler.package.DockerOptions(res,'ImageName','adriansegura99/geneci_infer-network_locpcacmi','ExecuteDockerBuild','off')
compiler.package.docker(res, 'Options', opts)
exit