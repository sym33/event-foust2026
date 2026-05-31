# Event Re-typing Pattern Artifact

This repository contains a machine-readable companion artifact for the event
re-typing pattern. It turns the paper's conceptual distinction into a small
OWL/SWRL/SHACL/SPARQL package with executable examples.

## Why This Artifact Is Needed

The paper argues that event ontology and classificatory description cannot be
cleanly separated in ontology engineering. Under a sortal, an occurrence is not
only placed in time; it is represented as the kind of occurrence that supplies
criteria for identity, internal structure, and relevant participants. This is
already visible in Guarino et al.'s treatment of event descriptions: focal,
internal, characterizing, and external components depend on the sortal under
which the occurrence is described.

The re-typing case adds a further representational problem. A later
classification may reorient an earlier one for the same traceable occurrence.
That change is not a new event token, but it is more than additional metadata.
It changes which sortal organizes the occurrence for ontology maintenance,
querying, and downstream use.

The history is not merely cumulative. A later reorientation can change the
maintenance role of earlier records: an earlier type assignment may move from
current organizing type to displaced frame, preliminary reading, or
review-relevant commitment. The earlier artifact remains present and auditable,
but it no longer functions in the same way once the later classification has
reoriented the record. The artifact is needed because this case crosses the
boundary between open-world ontological typing and closed-world maintenance
operations.

No single Semantic Web layer captures the pattern cleanly:

- OWL supplies the vocabulary, typing constraints, inverses, and reified
  re-typing records.
- SWRL states the positive derivation rule for when one classification act
  re-types another.
- SHACL checks integrity constraints that OWL alone does not reject, both for raw reorientation histories and for materialized re-typing records.
- SPARQL derives operational views such as current types, displaced types, and
  refigured classifications.
- The dependency-free derivation validator gives a regression check for the
  example cases used in the paper.

The split follows from the modeling problem. Re-typing is not class subsumption; it is an n-ary relation among two classification acts, two information-content entities, one occurrence, two sortals, temporal order, and reorientation. The artifact models that non-cumulative maintenance pattern instead of reducing it to a single OWL class axiom.

## Directory Layout

```text
ontology/retyping-pattern.ttl       OWL vocabulary and core constraints
rules/retyping.swrl                 SWRL derivation rules
shapes/retyping-shapes.ttl          SHACL integrity constraints
queries/*.rq                        SPARQL queries and CONSTRUCT materializer
examples/*.ttl                      Positive and negative example graphs
scripts/validate_examples.py        Dependency-free derivation validator
scripts/validate_shacl.py           pySHACL integrity validator
scripts/validate_sparql.py          SPARQL query regression validator
```

## Core Pattern

The paper's formal pattern is represented as follows.

| Paper term | Artifact encoding |
| --- | --- |
| occurrence `o` | `erp:Occurrent` |
| event sortal `T` | `erp:EventSortal`, a metamodeling proxy for an event type/class |
| classification act `c` | `erp:ClassificationAct` |
| classificatory artifact `i` | `erp:InformationContentEntity` |
| typing assertion | `erp:TypingAssertion` |
| act produces artifact | `erp:produces` |
| artifact asserts type | `erp:assertsTyping` plus `erp:typingOccurrence` and `erp:typingSortal` |
| temporal order | `erp:precedes` |
| reorientation | `erp:reorients` |
| reorientation basis | `erp:ReorientationBasis`, `erp:hasReorientationBasis`, `erp:basisForReorientationOf`, `erp:maintenancePurpose`, `erp:basisScope`, `erp:hasAuthorizingSource` |
| historical role shift | `erp:HistoricalRole`, `erp:CurrentFrame`, `erp:DisplacedFrame`, `erp:refiguredBy` |
| re-typing | `erp:RetypingRecord` or derived `erp:retypesAct` |

The positive derivation condition is:

```text
Retypes(c2,c1,o,T1,T2) iff
  c1 produces i1,
  c2 produces i2,
  i1 asserts that o has sortal T1,
  i2 asserts that o has sortal T2,
  T1 and T2 are distinct,
  c1 precedes c2,
  i2 reorients i1,
  i2 carries a reorientation basis that points to i1, states a maintenance purpose,
  gives a scope, and names an authorizing source or workflow.
```

## Dependency-Free Derivation Validation

The derivation validator checks the examples without requiring an RDF stack. Its expected output is:

```text
Validation passed.
Loaded example files: 6
Loaded triples: 196
Derived Retypes facts: 4
  later=ex:classify_chain_2, earlier=ex:classify_chain_1, occurrence=ex:chain_event, from=ex:T1, to=ex:T2
  later=ex:classify_chain_3, earlier=ex:classify_chain_2, occurrence=ex:chain_event, from=ex:T2, to=ex:T3
  later=ex:classify_disease_2, earlier=ex:classify_disease_1, occurrence=ex:disease_episode_17, from=ex:AtypicalPneumoniaEpisode, to=ex:COVID19Episode
  later=ex:classify_seismic_2, earlier=ex:classify_seismic_1, occurrence=ex:seismic_event_42, from=ex:TectonicEarthquake, to=ex:InducedSeismicity
Negative checks passed: enrichment and contested cases derive no Retypes facts.
Refigured classification facts: 5
Historical role assertions checked: 10
Chain check passed: T1 and T2 displaced; T3 current.
```

The validator uses only the standard library. It parses the simple Turtle style
used in `examples/`, derives the same re-typing facts as the SWRL/SPARQL
specification, and checks the positive and negative cases.

## SHACL Validation

The SHACL validation uses pySHACL over the ontology and bundled example graphs.
Its expected output is:

```text
Validation Report
Conforms: True
```

This loads the ontology and all example graphs, including the materialized re-typing records, and checks both raw typing-history reorientations and reified records.

## SPARQL Validation

The SPARQL regression check loads the ontology and examples into RDFLib and checks the query results. Expected output includes four derived re-typing rows, four displaced-type rows, five refigured-classification rows, six current-type rows, 40 constructed record triples, and `false` for both negative ASK queries.

## Example Cases

### Disease Reclassification

`examples/disease-reclassification.ttl` represents a case in which an
occurrence first classified as an atypical pneumonia episode is later classified
as a COVID-19 episode. The later classificatory artifact reorients the earlier
one. The same occurrence is retained; the organizing sortal changes.
The earlier pneumonia artifact is also assigned `erp:DisplacedFrame` and
`erp:ReviewRelevantCommitment`; the later COVID-19 artifact is assigned
`erp:CurrentFrame`. The example therefore records that the old classification
has changed historical role, not merely that a newer fact was appended.

Expected result:

```text
Retypes(classify_disease_2, classify_disease_1, disease_episode_17,
        AtypicalPneumoniaEpisode, COVID19Episode)
```

### Seismic Reclassification

`examples/seismic-reclassification.ttl` represents a recorded seismic
occurrence initially classified as a tectonic earthquake and later classified as
induced seismicity after additional evidence. This is stronger than enrichment:
the later sortal changes the relevant explanatory and maintenance commitments.
The tectonic artifact is kept as a displaced and review-relevant commitment,
because earlier alerts, hazard assumptions, and institutional decisions may
still need to be audited under the older frame. The induced-seismicity artifact
becomes the current frame for catalog maintenance.

Expected result:

```text
Retypes(classify_seismic_2, classify_seismic_1, seismic_event_42,
        TectonicEarthquake, InducedSeismicity)
```

### Enrichment Negative Case

`examples/enrichment-negative.ttl` represents a later assertion about the same
occurrence under the same sortal. It may add information, but it does not
re-type the occurrence.

Expected result:

```text
No Retypes fact.
```

### Contested Negative Case

`examples/contested-negative.ttl` represents two different classifications
without a reorientation relation. The model records disagreement or coexistence,
not re-typing.

Expected result:

```text
No Retypes fact.
```

### Chain History

`examples/chain-history.ttl` represents a sequence of reorienting
classifications. The current type is the final non-displaced sortal.
It also materializes the non-cumulative part of the pattern: `ice_chain_3`
refigures both `ice_chain_2` directly and `ice_chain_1` indirectly, so an
earlier classification can change role because of a later event in the
classification history.

Expected result:

```text
Retypes(classify_chain_2, classify_chain_1, chain_event, T1, T2)
Retypes(classify_chain_3, classify_chain_2, chain_event, T2, T3)
Current type: T3
```

## SPARQL Queries

The queries assume the ontology and relevant example files have been loaded
into one dataset.

Derive re-typing facts:

```bash
sparql --data=ontology/retyping-pattern.ttl \
       --data=examples/disease-reclassification.ttl \
       --query=queries/derive-retypes.rq
```

Materialize re-typing records:

```bash
sparql --data=ontology/retyping-pattern.ttl \
       --data=examples/disease-reclassification.ttl \
       --query=queries/construct-retyping-records.rq
```

Find current types:

```bash
sparql --data=ontology/retyping-pattern.ttl \
       --data=examples/chain-history.ttl \
       --query=queries/current-types.rq
```

Check negative cases:

```bash
sparql --data=ontology/retyping-pattern.ttl \
       --data=examples/enrichment-negative.ttl \
       --query=queries/ask-no-enrichment-retyping.rq

sparql --data=ontology/retyping-pattern.ttl \
       --data=examples/contested-negative.ttl \
       --query=queries/ask-no-contested-retyping.rq
```

Both ASK queries should return `false`. The bundled regression validator checks the expected counts for all queries.

## SHACL Validation

The SHACL shapes check the integrity of typing assertions, raw typing-history reorientations, and materialized re-typing records. After loading the ontology and examples, a SHACL engine should confirm that classificatory ICEs point to the same occurrence as their typing assertion and that reorienting classificatory ICEs support a genuine re-typing candidate. After adding `examples/materialized-retyping-records.ttl`, it should also validate the reified records:

- each typing assertion has exactly one occurrence and one sortal;
- each raw reorientation used for re-typing connects the same occurrence under distinct sortals;
- each raw reorientation used for re-typing carries a reorientation basis, maintenance purpose, scope, and authorizing source;
- each raw reorientation is produced by a later classification act than the displaced typing;
- each materialized re-typing record has one earlier and one later act;
- the earlier and later sortals differ;
- the later classificatory artifact reorients the earlier one;
- the earlier act precedes the later act;
- the record's occurrence matches the occurrence in both typing assertions.

The bundled SHACL validator loads the required ontology, positive cases, negative cases, and materialized records together.

## Modeling Limits

This artifact is scoped to the re-typing maintenance pattern, not to a full metaphysics of events. It does not attempt to axiomatize every
event relation, every BFO category, or all possible temporal logics. It captures
the paper's target problem: preserving occurrence continuity while recording
changed classificatory commitments.

The division across OWL, SWRL, SHACL, and SPARQL is part of the claim. OWL gives
the ontological vocabulary; SWRL and SPARQL derive the positive pattern; SHACL
guards raw typing-history assertions and materialized records; the current-type
view is closed-world and therefore is kept in SPARQL and in the validation layer rather
than forced into OWL.
