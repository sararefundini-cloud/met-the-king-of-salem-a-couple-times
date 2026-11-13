# Neo4j-ready import files

These files are a **node inventory** of motifs and terms on the public-domain
King James text. They are Neo4j-ready import files; they have **not yet been
loaded or tested in a running Neo4j instance**. The text-analytics results in
this project do not depend on Neo4j.

- `motifs.csv` — one row per motif, with rolled-up counts
- `terms.csv` — one row per lexicon term
- `import.cypher` — `LOAD CSV` script for Neo4j Desktop or Aura

The graph created by the Cypher script has two node layers only:
`(:Term)-[:IN_MOTIF]->(:Motif)`. There are no term–term or motif–motif
relationships. To try a load, copy the two CSVs into the DBMS `import/`
folder (or upload them on Aura) and run `import.cypher`.
