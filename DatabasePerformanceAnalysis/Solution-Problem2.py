import pandas as pd
import matplotlib.pyplot as plt
import re
from collections import Counter
import pyodbc
from azure.identity import DefaultAzureCredential
import struct


# Azure SQL Database connection details
connection_string = 'Driver={ODBC Driver 17 for SQL Server};Server=tcp:nonprod-sql.workforceoptimizer.com,1433;Database=Candidate_DB;Encrypt=yes;TrustServerCertificate=yes;Connection Timeout=30'

# Create a DB connection
def create_connection():
    credential = DefaultAzureCredential(exclude_interactive_browser_credential=False)
    token_bytes = credential.get_token("https://database.windows.net/.default").token.encode("UTF-16-LE")
    token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)
    SQL_COPT_SS_ACCESS_TOKEN = 1256  # This connection option is defined by microsoft in msodbcsql.h
    conn = pyodbc.connect(connection_string, attrs_before={SQL_COPT_SS_ACCESS_TOKEN: token_struct})
    return conn

conn = create_connection()

# 1. Visualize tables size
def visualize_table_sizes():
    query = """
    SELECT TOP 20
        (s.Name + '.'+ t.name) AS TableName,
        (SUM(a.total_pages) * 8) / 1024 AS TotalSpaceMB, 
        (SUM(a.used_pages) * 8) / 1024 AS UsedSpaceMB, 
        ((SUM(a.total_pages) - SUM(a.used_pages)) * 8) /1024 AS UnusedSpaceMB
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
        TotalSpaceMB DESC;
    """
    
    df = pd.read_sql(query, conn)
    df_sorted = df.sort_values('TotalSpaceMB', ascending=True)
    # Create horizontal bar chart
    fig, ax = plt.subplots(figsize=(12, 10))

    ax.barh(df_sorted['TableName'], df_sorted['UsedSpaceMB'], label='Used Space', color='#1f77b4')
    ax.barh(df_sorted['TableName'], df_sorted['UnusedSpaceMB'], left=df_sorted['UsedSpaceMB'], label='Unused Space', color='#ff7f0e')
    
    # Customize the chart
    ax.set_xlabel('Space (MB)')
    ax.set_title('Top 20 Tables by Size')
    ax.legend()
    
    # Add total size labels at the end of each bar
    for i, v in enumerate(df_sorted['TotalSpaceMB']):
        ax.text(v, i, f' {v:.2f}MB', va='center')
    
    # plt.tight_layout()
    fig.savefig('Output_1-viz_table_sizes.png')
    # plt.show()
    # Save the plot to a png file

# 2. List tables not following the Snake_Pascal_Case naming convention
def list_non_standard_tables():
    query = "SELECT name FROM sys.tables"
    df = pd.read_sql(query, conn)
    
    def is_snake_pascal_case(name):
        return re.match(r'^([A-Z][a-z0-9]+)(_[A-Z][a-z0-9]+)*$', name) is not None
    
    non_standard_tables = [name for name in df['name'] if not is_snake_pascal_case(name)]
    
    # Output the non-standard tables to text file
    with open('Output_2-non_standard_tables.txt', 'w') as f:
        for table in non_standard_tables:
            f.write(table + '\n')


# 3. Aggregate query text across the three Query Store queries
def aggregate_query_store_queries():   
    # Queries for Problem 1
    long_running_query = """
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
            rs.avg_duration DESC
    """
    
    most_executed_query = """
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
            total_executions DESC
    """
    
    multiple_plans_query = """
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
            plan_count DESC
    """
    
    top_15_long_running = pd.read_sql(long_running_query, conn)
    top_15_most_executed = pd.read_sql(most_executed_query, conn)
    top_15_multiple_plans = pd.read_sql(multiple_plans_query, conn)
        
    # Combine all query texts
    all_queries = (
        list(top_15_long_running['query_sql_text']) +
        list(top_15_most_executed['query_sql_text']) +
        list(top_15_multiple_plans['query_sql_text'])
    )
    
    # Count occurrences
    query_counts = Counter(all_queries)
    
    # Output queries that appear more than once to text file
    with open('Output_3-query_counts.txt', 'w') as f:
        for query, count in query_counts.items():
            if count > 1:
                f.write(str(count) + ';' + query.replace("\n", "") + '\n')

# Run the functions
visualize_table_sizes()
list_non_standard_tables()
aggregate_query_store_queries()
conn.close()