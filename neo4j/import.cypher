// KJV motif inventory — two node layers only.
// (:Term)-[:IN_MOTIF]->(:Motif)
// No term–term or motif–motif relationships in this load.
//
// These are Neo4j-ready import files; they have not yet been loaded
// or tested in a running Neo4j instance.
//
// Neo4j Desktop: copy terms.csv and motifs.csv into the DBMS import/
// folder, then run this script. Aura: upload the two CSVs and adjust
// the file URLs if needed.
//
// Files:
//   motifs.csv  — one row per motif, rolled-up counts
//   terms.csv   — one row per lexicon term (hit_count may be 0)

CREATE CONSTRAINT motif_name IF NOT EXISTS FOR (m:Motif) REQUIRE m.name IS UNIQUE;
CREATE CONSTRAINT term_id IF NOT EXISTS FOR (t:Term) REQUIRE t.term_id IS UNIQUE;

LOAD CSV WITH HEADERS FROM 'file:///motifs.csv' AS row
MERGE (m:Motif {name: row.motif})
SET m.term_count = toInteger(row.term_count),
    m.hit_count = toInteger(row.hit_count),
    m.verse_count = toInteger(row.verse_count),
    m.first_appearance = row.first_appearance,
    m.last_appearance = row.last_appearance,
    m.top_books = row.top_books,
    m.terms = row.terms;

LOAD CSV WITH HEADERS FROM 'file:///terms.csv' AS row
MERGE (t:Term {term_id: row.term_id})
SET t.name = row.term,
    t.subgroup = row.subgroup,
    t.match_type = row.match_type,
    t.confidence = row.confidence,
    t.hit_count = toInteger(row.hit_count),
    t.verse_count = toInteger(row.verse_count),
    t.first_appearance = row.first_appearance,
    t.last_appearance = row.last_appearance,
    t.top_books = row.top_books,
    t.ot_refs = row.ot_refs,
    t.echo_of = row.echo_of,
    t.notes = row.notes
WITH t, row
MATCH (m:Motif {name: row.motif})
MERGE (t)-[:IN_MOTIF]->(m);

// ---- example queries (nodes and IN_MOTIF only) ----

// Motif inventory by verse count
// MATCH (m:Motif)
// RETURN m.name, m.verse_count, m.hit_count, m.first_appearance, m.last_appearance, m.top_books
// ORDER BY m.verse_count DESC;

// Stones and its terms, by subgroup
// MATCH (t:Term)-[:IN_MOTIF]->(m:Motif {name:'Stones'})
// RETURN t.subgroup, t.name, t.verse_count, t.hit_count, t.first_appearance, t.last_appearance
// ORDER BY t.subgroup, t.verse_count DESC;

// A Johannine I AM term and its OT echo refs (property, not a relationship)
// MATCH (t:Term)-[:IN_MOTIF]->(:Motif {name:'I AM'})
// WHERE t.subgroup = 'Johannine I am'
// RETURN t.name, t.first_appearance, t.last_appearance, t.ot_refs;

// God-as-Rock terms
// MATCH (t:Term)-[:IN_MOTIF]->(:Motif {name:'Stones'})
// WHERE t.subgroup = 'God as Rock/Stone'
// RETURN t.name, t.verse_count, t.top_books
// ORDER BY t.verse_count DESC;
