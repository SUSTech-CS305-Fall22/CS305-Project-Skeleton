import argparse
import os
import networkx as nx
import matplotlib.pyplot as plt

def visualize_network(topo_file, nodes_file, output_file, show_queue = False):
    edges = []
    peer_nodes = []
    with open(topo_file, "r") as tf:
        while True:
            line = tf.readline()
            if not line:
                break
            if "#" in line:
                continue
            line_info = line.split(" ")
            edges.append([int(line_info[0]), int(line_info[1]), {"queue": int(line_info[4])}])

    with open(nodes_file, "r") as nf:
        while True:
            line = nf.readline()
            if not line:
                break
            if "#" in line:
                continue
            line_info = line.split(" ")
            peer_nodes.append(int(line_info[0]))
            

    print(f"edges: {edges}")
    print(f"nodes with peers: {peer_nodes}")
    G = nx.Graph()
    G.add_edges_from(edges)
    nodes_colormap = []
    for node in list(G.nodes()):
        if node in peer_nodes:
            nodes_colormap.append("r")
        else:
            nodes_colormap.append("b")
            
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, node_color=nodes_colormap);

    if show_queue:
        nx.draw_networkx_edge_labels(G,pos, edge_labels=nx.get_edge_attributes(G, 'queue'))

    plt.savefig(output_file)
    print(f"plot saved to {os.path.abspath(output_file)}, show queue size: {show_queue}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--topo', type=str, help='topo file', required=True)
    parser.add_argument('-n', '--node', type=str, help='nodes file', required=True)
    parser.add_argument('-o', '--output', type=str, help="output file", default="net-visual.png")
    parser.add_argument('-q', "--queue", help="show queue size in plot", action='store_true')
    args = parser.parse_args()
    
    visualize_network(args.topo, args.node, args.output, args.queue)
