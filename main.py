import networkx as nx
import time
import os
import argparse
import NPA
import EPA
import gptree
import utils
import tracemalloc
import psutil
import linecache



parser = argparse.ArgumentParser(description="Peeling Algorithm for Hypergraph (k, g)-core")
parser.add_argument("--algorithm", help="Algorithm to use", choices=["NPA", "EPA", "tree", "compare"], default="tree")
parser.add_argument("--network", help="Path to the network file"
                    ,default='./datasets/congress/network.hyp')
parser.add_argument("--k", type=int, help="Value of k",default=3)
parser.add_argument("--g", type=int, help="Value of g",default=3)
args = parser.parse_args()


process = psutil.Process(os.getpid())
memory_before = process.memory_info().rss / (1024 * 1024)  # Convert to MB
# Load hypergraph
hypergraph, E = utils.load_hypergraph(args.network)

if args.algorithm == "NPA":
    start_time = time.time()
    G,NOM = NPA.run(hypergraph, args.k, args.g)
    end_time = time.time()
elif args.algorithm == "EPA":
    start_time = time.time()
    G, report, S = EPA.run(hypergraph, args.k, args.g)
    end_time = time.time()
elif args.algorithm == "tree":
    start_time = time.time()
    G, gpList, root, HT, S = gptree.kgComputation(hypergraph, E, args.k, args.g)
    end_time = time.time()
    mode = input("Select Mode (INSERT, REMOVE, END): ")
    if mode == "INSERT":
        newEdge = input("Type the new edge (e.g. 1 2 3): ")
        nodes = {node.strip() for node in newEdge.strip().split(',')}
        nodes = {int(x) for x in  nodes}
        hyperedge = set(nodes)
        E.append(hyperedge)
        for node in nodes:
                if node not in hypergraph.nodes():
                    hypergraph.add_node(node, hyperedges=list())  # Add a node for each node
                hypergraph.nodes[node]['hyperedges'].append(hyperedge)  # Add the hyperedge to the node's hyperedge set
        gptree.insertEdge(hypergraph, gpList, root, HT, hyperedge, args.k, args.g, S)
    elif mode == "REMOVE":
        pass
    else:
        pass
elif args.algorithm == "compare":
    start_time = time.time()
    G1, report, S = EPA.run(hypergraph, args.k, args.g)
    end_time = time.time()
    start_time2 = time.time()
    G2, gpList, root, HT, S = gptree.kgComputation(hypergraph, E, args.k, args.g)
    end_time2 = time.time()
    # tf = False
    # if set(G1) == set(G2):
    #     tf = True
    #     for node in set(G1) | set(G2):
    #         if S[node] != len(gptree.findGNbr(HT, node, args.g)):
    #             tf = False
    # print(tf)
    # print(set(G2) - set(G1))
    print(f'EPA: {len(G1)}')
    print(f"Run Time: {end_time - start_time}\n")
    print(f'gpTree: {len(G2)}')
    print(f"Run Time: {end_time2 - start_time2}\n")
    G = G1


memory_after = process.memory_info().rss / (1024 * 1024)  # Convert to MB
memory_usage = memory_after - memory_before  # Calculate memory used


# Write results to file
output_dir = os.path.dirname(args.network)

if args.algorithm == "decom":
    output_filename = f"decomposition_mod.dat"
else:
    output_filename = f"{args.algorithm}_{args.k}_{args.g}_core.dat"
output_path = os.path.join(output_dir, output_filename)

with open(output_path, 'w') as output_file:
    # Write size of nodes
    if args.algorithm != "decom":
        output_file.write(f"Num of nodes: {str(len(G))}\n")
    # Write running time
    output_file.write(f"Run Time: {end_time - start_time}\n")
    # Write nodes
    if args.algorithm == "decom":
        output_file.write("Result\n")
        for key, value in G.items():
            output_file.write(f"{key}: {value}\n")
    else:
        output_file.write("Nodes:")
        nodes = " ".join(str(node) for node in G)
        output_file.write(nodes + "\n")

    #write memory usage
    output_file.write("Memory Usage(MB): ")
    output_file.write(f"{memory_usage}\n")


print(f"Results written to {output_path}")