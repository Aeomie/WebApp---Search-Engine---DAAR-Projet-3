from JaccardGraph import JaccardGraph

if __name__ == "__main__":
    # Create graph object
    jaccard_graph = JaccardGraph(
        threshold=0.1,
        max_frac = 0.15
    )

    # Build graph directly from inverted index (faster than building book_words first)
    jaccard_graph.build_graph_from_inverted_index(
        inverted_index_path="../books_data/index_TableTC.json",
        catalog_path="../books_data/catalog.json",
        progress_interval=0.01
    )

    # Compute PageRank (NumPy version)
    jaccard_graph.calculate_pagerank_numpy(
        max_iterations=100,
        damping=0.85
    )

    # Save results
    jaccard_graph.save_pagerank(
        "../books_data/pagerank.json"
    )

    print("✓ Finished building graph and PageRank.")
