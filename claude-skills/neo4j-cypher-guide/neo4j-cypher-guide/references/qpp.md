# Quantified Path Patterns (QPP) Reference

## Overview

Quantified Path Patterns (QPP) provide more powerful and efficient path pattern matching than traditional variable-length relationships. QPPs are part of the Graph Pattern Matching (GPM) feature and offer significant performance improvements for complex graph traversals.

## Key Advantages over Variable-Length Relationships

1. **Inline filtering** - Prune unwanted paths during traversal, not after
2. **Node access** - Reference and filter nodes along the path
3. **Complex patterns** - Repeat any pattern, not just single relationships
4. **Performance** - Can be 1000x+ faster for complex traversals due to early pruning

## Basic Syntax

### Quantified Relationships (Shorthand)

When you don't need to reference nodes in the pattern:

```cypher
// Traditional variable-length
MATCH (a:Person)-[:KNOWS*1..3]->(b:Person)

// QPP quantified relationship (equivalent but more efficient)
MATCH (a:Person)-[:KNOWS]-{1,3}(b:Person)
```

### Full QPP Syntax

When you need to reference or filter nodes/relationships in the pattern:

```cypher
// Basic QPP with node reference
MATCH (start:Station)
      ((n)-[r:CONNECTED]->(m) WHERE r.distance < 10){1,5}
      (end:Station)
RETURN start, end, [x IN n | x.name] AS stops
```

## Quantifier Syntax

### Fixed Repetition

```cypher
// Exactly 3 hops
(pattern){3}
```

### Range Repetition

```cypher
// Between 1 and 5 hops
(pattern){1,5}

// At least 2 hops
(pattern){2,}

// Zero or more (Kleene star)
(pattern){0,}
// or
(pattern)*

// One or more (Kleene plus)  
(pattern){1,}
// or
(pattern)+
```

## Group Variables

QPP introduces group variables that collect all matched elements:

```cypher
MATCH (a:Person)((n)-[r:KNOWS]->(m)){2,4}(b:Person)
WHERE a.name = 'Alice' AND b.name = 'Bob'
RETURN 
  [x IN n | x.name] AS intermediateNodes,
  [x IN r | x.since] AS relationshipDates
```

## Inline Filtering Examples

### Filter Nodes in Pattern

```cypher
// Find paths through wealthy people only
MATCH (a:Person)
      ((n:Person)-[:KNOWS]->(m:Person) WHERE n.netWorth > 1000000){1,3}
      (b:Person)
RETURN a, b
```

### Progressive Distance Filtering

```cypher
// Only traverse if getting closer to destination
MATCH (start:Location {name: 'A'}),
      (end:Location {name: 'B'})
MATCH (start)
      ((l)-[r:ROAD]->(r) 
       WHERE point.distance(r.location, end.location) < 
             point.distance(l.location, end.location) + 1000){1,}
      (end)
RETURN start, end
```

### Degree-Based Traversal

```cypher
// Stop at junction nodes (degree > 2)
MATCH p=(start:Node)
        (()-[]->(n WHERE count{(n)--()} < 3))*
        ()-[]->(junction WHERE count{(junction)--()} > 2)
RETURN p
```

## Advanced Patterns

### Alternating Node Types

```cypher
// Find paths alternating between Person and Company
MATCH path = (p:Person)
             ((p1:Person)-[:WORKS_FOR]->(c:Company)
              (c)-[:EMPLOYS]->(p2:Person)){1,3}
WHERE p.name = 'Alice'
RETURN path
```

### Conditional Path Expansion

```cypher
// Expand until a condition is met
MATCH (start:Account {id: 'A123'})
      ((a1:Account)-[t:TRANSFER]->(a2:Account) 
       WHERE t.amount > 10000 AND NOT a2.flagged){1,}
      (end:Account WHERE end.flagged = true)
RETURN start, end, count(t) AS hops
```

### Using EXISTS in QPP

```cypher
// Only traverse through nodes with specific relationships
MATCH (a:Person)
      ((n:Person)-[:KNOWS]->(m:Person) 
       WHERE EXISTS {(m)-[:MANAGES]->(:Department)}){1,3}
      (b:Person)
RETURN a, b
```

## Performance Optimization Patterns

### Early Pruning

```cypher
// BAD - Filter after expansion
MATCH path = (a)-[*1..10]->(b)
WHERE all(n IN nodes(path) WHERE n.active = true)
RETURN path

// GOOD - Filter during expansion
MATCH path = (a)((n WHERE n.active = true)-[]->(m WHERE m.active = true)){1,5}(b)
RETURN path
```

### Combining with Indexes

```cypher
// Start with indexed lookup, then QPP expansion
MATCH (start:Person {email: 'alice@example.com'})
MATCH (start)((n:Person)-[:KNOWS]->(m:Person WHERE m.age > 25)){1,3}(end:Person)
WHERE end.city = 'London'
RETURN end
```

## Common Use Cases

### Finding Cycles

```cypher
// Find cycles of specific length
MATCH (start:Account)
      ((a1)-[t:TRANSFER]->(a2) WHERE t.amount > 1000){4,10}
      (start)
RETURN start, sum([x IN t | x.amount]) AS cycleAmount
```

### Shortest Path with Constraints

```cypher
// Shortest path through specific node types only
MATCH (from:City {name: 'Berlin'}),
      (to:City {name: 'Prague'})
MATCH path = (from)
             ((c1:City)-[r:ROAD]->(c2:City) 
              WHERE r.toll < 10){1,}
             (to)
RETURN path
ORDER BY length(path)
LIMIT 1
```

### Multi-Hop Aggregations

```cypher
// Aggregate properties along the path
MATCH (source:Router)
      ((r1:Router)-[c:CONNECTION]->(r2:Router)){1,5}
      (target:Router)
WHERE source.ip = '192.168.1.1' AND target.ip = '10.0.0.1'
RETURN source, target,
       reduce(latency = 0, x IN c | latency + x.latency) AS totalLatency,
       [n IN r1 | n.ip] AS path
```

## Best Practices

1. **Use quantified relationships for simple patterns** - More concise and readable
2. **Apply filters early** - Filter within the QPP pattern, not afterwards
3. **Limit unbounded expansions** - Use upper bounds to prevent runaway queries
4. **Leverage indexes** - Start QPP patterns from indexed nodes when possible
5. **Consider memory usage** - Group variables store all matched elements

## Migration from Variable-Length Relationships

### Simple Migration

```cypher
// Old
MATCH (a)-[r:REL*1..3]->(b)
WHERE all(x IN r WHERE x.weight > 0.5)

// New with QPP
MATCH (a)(()-[r:REL WHERE r.weight > 0.5]->())
{1,3}(b)
```

### Complex Migration

```cypher
// Old (inefficient)
MATCH path = (a)-[*1..5]->(b)
WHERE all(n IN nodes(path) WHERE n.active = true)
  AND all(r IN relationships(path) WHERE r.weight > 0.5)

// New with QPP (efficient)
MATCH path = (a)
             ((n WHERE n.active = true)-[r WHERE r.weight > 0.5]->(m WHERE m.active = true)){1,5}
             (b)
```

## Important: Do Not Use Anonymous Nodes

1. All Nodes Must Be Explicitly Named
   ❌ **WRONG** - Anonymous nodes with WHERE clauses:

```cypher
// This will fail with "Variable `_` not defined"
MATCH (start)
  ((:Organization WHERE _.revenue > 100000000)-[:REL]->(:Organization)){1,3}
  (end)
```

✅ **CORRECT** - Explicitly named nodes:

```cypher
MATCH (start)
  ((org:Organization WHERE org.revenue > 100000000)-[:REL]->()){1,3}
  (end)
```

**Key Rule:** If you use a WHERE clause on a node in a QPP pattern, that node MUST have an explicit variable name. You cannot use `_` or anonymous patterns `()` with WHERE clauses.
