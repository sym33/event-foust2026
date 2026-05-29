#!/usr/bin/env python3
"""Run SHACL validation for the Event Re-typing Pattern examples."""
from pathlib import Path
from rdflib import Graph
from pyshacl import validate

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    data = Graph()
    for path in [ROOT / "ontology/retyping-pattern.ttl", *sorted((ROOT / "examples").glob("*.ttl"))]:
        data.parse(path, format="turtle")

    shapes = Graph().parse(ROOT / "shapes/retyping-shapes.ttl", format="turtle")
    conforms, _, report_text = validate(
        data,
        shacl_graph=shapes,
        inference="rdfs",
        abort_on_first=False,
        allow_infos=True,
        allow_warnings=True,
    )
    print(report_text)
    return 0 if conforms else 1


if __name__ == "__main__":
    raise SystemExit(main())
