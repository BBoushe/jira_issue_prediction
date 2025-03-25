# Project Structure
```
./jira_graph_prediction/
├── README.md
├── requirements.txt
├── data/
│   ├── README.md
│   ├── ThePublicJiraDataset/       <-- after downloading and extracting from Zendo
│   ├── etc/
│   │   └── mongod.conf
│   └── var/
│       ├── lib/
│       └── log/
│           └── mongodb/
│               └── mongod.log
├── notebooks/
│   ├── explore_and_build_graph.ipynb
│   ├── extract_dataset.ipynb
│   └── util/
├── papers/
│   └── 2201.08368v3.pdf
├── requirements.txt
├── scripts/
│   ├── data_extraction.py
│   ├── graph_construction.py
│   ├── main.py
│   └── text_embedding.py
└── util/
    ├── mongo_scripts/
    │   ├── countAllTypesInCollections.js
    │   ├── countBlockingInCollections.js
    │   ├── fetchDocument.js
    │   └── findOneBlockingDoc.js
    └── projectStructureCollector.sh
```

- data_extraction.py: Connects to MongoDB and retrieves issues/documents.
- graph_construction.py: Builds the graph (nodes + edges) from the fetched data.
- text_embedding.py: Encodes textual fields (summary, description, etc.) into embeddings.
- main.py: An example orchestrator script that wires together the above modules.
- notebooks/: Jupyter notebooks for experimentation, visual checks, or quick iteration.


