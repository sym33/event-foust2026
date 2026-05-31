#!/usr/bin/env python3
"""Run SPARQL regression checks for the Event Re-typing Pattern examples."""
from pathlib import Path
from rdflib import Graph

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    "derive-retypes.rq": ("rows", 4),
    "displaced-types.rq": ("rows", 4),
    "refigured-classifications.rq": ("rows", 5),
    "current-types.rq": ("rows", 6),
    "construct-retyping-records.rq": ("triples", 40),
    "ask-no-enrichment-retyping.rq": ("ask", False),
    "ask-no-contested-retyping.rq": ("ask", False),
}


def load_graph() -> Graph:
    graph = Graph()
    for path in [ROOT / "ontology/retyping-pattern.ttl", *sorted((ROOT / "examples").glob("*.ttl"))]:
        graph.parse(path, format="turtle")
    return graph


def result_size(result) -> int:
    if result.type == "CONSTRUCT":
        return len(result.graph)
    return len(list(result))


def main() -> int:
    graph = load_graph()
    failures = []
    for query_name, (kind, expected) in EXPECTED.items():
        result = graph.query((ROOT / "queries" / query_name).read_text())
        if kind == "ask":
            actual = bool(result.askAnswer)
            print(f"{query_name}: ASK {actual}")
        elif kind == "triples":
            actual = result_size(result)
            print(f"{query_name}: {actual} constructed triples")
        else:
            actual = result_size(result)
            print(f"{query_name}: {actual} rows")
        if actual != expected:
            failures.append((query_name, expected, actual))

    if failures:
        for query_name, expected, actual in failures:
            print(f"FAILED {query_name}: expected {expected}, got {actual}")
        return 1
    print("SPARQL validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
