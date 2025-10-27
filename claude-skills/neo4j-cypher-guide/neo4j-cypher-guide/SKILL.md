---
name: neo4j-cypher-guide
description: Comprehensive guide for writing modern Neo4j Cypher read queries. Essential for text2cypher MCP tools and LLMs generating Cypher queries. Covers removed/deprecated syntax, modern replacements, CALL subqueries for reads, COLLECT patterns, sorting best practices, and Quantified Path Patterns (QPP) for efficient graph traversal.
---

# Neo4j Modern Cypher Query Guide

This skill helps generate Neo4j Cypher read queries using modern syntax patterns and avoiding deprecated features. It focuses on efficient query patterns for graph traversal and data retrieval.

## Quick Compatibility Check

When generating Cypher queries, immediately avoid these REMOVED features:
- ❌ `id()` function → Use `elementId()`
- ❌ Implicit grouping keys → Use explicit WITH clauses
- ❌ Pattern expressions for lists → Use pattern comprehension or COLLECT subqueries
- ❌ Repeated relationship variables → Use unique variable names
- ❌ Automatic list to boolean coercion → Use explicit checks

## Core Principles for Query Generation

1. **Use modern syntax patterns** - QPP for complex traversals, CALL subqueries for complex reads
2. **Optimize during traversal** - Filter early within patterns, not after expansion
3. **Always filter nulls when sorting** - Add IS NOT NULL checks for sorted properties
4. **Explicit is better than implicit** - Always use explicit grouping and type checking

## Critical Sorting Rule

**ALWAYS filter NULL values when sorting:**
```cypher
// WRONG - May include null values
MATCH (n:Node)
RETURN n.name, n.value
ORDER BY n.value

// CORRECT - Filter nulls before sorting
MATCH (n:Node)
WHERE n.value IS NOT NULL
RETURN n.name, n.value
ORDER BY n.value
```

## Query Pattern Selection Guide

### For Simple Queries
Use standard Cypher patterns with modern syntax:
```cypher
MATCH (n:Label {property: value})
WHERE n.otherProperty IS :: STRING
RETURN n
```

### For Variable-Length Paths
Consider Quantified Path Patterns (QPP) for better performance:
```cypher
// Instead of: MATCH (a)-[*1..5]->(b)
// Use: MATCH (a)-[]-{1,5}(b)

// With filtering:
MATCH (a)((n WHERE n.active)-[]->(m)){1,5}(b)
```

### For Aggregations
Use COUNT{}, EXISTS{}, and COLLECT{} subqueries:
```cypher
MATCH (p:Person)
WHERE count{(p)-[:KNOWS]->()} > 5
RETURN p.name, 
       exists{(p)-[:MANAGES]->()} AS isManager
```

### For Complex Read Operations
Use CALL subqueries for sophisticated data retrieval:
```cypher
MATCH (d:Department)
CALL (d) {
  MATCH (d)<-[:WORKS_IN]-(p:Person)
  WHERE p.salary IS NOT NULL  // Filter nulls
  WITH p ORDER BY p.salary DESC
  LIMIT 3
  RETURN collect(p.name) AS topEarners
}
RETURN d.name, topEarners
```

## Common Query Transformations

### Counting Patterns
```cypher
// Old: RETURN size((n)-[]->())
// Modern: RETURN count{(n)-[]->()}
```

### Checking Existence
```cypher
// Old: WHERE exists((n)-[:REL]->())
// Modern: WHERE EXISTS {MATCH (n)-[:REL]->()}
// Also valid: WHERE exists{(n)-[:REL]->()}
```

### Element IDs
```cypher
// Old: WHERE id(n) = 123
// Modern: WHERE elementId(n) = "4:abc123:456"
// Note: elementId returns a string, not integer
```

### Sorting with Null Handling
```cypher
// Always add null check
MATCH (n:Node)
WHERE n.sortProperty IS NOT NULL
RETURN n
ORDER BY n.sortProperty

// Or use NULLS LAST
MATCH (n:Node)
RETURN n
ORDER BY n.sortProperty NULLS LAST
```

## When to Load Reference Documentation

Load the appropriate reference file when:

### references/deprecated-syntax.md
- Migrating queries from older Neo4j versions
- Encountering syntax errors with legacy queries
- Need complete list of removed/deprecated features

### references/subqueries.md
- Working with CALL subqueries for reads
- Using COLLECT or COUNT subqueries
- Handling complex aggregations
- Implementing sorting with null filtering

### references/qpp.md
- Optimizing variable-length path queries
- Need early filtering during traversal
- Working with paths longer than 3-4 hops
- Complex pattern matching requirements

## Query Generation Checklist

Before finalizing any generated query:

1. ✅ No deprecated functions (id, btree indexes, etc.)
2. ✅ Explicit grouping for aggregations
3. ✅ NULL filters for all sorted properties
4. ✅ Appropriate subquery patterns for reads
5. ✅ Consider QPP for paths with filtering needs
6. ✅ Use COUNT{} instead of size() for pattern counting
7. ✅ Variable scope clauses in CALL subqueries
8. ✅ Unique variable names for relationships

## Error Resolution Patterns

### "Implicit grouping key" errors
```cypher
// Problem: RETURN n.prop, count(*) + n.other
// Solution: WITH n.prop AS prop, n.other AS other, count(*) AS cnt
//          RETURN prop, cnt + other
```

### "id() function not found"
```cypher
// Use elementId() but note it returns a string, not integer
```

### "Repeated variable" errors
```cypher
// Problem: MATCH (a)-[r*]->(), (b)-[r*]->()
// Solution: MATCH (a)-[r1*]->(), (b)-[r2*]->()
```

## Performance Tips

1. **Start with indexed properties** - Always anchor patterns with indexed lookups
2. **Filter early in QPP** - Apply WHERE clauses within the pattern
3. **Filter nulls before sorting** - Prevent unexpected results and improve performance
4. **Limit expansion depth** - Use reasonable upper bounds in quantifiers
5. **Use EXISTS for existence checks** - More efficient than counting
6. **Profile queries** - Use PROFILE to identify bottlenecks

## Modern Cypher Features

### Label Expressions
```cypher
WHERE n:Label1|Label2  // OR
WHERE n:Label1&Label2  // AND
WHERE n:!Archived      // NOT
```

### Type Predicates
```cypher
WHERE n.prop IS :: STRING
WHERE n.value IS :: INTEGER NOT NULL
WHERE n.data IS :: LIST<STRING>
```

### Subquery Patterns for Reads
- COUNT{} - Count patterns efficiently
- EXISTS{} - Check pattern existence
- COLLECT{} - Collect complex results
- CALL{} - Execute subqueries for complex reads

### Quantified Path Patterns
- Inline filtering during traversal
- Access to nodes and relationships in patterns
- Significant performance improvements (up to 1000x)
- Support for complex, multi-hop patterns

Always prefer modern syntax patterns for better performance and maintainability.
