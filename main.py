import networkx as nx
import time
import os
import argparse
import NPA
import EPA
import gptree as gptree
import utils
import tracemalloc
import psutil
import linecache



parser = argparse.ArgumentParser(description="Peeling Algorithm for Hypergraph (k, g)-core")
parser.add_argument("--algorithm", help="Algorithm to use", choices=["NPA", "EPA", "tree", "compare"], default="compare")
parser.add_argument("--network", help="Path to the network file", default='congress')
parser.add_argument("--k", type=int, help="Value of k", default=20)
parser.add_argument("--g", type=int, help="Value of g", default=10)
args = parser.parse_args()
args.network = f"./datasets/{args.network}/network.hyp"

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
    print(f'Run Time: {end_time - start_time}')
    mode = input("Select Mode (INSERT, REMOVE, QUIT): ")
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
        targetId = int(input("Type the id of the hyperedge to remove: "))
        if 0 <= targetId < len(E):
            targetEdge = E.pop(targetId)
            remove_start = time.time()
            gptree.removeEdge(hypergraph, gpList, root, HT, targetEdge, args.k, args.g, S)
            remove_end = time.time()
            print(f'Removal Time: {remove_end - remove_start}')
        else:
            print("Index Out of Bound")
        pass
    else:
        pass
elif args.algorithm == "compare":
    memory_before_tree = process.memory_info().rss / (1024 * 1024)  # Convert to MB
    start_time_tree = time.time()
    # tracemalloc.start()
    G2, gpList, root, HT, S2 = gptree.kgComputation(hypergraph, E, args.k, args.g)
    # current, peak = tracemalloc.get_traced_memory()
    # tracemalloc.stop()
    end_time_tree = time.time()
    memory_after_tree = process.memory_info().rss / (1024 * 1024)  # Convert to MB
    print(f'gpTree: {len(G2)}')
    print(f"Run Time: {end_time_tree - start_time_tree}")
    print(f"Memory Usage: {memory_after_tree - memory_before_tree}\n")
    # print(f"Memory Usage: {current / (1024 * 1024)}")
    # print(f'Memory Peak: {peak / (1024 * 1024)}\n')

    memory_before_NPA = process.memory_info().rss / (1024 * 1024)  # Convert to MB
    start_time_NPA = time.time()
    # tracemalloc.start()
    G0, NOM = NPA.run(hypergraph, args.k, args.g)
    # current, peak = tracemalloc.get_traced_memory()
    # tracemalloc.stop()
    end_time_NPA = time.time()
    memory_after_NPA = process.memory_info().rss / (1024 * 1024)  # Convert to MB
    print(f'NPA: {len(G0)}')
    print(f"Run Time: {end_time_NPA - start_time_NPA}")
    print(f"Memory Usage: {memory_after_NPA - memory_before_NPA}\n")
    # print(f"Memory Usage: {current / (1024 * 1024)}")
    # print(f'Memory Peak: {peak / (1024 * 1024)}\n')

    memory_before = process.memory_info().rss / (1024 * 1024)  # Convert to MB
    start_time = time.time()
    # tracemalloc.start()
    G1, report, S = EPA.run(hypergraph, args.k, args.g)
    # current, peak = tracemalloc.get_traced_memory()
    # tracemalloc.stop()
    end_time = time.time()
    memory_after = process.memory_info().rss / (1024 * 1024)  # Convert to MB
    print(f'EPA: {len(G1)}')
    print(f"Run Time: {end_time - start_time}")
    print(f"Memory Usage: {memory_after - memory_before}\n")
    # print(f"Memory Usage: {current / (1024 * 1024)}")
    # print(f'Memory Peak: {peak / (1024 * 1024)}\n')
    
    # tf = False
    # if set(G1) == set(G2):
    #     tf = True
    #     for node in set(G1) | set(G2):
    #         if S[node] != len(gptree.findGNbr(HT, node, args.g)):
    #             tf = False
    # print(tf)
    # print(set(G2) - set(G1))print(f'EPA: {len(G1)}')
    G = G1


memory_after = process.memory_info().rss / (1024 * 1024)  # Convert to MB
memory_usage = memory_after - memory_before  # Calculate memory used


# Write results to file
output_dir = os.path.dirname(args.network)

output_filename = f"{args.algorithm}_{args.k}_{args.g}_core.dat"
output_path = os.path.join(output_dir, output_filename)

with open(output_path, 'w') as output_file:
    # Write size of nodes
    output_file.write(f"Num of nodes: {str(len(G))}\n")
    # Write running time
    output_file.write(f"Run Time: {end_time - start_time}\n")
    # Write nodes
    
    output_file.write("Nodes:")
    nodes = " ".join(str(node) for node in G)
    output_file.write(nodes + "\n")

    #write memory usage
    output_file.write("Memory Usage(MB): ")
    output_file.write(f"{memory_usage}\n")


print(f"Results written to {output_path}")