# Neo4j Subqueries and Aggregation Patterns

## CALL Subqueries for Read Operations

### Basic Syntax
CALL subqueries allow for complex query composition for:
- Post-union processing
- Limiting results per row
- Conditional queries
- Complex aggregations

### Variable Scope Clause (Recommended)
```cypher
// Import specific variables
MATCH (p:Person)
CALL (p) {
  MATCH (p)-[:KNOWS]->(friend)
  RETURN friend
}
RETURN p, friend

// Import no variables
MATCH (p:Person)
CALL () {
  MATCH (c:Company)
  RETURN count(c) AS companyCount
}
RETURN p, companyCount
```

### Conditional Queries
```cypher
// Return different results based on conditions
MATCH (n:Node)
CALL (n) {
  WITH n
  WHERE n.type = 'A'
  RETURN 'TypeA' AS result, n.propertyA AS value
  UNION
  WITH n
  WHERE n.type = 'B'
  RETURN 'TypeB' AS result, n.propertyB AS value
}
RETURN n.id, result, value
```

### Post-UNION Processing
```cypher
CALL {
  MATCH (p:Person) RETURN p AS node, 'Person' AS type
  UNION
  MATCH (c:Company) RETURN c AS node, 'Company' AS type
}
WITH node, type
WHERE node.revenue > 1000000
RETURN node.name, type
```

## COLLECT Subqueries

### Basic COLLECT Subquery
```cypher
MATCH (p:Person)
WITH p, COLLECT {
  MATCH (p)-[:KNOWS]->(friend)
  RETURN friend.name
} AS friendNames
RETURN p.name, friendNames
```

### Complex COLLECT with Filtering
```cypher
MATCH (p:Person)
WITH p, COLLECT {
  MATCH (p)-[:KNOWS]->(f)
  WHERE f.age > 30
  WITH f
  ORDER BY f.age DESC
  LIMIT 5
  RETURN f.name
} AS topOldestFriends
RETURN p.name, topOldestFriends
```

## COUNT Subqueries

### Modern count{} syntax
```cypher
// Count relationships
MATCH (p:Person)
WHERE count{(p)-[:KNOWS]->()} > 5
RETURN p

// Using COUNT in RETURN
MATCH (p:Person)
RETURN p.name, count{(p)-[:KNOWS]->()} AS friendCount
ORDER BY friendCount DESC
```

## EXISTS Subqueries

### Pattern Existence Check
```cypher
// Simple pattern check
MATCH (p:Person)
WHERE EXISTS {(p)-[:MANAGES]->(:Department)}
RETURN p

// Complex existence check
MATCH (p:Person)
WHERE EXISTS {
  MATCH (p)-[:WORKS_IN]->(d:Department)
  WHERE d.budget > 1000000
}
RETURN p
```

## Sorting Best Practices

### IMPORTANT: Always Filter NULL Values When Sorting
```cypher
// WRONG - May include null values in results
MATCH (p:Person)
RETURN p.name, p.age
ORDER BY p.age

// CORRECT - Filter out null values before sorting
MATCH (p:Person)
WHERE p.age IS NOT NULL
RETURN p.name, p.age
ORDER BY p.age

// Alternative - Handle nulls explicitly
MATCH (p:Person)
RETURN p.name, p.age
ORDER BY p.age DESC NULLS LAST
```

## Aggregation Best Practices

### Avoiding Implicit Grouping Keys
```cypher
// WRONG - Will fail in modern Neo4j
MATCH (p:Person)
RETURN p.name, p.age + count(*)

// CORRECT - Explicit grouping
MATCH (p:Person)
WITH p.name AS name, p.age AS age, count(*) AS cnt
RETURN name, age + cnt
```

### Proper Use of COLLECT
```cypher
// Collecting with ordering
MATCH (d:Department)<-[:WORKS_IN]-(p:Person)
WHERE p.salary IS NOT NULL  // Filter nulls before sorting
WITH d, p ORDER BY p.salary DESC
RETURN d.name, collect(p.name)[..5] AS topEarners
```

### Memory-Efficient Aggregations
```cypher
// Use subqueries to limit aggregation scope
MATCH (d:Department)
CALL (d) {
  MATCH (d)<-[:WORKS_IN]-(p:Person)
  WHERE p.salary IS NOT NULL
  RETURN avg(p.salary) AS avgSalary
}
RETURN d.name, avgSalary
```

## Common Read Patterns

### Pattern: Get Top N per Group
```cypher
MATCH (d:Department)
CALL (d) {
  MATCH (d)<-[:WORKS_IN]-(p:Person)
  WHERE p.salary IS NOT NULL  // Always filter nulls when sorting
  WITH p ORDER BY p.salary DESC
  LIMIT 3
  RETURN collect(p.name) AS topThree
}
RETURN d.name, topThree
```

### Pattern: Conditional Aggregation
```cypher
MATCH (p:Person)
WITH p, 
     count{(p)-[:KNOWS]->(:Person)} AS friendCount,
     count{(p)-[:WORKS_WITH]->(:Person)} AS colleagueCount
WHERE friendCount > colleagueCount
RETURN p.name, friendCount, colleagueCount
```

### Pattern: Multiple Aggregations
```cypher
MATCH (c:Company)
CALL (c) {
  MATCH (c)<-[:WORKS_FOR]-(p:Person)
  WHERE p.age IS NOT NULL  // Filter nulls for accurate aggregation
  RETURN count(p) AS employees, avg(p.age) AS avgAge
}
RETURN c.name, employees, avgAge
```

### Pattern: Limiting Results per Row
```cypher
// Get first 3 friends for each person
MATCH (p:Person)
CALL (p) {
  MATCH (p)-[:KNOWS]->(friend)
  RETURN friend
  ORDER BY friend.name
  LIMIT 3
}
RETURN p.name, collect(friend.name) AS firstThreeFriends
```