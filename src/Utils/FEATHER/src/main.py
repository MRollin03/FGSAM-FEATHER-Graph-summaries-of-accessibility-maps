"""Running FEATHER."""
from utils import tab_printer, load_graph, load_graphs, save_embedding
from feather import FEATHER, FEATHERG
from param_parser import parameter_parser
import pandas as pd
import numpy as np


def main(args):
    """
    Characteristic function embedding wrapper.
    :param args: Arguments object parsed up.
    """
    if args.model_type == "FEATHER":
        print("\nFitting a node embedding.\n")
        graph = load_graph(args.graph_input)
        features = pd.read_csv(args.feature_input).values  # (N, 10), no index column

        assert features.shape[0] == graph.number_of_nodes(), (
            f"Node/feature mismatch: {features.shape[0]} rows in CSV "
            f"vs {graph.number_of_nodes()} nodes in graph"
        )

        model = FEATHER()
        model.fit(graph, features, args)

    elif args.model_type == "FEATHER-G":
        print("\nFitting a graph level embedding.\n")
        graphs = load_graphs(args.graphs_input)
        model = FEATHERG()
        model.fit(graphs)

    else:
        raise ValueError(f"Unknown model type: {args.model_type}")

    X = model.get_embedding()
    save_embedding(X, args)


if __name__ == "__main__":
    args = parameter_parser()
    tab_printer(args)
    main(args)