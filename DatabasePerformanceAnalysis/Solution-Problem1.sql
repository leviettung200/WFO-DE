-- 1. How many tables are there in the database
SELECT COUNT(*) AS TableCount
FROM information_schema.tables
WHERE table_type = 'BASE TABLE';

-- 2. List all tables size
SELECT 
    s.Name AS SchemaName,
    t.name AS TableName,
    SUM(a.total_pages) * 8 AS TotalSpaceKB, 
    SUM(a.used_pages) * 8 AS UsedSpaceKB, 
    (SUM(a.total_pages) - SUM(a.used_pages)) * 8 AS UnusedSpaceKB
FROM 
    sys.tables t
INNER JOIN      
    sys.indexes i ON t.object_id = i.object_id
INNER JOIN 
    sys.partitions p ON i.object_id = p.object_id AND i.index_id = p.index_id
INNER JOIN 
    sys.allocation_units a ON p.partition_id = a.container_id
INNER JOIN 
    sys.schemas s ON t.schema_id = s.schema_id
GROUP BY 
    t.name, s.Name
ORDER BY 
    TotalSpaceKB DESC;

-- 3. List tables that have zero records
SELECT 
    t.NAME AS TableName,
    s.Name AS SchemaName
FROM 
    sys.tables t
INNER JOIN 
    sys.schemas s ON t.schema_id = s.schema_id
INNER JOIN 
    sys.indexes i ON t.OBJECT_ID = i.object_id
INNER JOIN 
    sys.partitions p ON i.object_id = p.OBJECT_ID AND i.index_id = p.index_id
GROUP BY 
    t.Name, s.Name
HAVING 
    SUM(p.Rows) = 0
ORDER BY 
    TableName;

-- 4. List top 3 tables that have most relationships to other tables
SELECT TOP 3
    t.NAME AS TableName,
    s.Name AS SchemaName,
    COUNT(fk.object_id) AS RelationshipCount
FROM 
    sys.tables t
INNER JOIN 
    sys.schemas s ON t.schema_id = s.schema_id
LEFT JOIN 
    sys.foreign_keys fk ON t.object_id = fk.parent_object_id OR t.object_id = fk.referenced_object_id
GROUP BY 
    t.Name, s.Name
ORDER BY 
    RelationshipCount DESC;

-- 5. [Query Store] List top 15 queries that have long running time
SELECT TOP 15
    q.query_id,
    qt.query_sql_text,
    rs.avg_duration / 1000 AS avg_duration_ms,
    rs.max_duration / 1000 AS max_duration_ms,
    rs.min_duration / 1000 AS min_duration_ms,
    rs.count_executions
FROM 
    sys.query_store_query q
JOIN 
    sys.query_store_query_text qt ON q.query_text_id = qt.query_text_id
JOIN 
    sys.query_store_plan p ON q.query_id = p.query_id
JOIN 
    sys.query_store_runtime_stats rs ON p.plan_id = rs.plan_id
ORDER BY 
    -- rs.max_duration DESC,
    rs.avg_duration DESC;


-- 6. [Query Store] List top 15 queries that have the most executions
SELECT TOP 15
    q.query_id,
    qt.query_sql_text,
    SUM(rs.count_executions) AS total_executions,
    AVG(rs.avg_duration) / 1000000 AS avg_duration_seconds
FROM 
    sys.query_store_query q
JOIN 
    sys.query_store_query_text qt ON q.query_text_id = qt.query_text_id
JOIN 
    sys.query_store_plan p ON q.query_id = p.query_id
JOIN 
    sys.query_store_runtime_stats rs ON p.plan_id = rs.plan_id
GROUP BY 
    q.query_id, qt.query_sql_text
ORDER BY 
    total_executions DESC;

-- 7. [Query Store] List top 15 queries that have more than 3 query plans
SELECT TOP 15
    q.query_id,
    qt.query_sql_text,
    COUNT(DISTINCT p.plan_id) AS plan_count
FROM 
    sys.query_store_query q
INNER JOIN 
    sys.query_store_query_text qt ON q.query_text_id = qt.query_text_id
JOIN 
    sys.query_store_plan p ON q.query_id = p.query_id
GROUP BY 
    q.query_id, qt.query_sql_text
HAVING 
    COUNT(DISTINCT p.plan_id) > 3
ORDER BY 
    plan_count DESC;
