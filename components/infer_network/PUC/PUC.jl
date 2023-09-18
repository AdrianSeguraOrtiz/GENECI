using NetworkInference

if length(ARGS) >= 2
    println("ARGS == 1: the argument will be treated as input csv file")
    in_file = ARGS[1]
    println("ARGS == 2: the argument will be treated as output folder")
    output_folder = ARGS[2]
elseif length(ARGS) == 1 && ARGS[1] == "--help" 
    println("Usage:")
    println("julia PUC.jl input.csv path/to/output_folder") 
    println("Arguments required:")
    println("\t 1) CSV input file")
    println("\t 2) Path to output folder")
    exit()
elseif length(ARGS) < 2
    println("More arguments required, write --help to see the options")
    throw(error())
end

inferred_network = infer_network(in_file, PUCNetworkInference(); delim = ',')

max_weight = first(inferred_network.edges).weight
min_weight = last(inferred_network.edges).weight

out_file = open(output_folder * "/GRN_PUC.csv", "w")
for edge in inferred_network.edges
    normalized_weight = (edge.weight - min_weight) / (max_weight - min_weight)
    nodes = edge.nodes
    write(out_file, string(
        nodes[1].label, ",", nodes[2].label, ",",
        normalized_weight, "\n",
        nodes[2].label, ",", nodes[1].label, ",",
        normalized_weight, "\n"
    ))
end
close(out_file)