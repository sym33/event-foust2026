# Event Re-typing Pattern Artifact

This repository is the machine-readable companion artifact for the event
re-typing pattern. It provides a small OWL/SWRL/SHACL/SPARQL package with
examples and validators for occurrence-level classification history.

The artifact covers cases in which one traceable occurrence is first classified
under one event sortal and later under another. The occurrence is preserved, the
earlier classification remains auditable, and the later classification changes
the maintenance role of the earlier record. This is stronger than enrichment
under a stable sortal and more structured than a provenance note.

The implementation uses the Semantic Web layers for different tasks:

- OWL defines the vocabulary for occurrences, classification acts,
  classificatory artifacts, event-sortal proxies, reorientation bases, and
  re-typing records.
- SWRL states the positive derivation rule for supported reorientation.
- SHACL checks integrity constraints over raw classification histories and
  materialized re-typing records.
- SPARQL derives operational views such as current types, displaced types,
  refigured classifications, and review-impact sets.
- The Python validators provide reproducible regression checks for the examples.

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

| Paper term | Artifact encoding |
| --- | --- |
| occurrence `o` | `erp:Occurrent` |
| event sortal `T` | `erp:EventSortal`, a proxy for an event type/class |
| classification act `c` | `erp:ClassificationAct` |
| classificatory artifact `i` | `erp:InformationContentEntity` |
| typing assertion | `erp:TypingAssertion` |
| act produces artifact | `erp:produces` |
| artifact asserts type | `erp:assertsTyping`, `erp:typingOccurrence`, `erp:typingSortal` |
| temporal order | `erp:precedes` |
| reorientation | `erp:reorients` |
| reorientation basis | `erp:ReorientationBasis`, `erp:hasReorientationBasis`, `erp:basisForReorientationOf`, `erp:maintenancePurpose`, `erp:basisScope`, `erp:hasAuthorizingSource` |
| historical role | `erp:CurrentFrame`, `erp:DisplacedFrame`, `erp:ReviewRelevantCommitment`, `erp:ReviewSalientCommitment`, `erp:ReviewRequiredCommitment`, `erp:refiguredBy` |
| impact review | `erp:ReviewPolicy`, `erp:dependsOnTyping`, `erp:hasReviewPolicy`, `erp:reviewSalientAfter`, `erp:reviewRequiredAfter`, `queries/review-impact.rq` |
| re-typing | `erp:RetypingRecord` or derived `erp:retypesAct` |

The positive derivation condition is:

```text
Retypes(c2,c1,o,T1,T2,p) iff
  c1 produces i1,
  c2 produces i2,
  i1 asserts that o has sortal T1,
  i2 asserts that o has sortal T2,
  T1 and T2 are distinct,
  c1 precedes c2,
  i2 reorients i1,
  i2 carries a reorientation basis that points to i1,
  states a maintenance purpose, gives a scope,
  and names an authorizing source or workflow.

Review impact is derived separately. A downstream artifact is review-salient
when it depends on a displaced classificatory artifact. It becomes
review-required only when the reorientation basis carries an explicit
`erp:ReviewPolicy` or maintenance protocol. The pattern therefore exposes the
affected dependencies without deciding by itself which of them require action.
```

## Validation

Run the dependency-free validator:

```bash
python3 scripts/validate_examples.py
```

Expected summary:

```text
Validation passed.
Loaded example files: 6
Loaded triples: 210
Derived Retypes facts: 4
Negative checks passed: enrichment and contested cases derive no Retypes facts.
Refigured classification facts: 5
Review-impact facts: 6
Historical role assertions checked: 10
Chain check passed: T1 and T2 displaced; T3 current.
```

Run the SPARQL regression checks:

```bash
python3 scripts/validate_sparql.py
```

Expected summary:

```text
derive-retypes.rq: 4 rows
displaced-types.rq: 4 rows
refigured-classifications.rq: 5 rows
current-types.rq: 6 rows
review-impact.rq: 6 rows
construct-retyping-records.rq: 40 constructed triples
ask-no-enrichment-retyping.rq: ASK False
ask-no-contested-retyping.rq: ASK False
SPARQL validation passed.
```

Run the SHACL check:

```bash
python3 scripts/validate_shacl.py
```

Expected output:

```text
Validation Report
Conforms: True
```

## Example Cases

### Disease Reclassification

`examples/disease-reclassification.ttl` represents an occurrence first
classified as an atypical pneumonia episode and later as a COVID-19 episode.
The earlier pneumonia artifact is kept as displaced and review-relevant; the
later COVID-19 artifact becomes the current frame. Line-list and exposure-map
artifacts depending on the earlier typing are review-salient after
reorientation, and the attached public-health review policy turns the relevant
ones into required review actions.

Expected result:

```text
Retypes(classify_disease_2, classify_disease_1, disease_episode_17,
        AtypicalPneumoniaEpisode, COVID19Episode)
```

### Seismic Reclassification

`examples/seismic-reclassification.ttl` represents a recorded seismic
occurrence first classified as a tectonic earthquake and later as induced
seismicity. The tectonic classification remains auditable because earlier
alerts, hazard assumptions, and institutional decisions may depend on it. Prior
alert and hazard-aggregate artifacts become review-salient after reorientation;
the catalog impact-review policy determines when that salience becomes a
required review action.

Expected result:

```text
Retypes(classify_seismic_2, classify_seismic_1, seismic_event_42,
        TectonicEarthquake, InducedSeismicity)
```

### Enrichment Negative Case

`examples/enrichment-negative.ttl` adds information under the same sortal. It
does not derive re-typing.

Expected result:

```text
No Retypes fact.
```

### Contested Negative Case

`examples/contested-negative.ttl` contains two different classifications without
a reorientation relation. The graph records disagreement or coexistence, not
re-typing.

Expected result:

```text
No Retypes fact.
```

### Chain History

`examples/chain-history.ttl` represents a sequence of reorienting
classifications. The final non-displaced sortal is current, while intermediate
classifications remain recoverable. The case also checks indirect refiguration:
`ice_chain_3` refigures both `ice_chain_2` directly and `ice_chain_1`
indirectly. A mapping artifact depending on the first classification is
review-salient across the chain; because no review policy is attached in this
example, salience is not converted into a required review action.

Expected result:

```text
Retypes(classify_chain_2, classify_chain_1, chain_event, T1, T2)
Retypes(classify_chain_3, classify_chain_2, chain_event, T2, T3)
Current type: T3
```

## SPARQL Queries

The queries assume that the ontology and relevant example graphs are loaded into
one dataset.

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

Find current, displaced, and review-impact views:

```bash
sparql --data=ontology/retyping-pattern.ttl \
       --data=examples/chain-history.ttl \
       --query=queries/current-types.rq

sparql --data=ontology/retyping-pattern.ttl \
       --data=examples/chain-history.ttl \
       --query=queries/displaced-types.rq

sparql --data=ontology/retyping-pattern.ttl \
       --data=examples/disease-reclassification.ttl \
       --query=queries/review-impact.rq
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

Both ASK queries should return `false`.

## SHACL Coverage

The SHACL shapes check that:

- typing assertions have exactly one occurrence and one sortal;
- raw reorientations used for re-typing connect the same occurrence under
  distinct sortals;
- reorientations carry a basis, maintenance purpose, scope, and authorizing
  source;
- the reorienting classification act is later than the displaced one;
- materialized re-typing records have one earlier and one later act;
- record occurrences match the occurrences in both typing assertions.

## Scope

The artifact is a reusable classification-history layer for event ontologies. It
preserves one occurrence while recording changed classificatory commitments,
current and displaced views, and the basis for reorientation. OWL supplies the
vocabulary; SWRL and SPARQL derive the positive pattern; SHACL checks integrity;
and the validators provide reproducible regression tests.
