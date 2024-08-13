## Problem 1. Explore Database

You need to run query to answer following question:

1. How many tables are there
2. List all tables size
3. List tables that have zero record
4. List top 3 tables have most relationship to other tables
5. [Query Store] List top 15 queries have long time running
   a. Write a small paragraph analyze first top 5 query caused long time running, how
   could it improve
6. [Query Store] List top 15 queries have most execution
7. [Query Store] List top 15 queries more than 3 query plans

## Problem 2. Utilize Python SQLAlchemy and others for advanced analysis

1. Visualize tables size
2. These tables some of them are not naming convention yet, the standard is Snake_Pascal_Case style, write a function in python to list them out
3. For 3 Query Store queries in Problem 1, aggregate to find query text that exists across those 3
