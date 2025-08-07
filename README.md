# Combinators Dataset

This repo consists mainly of two files:

- 'combinators-dataset/dataset.jsonl' : a jsonl file containing almost 12.000 pairs of type term expressions in SK Combinatory Logic.
- combinators-dataset/main.py : by adjusting the hyperparameters and running this file you might replicate the dataset.

## Dataset Structure:

Each row of the dataset consists of a json object with two fields: 'term' and 'type'. The first one is a
string of S and K that represents a term in the corresponding type.
