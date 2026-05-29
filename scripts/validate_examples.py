#!/usr/bin/env python3
"""Validate the event re-typing examples without external RDF libraries.

The script parses the deliberately simple Turtle subset used in examples/.
It checks the same boundary conditions as the SPARQL queries:

- positive disease and seismic re-typing cases are derived;
- enrichment under the same sortal does not derive re-typing;
- contested classification without supersession does not derive re-typing;
- chain histories preserve intermediate superseded sortals and current typing.

For full RDF/SHACL validation, use an RDF engine such as pySHACL against
ontology/retyping-pattern.ttl and shapes/retyping-shapes.ttl.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


ERP = "https://w3id.org/event-retyping-pattern/"
EX = "https://w3id.org/event-retyping-pattern/example/"


@dataclass(frozen=True)
class Retypes:
    later_act: str
    earlier_act: str
    occurrence: str
    earlier_sortal: str
    later_sortal: str


def expand(token: str, prefixes: dict[str, str]) -> str:
    token = token.strip()
    if token == "a":
        return "rdf:type"
    if token.startswith("<") and token.endswith(">"):
        return token[1:-1]
    if ":" in token:
        prefix, local = token.split(":", 1)
        return prefixes[prefix] + local
    return token


def load_triples(paths: list[Path]) -> set[tuple[str, str, str]]:
    prefixes = {"erp": ERP, "ex": EX}
    triples: set[tuple[str, str, str]] = set()
    prefix_re = re.compile(r"@prefix\s+([^:]+):\s+<([^>]+)>\s+\.")

    for path in paths:
        for raw in path.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            match = prefix_re.match(line)
            if match:
                prefixes[match.group(1)] = match.group(2)
                continue
            if not line.endswith("."):
                raise ValueError(f"Unsupported Turtle line in {path}: {line}")
            body = line[:-1].strip()
            parts = body.split()
            if len(parts) < 3:
                raise ValueError(f"Unsupported Turtle line in {path}: {line}")
            subject = expand(parts[0], prefixes)
            predicate = expand(parts[1], prefixes)
            obj = expand(parts[2], prefixes)
            triples.add((subject, predicate, obj))
    return triples


def objects(triples: set[tuple[str, str, str]], subject: str, predicate: str) -> set[str]:
    return {o for s, p, o in triples if s == subject and p == predicate}


def subjects(triples: set[tuple[str, str, str]], predicate: str, obj: str) -> set[str]:
    return {s for s, p, o in triples if p == predicate and o == obj}


def derive_retypes(triples: set[tuple[str, str, str]]) -> set[Retypes]:
    produces = ERP + "produces"
    precedes = ERP + "precedes"
    supersedes = ERP + "supersedes"
    has_warrant = ERP + "hasSupersessionWarrant"
    warranted_replacement_of = ERP + "warrantedReplacementOf"
    maintenance_purpose = ERP + "maintenancePurpose"
    asserts_typing = ERP + "assertsTyping"
    typing_occurrence = ERP + "typingOccurrence"
    typing_sortal = ERP + "typingSortal"

    out: set[Retypes] = set()
    for earlier_act, _, earlier_ice in triples:
        if _ != produces:
            continue
        for later_act in objects(triples, earlier_act, precedes):
            for later_ice in objects(triples, later_act, produces):
                if (later_ice, supersedes, earlier_ice) not in triples:
                    continue
                warrants = objects(triples, later_ice, has_warrant)
                if not any(
                    (warrant, warranted_replacement_of, earlier_ice) in triples
                    and objects(triples, warrant, maintenance_purpose)
                    for warrant in warrants
                ):
                    continue
                for earlier_typing in objects(triples, earlier_ice, asserts_typing):
                    for later_typing in objects(triples, later_ice, asserts_typing):
                        earlier_occurrences = objects(triples, earlier_typing, typing_occurrence)
                        later_occurrences = objects(triples, later_typing, typing_occurrence)
                        for occurrence in earlier_occurrences & later_occurrences:
                            for earlier_sortal in objects(triples, earlier_typing, typing_sortal):
                                for later_sortal in objects(triples, later_typing, typing_sortal):
                                    if earlier_sortal != later_sortal:
                                        out.add(
                                            Retypes(
                                                later_act,
                                                earlier_act,
                                                occurrence,
                                                earlier_sortal,
                                                later_sortal,
                                            )
                                        )
    return out


def current_types(triples: set[tuple[str, str, str]], retypes: set[Retypes]) -> set[tuple[str, str]]:
    produces = ERP + "produces"
    asserts_typing = ERP + "assertsTyping"
    typing_occurrence = ERP + "typingOccurrence"
    typing_sortal = ERP + "typingSortal"

    superseded = {(r.earlier_act, r.occurrence, r.earlier_sortal) for r in retypes}
    current: set[tuple[str, str]] = set()
    for act, _, ice in triples:
        if _ != produces:
            continue
        for typing in objects(triples, ice, asserts_typing):
            for occurrence in objects(triples, typing, typing_occurrence):
                for sortal in objects(triples, typing, typing_sortal):
                    if (act, occurrence, sortal) not in superseded:
                        current.add((occurrence, sortal))
    return current


def compact(value: str) -> str:
    return value.replace(EX, "ex:").replace(ERP, "erp:")


def main() -> None:
    example_paths = sorted(EXAMPLES.glob("*.ttl"))
    triples = load_triples(example_paths)
    retypes = derive_retypes(triples)
    current = current_types(triples, retypes)
    superseded = {(r.occurrence, r.earlier_sortal) for r in retypes}

    expected_retypes = {
        Retypes(EX + "classify_disease_2", EX + "classify_disease_1", EX + "disease_episode_17", EX + "AtypicalPneumoniaEpisode", EX + "COVID19Episode"),
        Retypes(EX + "classify_seismic_2", EX + "classify_seismic_1", EX + "seismic_event_42", EX + "TectonicEarthquake", EX + "InducedSeismicity"),
        Retypes(EX + "classify_chain_2", EX + "classify_chain_1", EX + "chain_event", EX + "T1", EX + "T2"),
        Retypes(EX + "classify_chain_3", EX + "classify_chain_2", EX + "chain_event", EX + "T2", EX + "T3"),
    }

    if retypes != expected_retypes:
        missing = expected_retypes - retypes
        extra = retypes - expected_retypes
        raise AssertionError(f"Unexpected Retypes facts. Missing={missing}; Extra={extra}")

    assert (EX + "enrichment_event", EX + "StableSyndrome") in current
    assert all(r.occurrence != EX + "enrichment_event" for r in retypes)
    assert all(r.occurrence != EX + "contested_event" for r in retypes)
    assert (EX + "chain_event", EX + "T1") in superseded
    assert (EX + "chain_event", EX + "T2") in superseded
    assert (EX + "chain_event", EX + "T3") in current
    assert (EX + "chain_event", EX + "T1") not in current
    assert (EX + "chain_event", EX + "T2") not in current

    print("Validation passed.")
    print(f"Loaded example files: {len(example_paths)}")
    print(f"Loaded triples: {len(triples)}")
    print(f"Derived Retypes facts: {len(retypes)}")
    for fact in sorted(retypes, key=lambda r: (r.occurrence, r.earlier_sortal, r.later_sortal)):
        print(
            "  "
            + ", ".join(
                [
                    f"later={compact(fact.later_act)}",
                    f"earlier={compact(fact.earlier_act)}",
                    f"occurrence={compact(fact.occurrence)}",
                    f"from={compact(fact.earlier_sortal)}",
                    f"to={compact(fact.later_sortal)}",
                ]
            )
        )
    print("Negative checks passed: enrichment and contested cases derive no Retypes facts.")
    print("Chain check passed: T1 and T2 superseded; T3 current.")


if __name__ == "__main__":
    main()
