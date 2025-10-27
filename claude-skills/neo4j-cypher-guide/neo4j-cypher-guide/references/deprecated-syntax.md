# Neo4j Modern Cypher Syntax Reference

## Critical Removed Features

### 1. id() Function (REMOVED)
**Old syntax:** 
```cypher
MATCH (n) WHERE id(n) = 123
```
**Replacement:** Use elementId() function
```cypher
MATCH (n) WHERE elementId(n) = "4:abc123:456"
```
**Note:** elementId() returns a string, not an integer. The format includes database id, node/relationship id, and other metadata.

### 2. Pattern Expressions for Path Lists (REMOVED)
**Old syntax:**
```cypher
RETURN [(n)-[r]->(m) | m.name]
```
**Note:** Pattern expressions can still be used as predicates in WHERE clauses, but not for producing lists

### 3. Implicit Grouping Keys (REMOVED)
**Problem:** Mixing aggregating and non-aggregating expressions without explicit grouping
```cypher
// This will fail in modern Neo4j
MATCH (n:Person)
RETURN n.age + count(*), n.name
```
**Solution:** Use explicit grouping with WITH
```cypher
MATCH (n:Person)
WITH n.age AS age, n.name AS name, count(*) AS cnt
RETURN age + cnt, name
```

### 4. Repeated Relationship Variables (REMOVED)
**Old syntax:**
```cypher
MATCH ()-[r*]->(), ()-[r*]->()  // Using same 'r' variable
```
**Solution:** Use different variables
```cypher
MATCH ()-[r1*]->(), ()-[r2*]->()
```

### 5. BTREE Indexes (REMOVED)
**Old syntax:**
```cypher
CREATE INDEX FOR (n:Label) ON (n.property) OPTIONS {indexProvider: 'native-btree-1.0'}
```
**Replacements:**
- For text queries: Use TEXT index
- For range queries: Use RANGE index (default)
- For spatial queries: Use POINT index

### 6. Automatic List to Boolean Coercion (REMOVED)
**Old syntax:**
```cypher
WHERE [1,2,3]  // Lists evaluated as true/false
```
**Replacement:** Use explicit checks
```cypher
WHERE size([1,2,3]) > 0
WHERE NOT isEmpty([1,2,3])
```

## Deprecated Features (Avoid these)

### Importing WITH in CALL Subqueries
**Deprecated syntax:**
```cypher
MATCH (n:Person)
CALL {
  WITH n  // Deprecated
  MATCH (n)-[:KNOWS]->(friend)
  RETURN friend
}
```
**Recommended syntax:**
```cypher
MATCH (n:Person)
CALL (n) {  // Scope clause
  MATCH (n)-[:KNOWS]->(friend)
  RETURN friend
}
```

## Common Migration Patterns

### Pattern 1: Counting Subqueries
**Old syntax:**
```cypher
RETURN size((n)--()) AS degree
```
**Modern syntax:**
```cypher
RETURN count{(n)--()} AS degree
```

### Pattern 2: Existence Checks
**Old syntax:**
```cypher
WHERE exists((n)-[:REL]->())
```
**Modern syntax (both work):**
```cypher
WHERE exists{(n)-[:REL]->()}
WHERE EXISTS {MATCH (n)-[:REL]->()}
```

## Modern Type System

### Label and Type Expressions
Label expressions for more concise syntax:
```cypher
// Check multiple labels
WHERE n:Person|Company

// Check label combinations
WHERE n:Person&Employee

// Negation
WHERE n:!Archived
```
