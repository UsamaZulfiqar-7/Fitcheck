"""Curated lessons: SQL, Excel, Power BI, Pandas, Statistics."""
from core.content._base import Q, R, T, register

# =====================================================================================================
# SQL
# =====================================================================================================
SQL_TABLES = """
```sql
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    name        TEXT,
    city        TEXT
);
CREATE TABLE orders (
    order_id    INTEGER PRIMARY KEY,
    customer_id INTEGER,
    amount      REAL,
    order_date  TEXT
);
INSERT INTO customers VALUES (1,'Ayesha','Lahore'),(2,'Bilal','Karachi'),(3,'Chen','Lahore'),(4,'Dana','Islamabad');
INSERT INTO orders VALUES
 (101,1,250.00,'2024-01-05'),(102,1,100.00,'2024-01-20'),(103,2,75.50,'2024-02-02'),
 (104,3,300.00,'2024-02-14'),(105,3,50.00,'2024-03-01');
```
"""

register(
    "SQL", level="Beginner",
    overview=("SQL (Structured Query Language) is the standard language for asking questions of data stored in relational "
              "databases such as PostgreSQL, MySQL, SQLite and SQL Server. With a few keywords you can filter rows, "
              "summarise numbers and combine tables."),
    why=("Almost every data role starts with data in a database. Analysts use SQL to pull and summarise data, engineers "
         "use it to build pipelines, and many interviews include a SQL test."),
    prerequisites=["Comfort with tables/spreadsheets (rows and columns)", "No programming experience needed"],
    stages=[
        ("Stage 1: Fundamentals", [
            T("sql-what", "What is SQL and what is a relational database?", """
A **relational database** stores data in **tables**. A table has **columns** (fields such as `name`) and **rows**
(records such as one customer). Tables are linked with **keys**: `customer_id` in `orders` points to `customer_id`
in `customers`.

SQL is *declarative*: you describe **what** result you want, and the database decides **how** to get it.

Main statement families:
- `SELECT` - read data (what you will use most)
- `INSERT`, `UPDATE`, `DELETE` - change data
- `CREATE`, `ALTER`, `DROP` - define tables

**Try it:** install the free *DB Browser for SQLite* (or use the `sqlite3` command, or PostgreSQL) and keep it open while you read.
"""),
            T("sql-setup", "Create the practice tables", "Run this once. All examples in this path use these two tables.\n" + SQL_TABLES + """
After running it, `SELECT * FROM customers;` should show 4 rows and `SELECT * FROM orders;` should show 5 rows.
"""),
        ]),
        ("Stage 2: Core concepts", [
            T("sql-select-where", "SELECT, WHERE and ORDER BY", """
```sql
SELECT name, city
FROM customers
WHERE city = 'Lahore'
ORDER BY name;
```
**Result**

| name   | city   |
|--------|--------|
| Ayesha | Lahore |
| Chen   | Lahore |

How to read it: `FROM` chooses the table, `WHERE` keeps only matching rows, `SELECT` chooses the columns, `ORDER BY`
sorts (add `DESC` for descending). Useful filters: `=`, `<>`, `>`, `<`, `AND`, `OR`, `IN ('Lahore','Karachi')`,
`LIKE 'A%'`, `BETWEEN 100 AND 300`, `IS NULL`.
"""),
            T("sql-group-by", "Aggregates, GROUP BY and HAVING", """
Aggregate functions collapse many rows into one value: `COUNT`, `SUM`, `AVG`, `MIN`, `MAX`.

```sql
SELECT customer_id, COUNT(*) AS num_orders, SUM(amount) AS total
FROM orders
GROUP BY customer_id;
```
| customer_id | num_orders | total |
|---|---|---|
| 1 | 2 | 350.0 |
| 2 | 1 | 75.5 |
| 3 | 2 | 350.0 |

`GROUP BY` makes one output row per customer. To filter **groups** use `HAVING` (it runs *after* grouping):

```sql
SELECT customer_id, SUM(amount) AS total
FROM orders
GROUP BY customer_id
HAVING SUM(amount) > 300;
```
Result: customers 1 and 3 (both total 350). Customer 2 (75.5) is removed.

**WHERE vs HAVING:** `WHERE` filters rows *before* grouping, `HAVING` filters groups *after* aggregation.
"""),
        ]),
        ("Stage 3: Practical examples", [
            T("sql-joins", "JOINs: combining tables", """
```sql
SELECT c.name, o.order_id, o.amount
FROM customers c
INNER JOIN orders o ON c.customer_id = o.customer_id;
```
`INNER JOIN` keeps only rows that match in both tables, so you get 5 rows (one per order):

| name | order_id | amount |
|---|---|---|
| Ayesha | 101 | 250.0 |
| Ayesha | 102 | 100.0 |
| Bilal | 103 | 75.5 |
| Chen | 104 | 300.0 |
| Chen | 105 | 50.0 |

Dana has no orders, so she is missing. A `LEFT JOIN` keeps **all** rows of the left table:

```sql
SELECT c.name, o.order_id
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
WHERE o.order_id IS NULL;
```
Result: **Dana** (the customer without orders). This "LEFT JOIN + IS NULL" pattern finds missing relationships.
"""),
            T("sql-combine", "Putting it together: a small report", """
Total sales per city, highest first:

```sql
SELECT c.city, SUM(o.amount) AS total_sales
FROM customers c
JOIN orders o ON o.customer_id = c.customer_id
GROUP BY c.city
ORDER BY total_sales DESC;
```
| city | total_sales |
|---|---|
| Lahore | 700.0 |
| Karachi | 75.5 |

Lahore = Ayesha 350 + Chen 350. Islamabad does not appear because Dana has no orders (inner join).

Order of writing: `SELECT ... FROM ... JOIN ... WHERE ... GROUP BY ... HAVING ... ORDER BY ... LIMIT`.
"""),
        ]),
        ("Stage 4: Hands-on exercises", [
            T("sql-hands-on", "Do the exercises", """
Open the **Practice** tab of this skill and solve all questions on your own database *before* revealing the solutions.

Tips:
1. Run the query after every small change.
2. If the result looks wrong, run the query without `GROUP BY`/`WHERE` first to see the raw rows.
3. Compare your result with the expected output in the solution, not only the query text - different queries can be correct.

Extra practice (free, interactive): SQLBolt and SQLZoo (see Resources).
"""),
        ]),
        ("Stage 5: Revision and self-assessment", [
            T("sql-revision", "Cheat sheet and common mistakes", """
**Cheat sheet:** `SELECT` columns -> `FROM` table -> `JOIN` more tables -> `WHERE` filter rows -> `GROUP BY` -> `HAVING` filter groups
-> `ORDER BY` -> `LIMIT`.

**Common mistakes**
- Using `= NULL` instead of `IS NULL`.
- Selecting a column that is not in `GROUP BY` and not aggregated (error in most databases).
- Using `WHERE SUM(amount) > 300` - aggregates need `HAVING`.
- Forgetting the `ON` condition in a join, which multiplies rows.
- Comparing text with the wrong case or spacing (`'lahore'` vs `'Lahore'` can differ).

**Self-check:** can you explain INNER vs LEFT JOIN and WHERE vs HAVING without notes? If yes, mark this path complete.
"""),
        ]),
    ],
    practice=[
        Q("Write a query that returns order_id and amount for orders above 100, largest first.",
          "Use WHERE and ORDER BY ... DESC.",
          "```sql\nSELECT order_id, amount FROM orders WHERE amount > 100 ORDER BY amount DESC;\n```\nExpected: 104 (300.0), 101 (250.0). Order 102 has exactly 100, which is not > 100."),
        Q("Which customers placed MORE THAN ONE order? Use GROUP BY and HAVING.",
          "Group orders by customer_id and filter with HAVING COUNT(*) > 1.",
          "```sql\nSELECT customer_id, COUNT(*) AS num_orders\nFROM orders\nGROUP BY customer_id\nHAVING COUNT(*) > 1;\n```\nExpected: customer 1 (2 orders) and customer 3 (2 orders)."),
        Q("Show the total amount spent per city. Which city is first?",
          "Join customers and orders, then group by city.",
          "```sql\nSELECT c.city, SUM(o.amount) AS total\nFROM customers c JOIN orders o ON o.customer_id = c.customer_id\nGROUP BY c.city ORDER BY total DESC;\n```\nLahore is first with 700.0, then Karachi with 75.5."),
        Q("Find customers who have never placed an order.",
          "LEFT JOIN orders and keep rows where the order side is NULL.",
          "```sql\nSELECT c.name\nFROM customers c LEFT JOIN orders o ON o.customer_id = c.customer_id\nWHERE o.order_id IS NULL;\n```\nExpected: Dana."),
        Q("What is the average order amount? (Calculate it by hand first.)",
          "AVG(amount). Sum is 775.5 across 5 orders.",
          "```sql\nSELECT AVG(amount) FROM orders;\n```\n(250 + 100 + 75.5 + 300 + 50) / 5 = 775.5 / 5 = **155.1**."),
        Q("Explain the difference between WHERE and HAVING in one or two sentences.",
          "Think about when each runs.",
          "WHERE filters individual rows before grouping and cannot use aggregates. HAVING filters groups after GROUP BY and can use aggregate functions such as SUM() or COUNT()."),
    ],
    resources=[
        R("SQLBolt - interactive SQL lessons", "https://sqlbolt.com/", "interactive"),
        R("SQLZoo - interactive SQL tutorial", "https://sqlzoo.net/", "interactive"),
        R("W3Schools SQL tutorial", "https://www.w3schools.com/sql/", "tutorial"),
        R("PostgreSQL official tutorial", "https://www.postgresql.org/docs/current/tutorial.html", "docs"),
        R("SQLite official documentation", "https://www.sqlite.org/docs.html", "docs"),
    ],
)

# =====================================================================================================
# EXCEL
# =====================================================================================================
register(
    "Excel", level="Beginner",
    overview=("Microsoft Excel is a spreadsheet application used to store, clean, calculate, summarise and chart data. "
              "Formulas, lookups and PivotTables make it one of the most common tools in business analytics."),
    why=("Most business teams share data in Excel. Analyst roles expect you to clean data, use lookup formulas, build "
         "PivotTables and charts quickly."),
    prerequisites=["Basic computer skills", "Having Excel (or free Excel for the web / LibreOffice Calc)"],
    stages=[
        ("Stage 1: Fundamentals", [
            T("xl-basics", "Workbook, cells and references", """
A **workbook** contains **sheets**; a sheet is a grid of **cells** such as `B3` (column B, row 3). A formula always starts
with `=`.

- **Relative reference** `A1` changes when you copy the formula down/right.
- **Absolute reference** `$A$1` never changes (press **F4** to toggle).
- **Mixed** `$A1` or `A$1` locks only the column or row.

Example: in `C2` type `=A2*B2` (quantity x price) and drag the fill handle down - Excel changes it to `=A3*B3`, `=A4*B4` ...
Convert your range to a **Table** (Ctrl+T) so formulas and filters expand automatically.
"""),
        ]),
        ("Stage 2: Core concepts", [
            T("xl-formulas", "Core formulas: SUM, IF, COUNTIF, SUMIF", """
Assume sales data: `A2:A7` = Region, `B2:B7` = Amount with values East 100, West 200, East 150, West 50, East 100, West 100.

| Goal | Formula | Result |
|---|---|---|
| Total | `=SUM(B2:B7)` | 700 |
| Average | `=AVERAGE(B2:B7)` | 116.67 |
| Orders above 100 | `=COUNTIF(B2:B7,">100")` | 2 |
| Total for East | `=SUMIF(A2:A7,"East",B2:B7)` | 350 |
| Label big orders | `=IF(B2>=150,"Big","Small")` | Small (for 100) |

`IF(test, value_if_true, value_if_false)` is the basis of most decision logic. Combine tests with `AND()` / `OR()`.
Tip: text in formulas goes inside double quotes, and criteria like `">100"` are text too.
"""),
            T("xl-clean", "Sorting, filtering and cleaning data", """
- **Sort & Filter:** Data -> Sort / Filter.
- **Remove duplicates:** Data -> Remove Duplicates.
- **TRIM** removes extra spaces: `=TRIM(A2)`. **PROPER/UPPER/LOWER** fix case.
- **Text to Columns** splits "Lahore, Pakistan" into two columns.
- **Data Validation** (Data -> Data Validation) limits what can be typed, for example a drop-down list.

Always keep a copy of the raw data on its own sheet and clean a copy.
"""),
        ]),
        ("Stage 3: Practical examples", [
            T("xl-lookup", "Lookup formulas: VLOOKUP, XLOOKUP, INDEX/MATCH", """
A lookup finds a value in a table using a key. Suppose `Products!A:B` holds product id (A) and price (B), and `D2` holds id `P102`.

```
=VLOOKUP(D2, Products!A:B, 2, FALSE)
```
Arguments: *lookup value*, *table range* (key must be in the **first** column), *column number to return*, and `FALSE` for an **exact** match.
If the id is missing Excel returns `#N/A`; wrap it: `=IFERROR(VLOOKUP(...), "Not found")`.

Modern alternative (Microsoft 365 / Excel 2021):
```
=XLOOKUP(D2, Products!A:A, Products!B:B, "Not found")
```
`XLOOKUP` can look left, defaults to exact match, and has a built-in "not found" value.

Older but flexible: `=INDEX(Products!B:B, MATCH(D2, Products!A:A, 0))` - `MATCH(...,0)` finds the row, `INDEX` returns the value.
"""),
            T("xl-pivot", "PivotTables and charts", """
A **PivotTable** summarises a table without writing formulas: Insert -> PivotTable, then drag fields:
- **Rows:** Region
- **Values:** Sum of Amount
- **Columns / Filters:** Month, Product ...

Using the example sales data the pivot shows East = 350, West = 350, Grand Total = 700. Refresh it (Data -> Refresh All) after the data changes.
Create a chart from the PivotTable (PivotChart). Choose chart types by purpose: **column/bar** to compare categories, **line** for trends over time, **pie** only for a few parts of a whole.
"""),
        ]),
        ("Stage 4: Hands-on exercises", [
            T("xl-hands-on", "Build a small sales workbook", """
1. Create a sheet with Date, Region, Product, Quantity, Price.
2. Add a `Revenue` column (`=Quantity*Price`).
3. Convert to a Table and add a lookup that fills the product category from a second sheet.
4. Build a PivotTable of revenue by region and month, and a column chart.
5. Add a drop-down (Data Validation) for Region in new rows.

Then answer the questions in the **Practice** tab.
"""),
        ]),
        ("Stage 5: Revision and self-assessment", [
            T("xl-revision", "Common mistakes and checklist", """
- Numbers stored as text (left-aligned) break `SUM` - convert with *Text to Columns* or `=VALUE()`.
- VLOOKUP with `TRUE` (approximate match) on unsorted data gives wrong answers - use `FALSE`.
- Forgetting `$` when copying a formula that must stay fixed.
- Hard-coding numbers inside formulas instead of referencing cells.
- Merging cells in data tables (breaks sorting and pivots).

Checklist: relative vs absolute references, IF/COUNTIF/SUMIF, one lookup formula, PivotTable, chart. If you can do all five, mark the path complete.
"""),
        ]),
    ],
    practice=[
        Q("Explain how to look up a product price from another sheet using a product id.",
          "Use a lookup formula with an exact match.",
          "`=VLOOKUP(id, Products!A:B, 2, FALSE)` or `=XLOOKUP(id, Products!A:A, Products!B:B, \"Not found\")`. The last argument of VLOOKUP must be FALSE for an exact match; the key must be in the first column of the table."),
        Q("With Region in A2:A7 and Amount in B2:B7, write a formula for the total amount of region \"West\".",
          "SUMIF(range, criteria, sum_range).",
          "`=SUMIF(A2:A7,\"West\",B2:B7)`. With the sample values (200 + 50 + 100) the result is **350**."),
        Q("What is the difference between $A$1 and A1 when you copy a formula?",
          "Think about what stays fixed.",
          "`A1` is relative and shifts when copied. `$A$1` is absolute and always points to the same cell. Use absolute references for constants such as a tax rate cell."),
        Q("Write an IF formula that returns \"Pass\" when B2 >= 50 and \"Fail\" otherwise.",
          "IF(test, true, false).",
          "`=IF(B2>=50,\"Pass\",\"Fail\")`"),
        Q("When should you use a PivotTable instead of formulas?",
          "Think about quick summaries by category.",
          "When you need to summarise large tables by categories (sum/count/average by region, month...) and want to change the grouping quickly by dragging fields, without writing a formula for every combination."),
    ],
    resources=[
        R("Microsoft Excel help and training", "https://support.microsoft.com/en-us/excel", "docs"),
        R("Exceljet - formulas and functions explained", "https://exceljet.net/", "tutorial"),
        R("Excel Easy - free Excel tutorial", "https://www.excel-easy.com/", "tutorial"),
    ],
)

# =====================================================================================================
# POWER BI
# =====================================================================================================
register(
    "Power BI", level="Beginner",
    overview=("Power BI is Microsoft's business-intelligence tool. You connect to data, clean it with Power Query, model it with "
              "relationships, calculate with DAX, and publish interactive reports and dashboards."),
    why=("Analyst and BI roles use Power BI to turn raw tables into dashboards that managers read every day. Knowing the "
         "data model and DAX measures is what separates beginners from job-ready candidates."),
    prerequisites=["Basic Excel", "Basic understanding of tables and relationships (SQL knowledge helps)",
                   "Windows PC (Power BI Desktop is free for Windows)"],
    stages=[
        ("Stage 1: Fundamentals", [
            T("pbi-overview", "Power BI components and workflow", """
Power BI has three main parts:
- **Power BI Desktop** (Windows, free): build the report and data model.
- **Power BI Service** (online): publish, share, schedule refresh, build dashboards.
- **Mobile apps**: view reports.

Typical workflow: **Get data -> Transform (Power Query) -> Model (relationships) -> Measures (DAX) -> Visualise -> Publish**.

Install Power BI Desktop from the Microsoft Store or the official download page and open a blank report.
"""),
        ]),
        ("Stage 2: Core concepts", [
            T("pbi-powerquery", "Get data and clean it with Power Query", """
Home -> **Get data** (Excel, CSV, SQL Server...) -> **Transform data** opens Power Query. Every action is recorded as an
**Applied Step** that replays whenever data refreshes. Common steps: change data types, remove duplicates, fill down,
split columns, filter rows, merge/append queries, unpivot columns.

Rule of thumb: **clean data in Power Query, calculate in DAX**. Use *Column profile* (View tab) to spot nulls and errors.
"""),
            T("pbi-model", "Data model and relationships (star schema)", """
Good models use a **star schema**: one central **fact table** (events such as `Sales` with amounts and keys) surrounded by **dimension tables**
(`Customer`, `Product`, `Date`). Relationships are normally **one-to-many** (one product -> many sales) with filtering flowing from the
dimension (one side) to the fact (many side).

Why it matters: filters on a dimension (e.g. choose a year in a slicer) automatically filter the fact table, and DAX stays simple and fast.
Build it in *Model view* by dragging key columns between tables, and mark your calendar table as a **Date table**.
"""),
        ]),
        ("Stage 3: Practical examples", [
            T("pbi-dax", "DAX basics: calculated columns vs measures", """
**Calculated column** - computed row by row when data is refreshed and stored in the model:
```
Line Total = Sales[Quantity] * Sales[UnitPrice]
```
**Measure** - calculated at query time, responding to the filters in the visual (**filter context**):
```
Total Sales = SUM(Sales[Line Total])
Sales 2024  = CALCULATE([Total Sales], 'Date'[Year] = 2024)
```
Use measures for numbers you aggregate (totals, ratios, averages) and calculated columns only when you need a value per row to slice or filter by.
`CALCULATE` changes the filter context; it is the most important DAX function. Example: if a table visual shows **Region = East**, `[Total Sales]` returns the East total automatically.
"""),
        ]),
        ("Stage 4: Hands-on exercises", [
            T("pbi-report", "Build and publish a report", """
1. Import a small sales CSV and a products CSV; clean data types in Power Query.
2. Create a Date table (`CALENDARAUTO()` or import one) and relate Sales -> Product and Sales -> Date.
3. Create measures: `Total Sales`, `Orders = COUNTROWS(Sales)`, `Average Order = DIVIDE([Total Sales],[Orders])`.
4. Build visuals: card (Total Sales), clustered column (Sales by Product), line chart (Sales by Month), slicer (Year).
5. Format: consistent colours, titles, no clutter. Publish to the Service if you have a work/school account.

Then do the **Practice** questions.
"""),
        ]),
        ("Stage 5: Revision and self-assessment", [
            T("pbi-revision", "Import vs DirectQuery and common mistakes", """
- **Import mode** loads a copy of the data into Power BI (fast, needs scheduled refresh). **DirectQuery** sends queries to the source at run time (always current, usually slower, limited DAX/transform options).
- Mistake: using many-to-many relationships or one flat wide table instead of a star schema.
- Mistake: creating calculated columns for what should be a measure.
- Mistake: using `/` for division - use `DIVIDE()` to avoid divide-by-zero errors.
- Mistake: too many visuals on a page; keep one clear message per page.
"""),
        ]),
    ],
    practice=[
        Q("What is the difference between a calculated column and a measure in Power BI?",
          "When is each one calculated?",
          "A calculated column is evaluated row by row during data refresh and stored in the model, so it uses memory. A measure is evaluated when a visual is rendered, using the current filter context, and is not stored per row. Use measures for aggregations such as totals and ratios."),
        Q("Why is a star schema recommended?",
          "Think of fact vs dimension tables and filtering.",
          "It separates numeric events (fact table) from descriptive attributes (dimension tables), gives simple one-to-many relationships, makes DAX easier, improves performance and avoids ambiguous filter paths."),
        Q("Write a measure that returns total sales and a second one that divides total sales by the number of orders safely.",
          "SUM, COUNTROWS and DIVIDE.",
          "```\nTotal Sales = SUM(Sales[Line Total])\nOrders = COUNTROWS(Sales)\nAverage Order = DIVIDE([Total Sales], [Orders])\n```\nDIVIDE returns blank (or an alternate result) instead of an error when Orders is 0."),
        Q("Explain filter context with an example.",
          "What happens when a slicer or a chart category is selected?",
          "Filter context is the set of filters applied to a calculation by slicers, rows/columns of a visual and report filters. If a bar chart shows Region = East, the measure Total Sales is evaluated only on East rows, so the same measure returns different values in each bar."),
        Q("When would you choose Import mode over DirectQuery?",
          "Compare speed and freshness.",
          "Import is usually best: it is fast and supports full DAX/Power Query features. DirectQuery is for very large data or when you must see near-real-time data, accepting slower visuals and some feature limits."),
    ],
    resources=[
        R("Microsoft Learn - Power BI documentation", "https://learn.microsoft.com/en-us/power-bi/", "docs"),
        R("Microsoft Learn - Get started with Power BI Desktop", "https://learn.microsoft.com/en-us/power-bi/fundamentals/desktop-getting-started", "tutorial"),
        R("Microsoft Learn - DAX reference", "https://learn.microsoft.com/en-us/dax/", "docs"),
    ],
)

# =====================================================================================================
# PANDAS
# =====================================================================================================
register(
    "Pandas", level="Beginner",
    overview=("pandas is the main Python library for working with tables of data. Its core objects are the Series (one column) "
              "and the DataFrame (a table) with fast tools for loading, cleaning, filtering, grouping and merging."),
    why=("Data analysts and data scientists use pandas daily for cleaning and exploring datasets before charts or models."),
    prerequisites=["Python basics (variables, lists, dictionaries, functions)", "pip install pandas"],
    stages=[
        ("Stage 1: Fundamentals", [
            T("pd-basics", "Series, DataFrame and loading data", """
```python
import pandas as pd

df = pd.DataFrame({
    "city":  ["Lahore", "Karachi", "Lahore", "Islamabad"],
    "sales": [250, 75, 300, 120],
})
print(df)
```
Output:
```
        city  sales
0     Lahore    250
1    Karachi     75
2     Lahore    300
3  Islamabad    120
```
Load files with `pd.read_csv("file.csv")` or `pd.read_excel("file.xlsx")`. First look at data with `df.head()`, `df.info()` (types, missing values) and `df.describe()` (summary statistics).
"""),
        ]),
        ("Stage 2: Core concepts", [
            T("pd-select", "Selecting and filtering", """
```python
df["sales"]                      # one column (Series)
df[["city", "sales"]]            # several columns
df.loc[0, "city"]                # by label -> 'Lahore'
df.iloc[1]                       # by position (second row)
df[df["sales"] > 100]            # boolean filter
df[(df["city"] == "Lahore") & (df["sales"] > 260)]
```
Last line returns only the row with 300 sales (Lahore). Use `&` (and), `|` (or), `~` (not) with **parentheses** around each condition.
Add a column: `df["tax"] = df["sales"] * 0.1`.
"""),
        ]),
        ("Stage 3: Practical examples", [
            T("pd-groupby", "groupby, missing values and merge", """
```python
print(df.groupby("city")["sales"].sum())
```
Output:
```
city
Islamabad    120
Karachi       75
Lahore       550
Name: sales, dtype: int64
```
**Missing values:** `df.isna().sum()` counts them; `df.dropna()` removes rows; `df["sales"].fillna(0)` fills them.

**Merge** (like SQL JOIN):
```python
managers = pd.DataFrame({"city": ["Lahore", "Karachi"], "manager": ["Sara", "Omar"]})
merged = df.merge(managers, on="city", how="left")
```
`how="left"` keeps all rows of `df`; Islamabad gets `NaN` as manager because it has no match.
"""),
        ]),
        ("Stage 4: Hands-on exercises", [
            T("pd-hands-on", "Analyse a real CSV", """
1. Download any small CSV (for example a sales or weather dataset from Kaggle or your own Excel exported as CSV).
2. Inspect it with `head`, `info`, `describe`.
3. Clean it: fix data types, handle missing values, remove duplicates (`df.drop_duplicates()`).
4. Answer 3 business questions with `groupby`, filtering and sorting (`df.sort_values("sales", ascending=False)`).
5. Save the result with `df.to_csv("clean.csv", index=False)`.

Then complete the **Practice** tab.
"""),
        ]),
        ("Stage 5: Revision and self-assessment", [
            T("pd-revision", "Common mistakes", """
- Chained assignment (`df[df.a > 1]["b"] = 0`) does not change `df` - use `df.loc[df.a > 1, "b"] = 0`.
- Using `and`/`or` instead of `&`/`|` in filters raises an error.
- Forgetting that most methods return a **new** DataFrame instead of modifying in place.
- Reading dates as text: use `pd.to_datetime(df["date"])`.
- Looping over rows when a vectorised operation (`df["a"] * df["b"]`) is shorter and much faster.
"""),
        ]),
    ],
    practice=[
        Q("Given a DataFrame df with columns city and sales, write code to get the average sales per city.",
          "groupby + mean.",
          "```python\ndf.groupby(\"city\")[\"sales\"].mean()\n```\nFor the sample data: Islamabad 120.0, Karachi 75.0, Lahore 275.0."),
        Q("Select rows where sales are greater than 100 AND the city is Lahore.",
          "Use & and parentheses.",
          "```python\ndf[(df[\"sales\"] > 100) & (df[\"city\"] == \"Lahore\")]\n```"),
        Q("How do you find how many missing values each column has?",
          "isna and sum.",
          "```python\ndf.isna().sum()\n```"),
        Q("What is the difference between loc and iloc?",
          "Labels vs positions.",
          "`loc` selects by label (row/column names, inclusive slices); `iloc` selects by integer position (exclusive end like normal Python slices)."),
        Q("Join two DataFrames orders and customers on customer_id keeping all orders.",
          "merge with how='left'.",
          "```python\norders.merge(customers, on=\"customer_id\", how=\"left\")\n```"),
    ],
    resources=[
        R("pandas - 10 minutes to pandas", "https://pandas.pydata.org/docs/user_guide/10min.html", "docs"),
        R("Kaggle Learn - Pandas (free micro-course)", "https://www.kaggle.com/learn/pandas", "interactive"),
        R("pandas user guide", "https://pandas.pydata.org/docs/user_guide/index.html", "docs"),
    ],
)

# =====================================================================================================
# STATISTICS
# =====================================================================================================
register(
    "Statistics", level="Intermediate",
    overview=("Statistics is the science of collecting, summarising and drawing conclusions from data. Descriptive statistics "
              "summarise what you have; inferential statistics (sampling, confidence intervals, hypothesis tests) help you make "
              "decisions about a larger population."),
    why=("Analysts and data scientists must judge whether a difference is real or random, choose the right averages, and avoid "
         "misleading conclusions. Statistics also underpins machine learning."),
    prerequisites=["School-level algebra", "Basic Python or Excel is helpful for practice"],
    stages=[
        ("Stage 1: Fundamentals", [
            T("st-descriptive", "Mean, median, mode and spread", """
Use this small dataset throughout: `2, 4, 4, 4, 5, 5, 7, 9`.

- **Mean** = sum / count = 40 / 8 = **5**
- **Median** (middle value) = (4 + 5) / 2 = **4.5**
- **Mode** (most frequent) = **4**
- **Range** = 9 - 2 = 7
- **Variance** (population) = average squared distance from the mean = (9+1+1+1+0+0+4+16)/8 = 32/8 = **4**
- **Standard deviation** = sqrt(4) = **2**
- For a *sample*, divide by n-1: variance = 32/7 ≈ **4.57**, standard deviation ≈ **2.14**.

```python
import statistics as st
data = [2, 4, 4, 4, 5, 5, 7, 9]
print(st.mean(data), st.median(data), st.mode(data))   # 5 4.5 4
print(st.pstdev(data), round(st.stdev(data), 2))       # 2.0 2.14
```
**Which average?** Use the **median** when data has outliers (incomes, house prices); the mean is pulled by extreme values.
"""),
        ]),
        ("Stage 2: Core concepts", [
            T("st-distribution", "Distributions and the normal curve", """
A **distribution** shows how often each value occurs. The **normal distribution** is bell-shaped and symmetric around the mean.
The *empirical rule*: about **68%** of values lie within 1 standard deviation of the mean, **95%** within 2 and **99.7%** within 3.

A **z-score** = (value - mean) / standard deviation. With mean 5 and sd 2, the value 9 has z = 2, i.e. it is 2 standard deviations above average (unusually high).
Always plot a histogram first; many real datasets are skewed, not normal.
"""),
            T("st-correlation", "Correlation and regression idea", """
**Correlation** (r, from -1 to +1) measures how strongly two numeric variables move together in a straight line. r = +0.9 means a strong positive relationship, 0 means no linear relationship.

**Correlation does not mean causation:** ice-cream sales and sunburn are correlated because both rise in summer.
Simple linear regression fits a line `y = a + b*x`; `b` is the average change in y for one extra unit of x.
"""),
        ]),
        ("Stage 3: Practical examples", [
            T("st-sampling", "Sampling and confidence intervals", """
We rarely see the whole **population**, so we use a **sample**. Larger, random samples give more reliable estimates. The **standard error** of a mean is `s / sqrt(n)`.

A **95% confidence interval** for a mean is roughly `mean ± 2 × standard error` for reasonably large samples.
Example: sample mean 50, s = 10, n = 100 -> standard error = 1 -> interval ≈ **48 to 52**.
Interpretation: if we repeated the sampling many times, about 95% of such intervals would contain the true mean. It does **not** mean there is a 95% chance this one contains it in a casual sense - avoid over-claiming.
"""),
            T("st-hypothesis", "Hypothesis tests and p-values", """
1. State the **null hypothesis (H0)**: no effect/difference. The alternative (H1): there is one.
2. Choose a significance level, commonly **α = 0.05**.
3. Compute a test statistic (t-test for means, chi-square for categories) and its **p-value**.
4. If **p < α**, the data would be unlikely under H0, so we reject H0.

**p-value** = the probability of seeing results at least this extreme **if H0 were true**. It is *not* the probability that H0 is true and not the size of the effect.
**Errors:** Type I = rejecting a true H0 (false alarm, probability α); Type II = failing to reject a false H0 (missed effect).
```python
from scipy import stats
a = [23, 25, 27, 30, 31]
b = [30, 33, 34, 36, 38]
print(stats.ttest_ind(a, b))   # small p-value -> means likely differ
```
"""),
        ]),
        ("Stage 4: Hands-on exercises", [
            T("st-hands-on", "Analyse a dataset", """
Choose a small dataset (for example student marks or sales). In Excel or pandas:
1. Compute mean, median, standard deviation and draw a histogram.
2. Find outliers with z-scores or the IQR rule.
3. Compare two groups (for example Class A vs Class B) with a t-test and write 3 sentences interpreting the result in plain language.
4. Compute the correlation between two columns and state one reason why causation might not hold.

Then answer the **Practice** questions.
"""),
        ]),
        ("Stage 5: Revision and self-assessment", [
            T("st-revision", "Common mistakes", """
- Reporting only the mean for skewed data.
- Treating "p < 0.05" as proof or as importance of the effect.
- Running many tests and reporting only the significant one (p-hacking).
- Confusing correlation with causation.
- Small or biased samples (for example surveying only your friends).
"""),
        ]),
    ],
    practice=[
        Q("Compute the mean, median and mode of 3, 5, 5, 7, 20. Which average best describes the typical value?",
          "Order the numbers; look at the outlier 20.",
          "Mean = 40/5 = 8; median = 5; mode = 5. The median (5) describes the typical value better because 20 is an outlier that pulls the mean up."),
        Q("Explain what a p-value of 0.03 means.",
          "Assume the null hypothesis is true.",
          "If the null hypothesis were true, there would be about a 3% chance of seeing a result at least as extreme as the observed one. At α = 0.05 we would reject H0, but this does not prove the alternative nor show the effect is large."),
        Q("A sample of 100 users has mean spend 50 and standard deviation 10. Give an approximate 95% confidence interval.",
          "Standard error = s / sqrt(n).",
          "SE = 10/√100 = 1, so the interval is about 50 ± 2×1 = **48 to 52**."),
        Q("Why does correlation not imply causation? Give an example.",
          "Think about a hidden third variable.",
          "Two variables can move together because of a third factor (confounder) or by chance. Example: ice-cream sales and drowning incidents both rise in summer because of hot weather, not because ice cream causes drowning."),
        Q("What are Type I and Type II errors?",
          "False alarm vs missed detection.",
          "Type I: rejecting a true null hypothesis (false positive). Type II: failing to reject a false null hypothesis (false negative)."),
    ],
    resources=[
        R("Khan Academy - Statistics and probability", "https://www.khanacademy.org/math/statistics-probability", "course"),
        R("OpenIntro Statistics (free textbook)", "https://www.openintro.org/book/os/", "book"),
        R("Python statistics module documentation", "https://docs.python.org/3/library/statistics.html", "docs"),
    ],
)
