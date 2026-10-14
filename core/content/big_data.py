"""Curated lessons: Hadoop, Spark, Kafka."""
from core.content._base import Q, R, T, register

# =====================================================================================================
# HADOOP
# =====================================================================================================
register(
    "Hadoop", level="Intermediate",
    overview=("Apache Hadoop is an open-source framework for storing and processing very large datasets on clusters of ordinary "
              "computers. Its main parts are HDFS (distributed storage), YARN (resource management) and MapReduce (batch processing)."),
    why=("Big data roles expect you to understand how data is stored and processed across many machines, and Hadoop's ideas "
         "(blocks, replication, map and reduce) are the foundation of modern tools such as Spark and Hive."),
    prerequisites=["Basic Linux commands", "Basic Python or Java", "Java installed; on Windows use WSL 2 or Docker"],
    stages=[
        ("Stage 1: Fundamentals", [
            T("hd-bigdata", "Big data and the Hadoop ecosystem", """
Big data is often described with the **3 Vs**: **Volume** (huge size), **Velocity** (fast arrival) and **Variety** (many formats).
One computer cannot store or process it quickly, so Hadoop splits the work across many machines.

Core components:
- **HDFS** - Hadoop Distributed File System (storage).
- **YARN** - allocates cluster CPU/memory to applications.
- **MapReduce** - programming model for batch processing.
- Ecosystem tools: **Hive** (SQL on Hadoop), **HBase**, **Spark**, **Sqoop**, **Oozie**/**Airflow**.

Key idea: **move the computation to the data** instead of moving huge data to the computation.
"""),
        ]),
        ("Stage 2: Core concepts", [
            T("hd-hdfs", "HDFS architecture: NameNode, DataNodes, blocks, replication", """
- Files are split into **blocks** (default **128 MB**) which are stored on different **DataNodes**.
- The **NameNode** keeps the metadata: the directory tree and which DataNodes hold each block. It does not store file contents.
- Each block is **replicated** (default **replication factor = 3**), usually on different machines (and racks).
- DataNodes send **heartbeats** to the NameNode. If a DataNode stops responding, the NameNode notices that its blocks have fewer replicas than required and instructs other nodes to create new copies.

**Why replication gives fault tolerance:** when a machine fails, other copies of every block still exist, so reads continue and the cluster re-creates the missing copies automatically - no data is lost from a single failure.
Large blocks reduce metadata size and make reading big files efficient (few seeks, mostly sequential reads).
"""),
            T("hd-mapreduce", "How MapReduce works (word count)", """
MapReduce has three phases:
1. **Map**: read input records and emit key-value pairs.
2. **Shuffle & sort**: the framework groups all values by key.
3. **Reduce**: combine the values of each key.

A pure-Python simulation of word count so you can see the data flow:
```python
from collections import defaultdict

lines = ["big data big", "data tools"]

# MAP: emit (word, 1)
mapped = [(word, 1) for line in lines for word in line.split()]
print(mapped)   # [('big', 1), ('data', 1), ('big', 1), ('data', 1), ('tools', 1)]

# SHUFFLE: group by key
groups = defaultdict(list)
for word, one in mapped:
    groups[word].append(one)
print(dict(groups))   # {'big': [1, 1], 'data': [1, 1], 'tools': [1]}

# REDUCE: sum each group
result = {word: sum(ones) for word, ones in groups.items()}
print(result)   # {'big': 2, 'data': 2, 'tools': 1}
```
On a real cluster many mappers and reducers run in parallel on different machines.
"""),
        ]),
        ("Stage 3: Practical examples", [
            T("hd-commands", "HDFS shell commands", """
```bash
hdfs dfs -mkdir -p /user/student/input        # create a directory
hdfs dfs -put sample.txt /user/student/input  # upload a local file
hdfs dfs -ls /user/student/input              # list files
hdfs dfs -cat /user/student/input/sample.txt  # print a file
hdfs dfs -get /user/student/input/sample.txt ./copy.txt   # download
hdfs dfs -rm -r /user/student/old             # delete a directory
hdfs fsck /user/student/input -files -blocks  # see block information
```
These work in a configured Hadoop installation (pseudo-distributed mode on one machine is enough for learning).
"""),
            T("hd-run-job", "Run the built-in WordCount job", """
```bash
hadoop jar $HADOOP_HOME/share/hadoop/mapreduce/hadoop-mapreduce-examples-*.jar \\
    wordcount /user/student/input /user/student/output

hdfs dfs -cat /user/student/output/part-r-00000
```
The **output directory must not exist** before you run the job, otherwise Hadoop stops with an error (to avoid overwriting results).
Each line of the result is `word<TAB>count`. You can also write the mapper and reducer in Python using **Hadoop Streaming**.
"""),
        ]),
        ("Stage 4: Hands-on exercises", [
            T("hd-hands-on", "Set up and practise", """
Learning setup options:
- **Docker**: use a Hadoop image or compose file and open a shell in the container.
- **WSL 2** (Windows Subsystem for Linux) with Ubuntu and a pseudo-distributed install following the official *Single Node Cluster* guide.

Exercises: upload a text file to HDFS, check its blocks with `hdfs fsck`, run WordCount, and read the result. Then change the replication factor of a file:
`hdfs dfs -setrep -w 2 /user/student/input/sample.txt`.
"""),
        ]),
        ("Stage 5: Revision and self-assessment", [
            T("hd-revision", "Common mistakes and comparisons", """
- Re-running a job into an existing output folder (job fails).
- Thinking HDFS is good for many tiny files - the NameNode keeps metadata for every file in memory, so millions of small files hurt it.
- Confusing the NameNode (metadata) with DataNodes (data).
- Hadoop MapReduce vs Spark: MapReduce writes intermediate results to disk between stages (robust but slower); Spark keeps data in memory where possible (faster, especially for iterative work). Hadoop (HDFS/YARN) and Spark are often used *together*.
"""),
        ]),
    ],
    practice=[
        Q("Explain how HDFS replication provides fault tolerance.",
          "What happens when one DataNode fails?",
          "Each block is stored on several DataNodes (default 3). If one node fails, the other replicas still serve the data, and the NameNode detects the missing replicas through heartbeats and instructs other DataNodes to copy blocks until the replication factor is restored."),
        Q("What does the NameNode store and what do DataNodes store?",
          "Metadata vs blocks.",
          "The NameNode stores metadata: the file system tree and the mapping of files to blocks and block locations. DataNodes store the actual data blocks and report to the NameNode with heartbeats and block reports."),
        Q("Describe the three phases of MapReduce for a word-count job on the input 'to be or not to be'.",
          "Map -> shuffle/sort -> reduce.",
          "Map emits (to,1) (be,1) (or,1) (not,1) (to,1) (be,1). Shuffle groups: be:[1,1], not:[1], or:[1], to:[1,1]. Reduce sums: be=2, not=1, or=1, to=2."),
        Q("Why is the HDFS block size so large (128 MB by default)?",
          "Think about disk seeks and NameNode memory.",
          "Large blocks reduce the number of blocks (so less metadata for the NameNode) and favour long sequential reads, which are efficient for big-data scans, compared with many small seeks."),
        Q("Give two differences between Hadoop MapReduce and Apache Spark.",
          "Disk vs memory, API style.",
          "MapReduce writes intermediate data to disk between map and reduce stages, Spark keeps it in memory when possible and is typically faster, especially for iterative algorithms. Spark also offers richer APIs (DataFrames, SQL, streaming, ML) than raw MapReduce."),
    ],
    resources=[
        R("Apache Hadoop documentation", "https://hadoop.apache.org/docs/stable/", "docs"),
        R("HDFS Architecture guide", "https://hadoop.apache.org/docs/stable/hadoop-project-dist/hadoop-hdfs/HdfsDesign.html", "docs"),
        R("MapReduce tutorial (official)", "https://hadoop.apache.org/docs/stable/hadoop-mapreduce-client/hadoop-mapreduce-client-core/MapReduceTutorial.html", "docs"),
    ],
)

# =====================================================================================================
# SPARK
# =====================================================================================================
register(
    "Spark", level="Intermediate",
    overview=("Apache Spark is a fast, general-purpose engine for large-scale data processing. You write DataFrame / SQL code "
              "(often in Python as PySpark) and Spark runs it in parallel on one machine or a cluster."),
    why=("Spark is the standard tool for big-data ETL, analytics and ML pipelines. Data engineer and big-data analyst jobs "
         "often list it as a core requirement."),
    prerequisites=["Python and SQL basics", "pandas is helpful", "Java (JDK 17 is a safe choice) for local PySpark"],
    stages=[
        ("Stage 1: Fundamentals", [
            T("sp-arch", "Spark architecture and setup", """
A Spark application has a **driver** (your program, plans the work), **executors** (worker processes that run tasks in parallel) and a **cluster manager** (Standalone, YARN, Kubernetes). In local mode everything runs on your laptop.

Main APIs: **DataFrame/SQL** (recommended), **RDD** (low-level), **Structured Streaming**, **MLlib**.

Install for practice:
```bash
pip install pyspark
```
You also need Java installed (check with `java -version`). On Windows, WSL 2 or Docker avoids most setup problems.
"""),
        ]),
        ("Stage 2: Core concepts", [
            T("sp-lazy", "Transformations, actions and lazy evaluation", """
- **Transformations** build a plan and return a new DataFrame: `select`, `filter`, `withColumn`, `groupBy`, `join`. They are **lazy** - nothing runs yet.
- **Actions** trigger execution: `show()`, `count()`, `collect()`, `write...`.
- **Narrow** transformations (filter, select) work within each partition. **Wide** transformations (groupBy, join, orderBy) need a **shuffle** - data is redistributed across the network, which is the expensive part.
- Spark optimises the plan (Catalyst optimiser) before running it. Use `df.explain()` to see it.
- `df.cache()` keeps a DataFrame in memory when you reuse it several times.
"""),
        ]),
        ("Stage 3: Practical examples", [
            T("sp-dataframe", "DataFrame example", """
```python
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = SparkSession.builder.appName("demo").master("local[*]").getOrCreate()

df = spark.createDataFrame(
    [("Lahore", 250), ("Karachi", 75), ("Lahore", 300)],
    ["city", "sales"],
)
df.groupBy("city").agg(F.sum("sales").alias("total")).show()
```
Output (row order can differ):
```
+-------+-----+
|   city|total|
+-------+-----+
| Lahore|  550|
|Karachi|   75|
+-------+-----+
```
Reading data: `spark.read.csv("data.csv", header=True, inferSchema=True)`; writing: `df.write.mode("overwrite").parquet("out/")`. **Parquet** is a compressed columnar format and the usual choice for big data.
"""),
            T("sp-sql", "Spark SQL and word count", """
```python
df.createOrReplaceTempView("sales")
spark.sql("SELECT city, SUM(sales) AS total FROM sales GROUP BY city ORDER BY total DESC").show()
```
Same result as above, written in SQL.

Word count with the RDD API:
```python
lines = spark.sparkContext.parallelize(["big data big", "data tools"])
counts = (lines.flatMap(lambda l: l.split())
               .map(lambda w: (w, 1))
               .reduceByKey(lambda a, b: a + b))
print(sorted(counts.collect()))   # [('big', 2), ('data', 2), ('tools', 1)]
```
`reduceByKey` combines values locally before the shuffle, which is more efficient than grouping everything first.
"""),
        ]),
        ("Stage 4: Hands-on exercises", [
            T("sp-hands-on", "Process a bigger CSV", """
1. Take a CSV with at least 100,000 rows (for example public taxi trips or a generated file).
2. Read it with `inferSchema`, check `df.printSchema()`.
3. Clean nulls, create a derived column, aggregate with `groupBy`.
4. Save the result as Parquet and read it back.
5. Open the Spark UI at http://localhost:4040 while a job runs and find the stages and shuffle.
"""),
        ]),
        ("Stage 5: Revision and self-assessment", [
            T("sp-revision", "Common mistakes", """
- Calling `collect()` on a huge DataFrame - it brings everything to the driver and can crash it. Use `show()`, `limit()` or write to storage.
- Using Python UDFs where built-in functions exist (UDFs are much slower).
- Too few/too many partitions (`repartition`, `coalesce`) causing slow or tiny tasks.
- Not realising transformations are lazy, so an error appears only when an action runs.
- Treating Spark as always better: for small data, pandas is simpler and faster.
"""),
        ]),
    ],
    practice=[
        Q("What is the difference between a transformation and an action in Spark? Give two examples of each.",
          "Lazy vs executing.",
          "Transformations (filter, select, groupBy, join) are lazy and only describe a new DataFrame. Actions (show, count, collect, write) trigger execution of the whole plan."),
        Q("What is a shuffle and which operations cause it?",
          "Data moving between partitions.",
          "A shuffle redistributes data across partitions (and over the network) so that records with the same key end up together. Wide operations such as groupBy, join, distinct and orderBy cause it. It is expensive, so minimise it."),
        Q("Write PySpark code that reads sales.csv (with header) and returns the total of the 'amount' column per 'region'.",
          "spark.read.csv + groupBy + agg.",
          "```python\ndf = spark.read.csv('sales.csv', header=True, inferSchema=True)\ndf.groupBy('region').agg(F.sum('amount').alias('total')).show()\n```"),
        Q("Why is collect() dangerous on a large dataset?",
          "Where does the data end up?",
          "collect() brings every row to the driver's memory. On a big dataset this can exhaust driver memory and crash the application. Use show(), take(), limit() or write the result to storage."),
        Q("Give two reasons Spark is often faster than classic Hadoop MapReduce.",
          "Think about disk I/O and optimisation.",
          "Spark keeps intermediate data in memory instead of writing to disk between stages, and its Catalyst optimiser plans the whole job (for example pushing filters down and combining steps) before it runs."),
    ],
    resources=[
        R("Apache Spark documentation", "https://spark.apache.org/docs/latest/", "docs"),
        R("PySpark getting started", "https://spark.apache.org/docs/latest/api/python/getting_started/index.html", "docs"),
        R("Spark SQL guide", "https://spark.apache.org/docs/latest/sql-programming-guide.html", "docs"),
    ],
)

# =====================================================================================================
# KAFKA
# =====================================================================================================
register(
    "Kafka", level="Intermediate",
    overview=("Apache Kafka is a distributed event-streaming platform. Applications publish events to named topics and other "
              "applications read them, in order, in real time or later."),
    why=("Streaming pipelines, real-time analytics and microservices use Kafka to move data reliably between systems. "
         "Big-data and data-engineering roles often list it."),
    prerequisites=["Basic Linux/terminal", "Python or Java basics", "Docker or WSL 2 on Windows"],
    stages=[
        ("Stage 1: Fundamentals", [
            T("kf-concepts", "Events, topics, producers and consumers", """
- An **event** (record/message) has a key, value, timestamp and optional headers - for example "order 101 created".
- A **topic** is a named log of events (like a table you only append to).
- **Producers** write events to topics; **consumers** read them.
- A **broker** is a Kafka server; a **cluster** is several brokers.

Unlike a traditional queue, Kafka keeps events for a retention period, so many consumers can read the same data independently and re-read old events.
"""),
        ]),
        ("Stage 2: Core concepts", [
            T("kf-partitions", "Partitions, offsets, consumer groups, replication", """
- A topic is split into **partitions** for parallelism. Each partition is an ordered log; every event gets an **offset** (0, 1, 2...) within its partition.
- **Ordering is guaranteed only inside one partition.** Events with the same **key** go to the same partition (hash of the key), so all events of "customer 7" stay in order.
- A **consumer group** shares the work: each partition is read by one consumer in the group, so more consumers (up to the number of partitions) means faster processing. Different groups each receive all events.
- Consumers **commit offsets** to remember what they processed.
- **Replication factor** (for example 3) copies each partition to other brokers; one is the **leader**, others are **followers**. If the leader fails, a follower takes over.
- Modern Kafka runs in **KRaft** mode without ZooKeeper.
"""),
        ]),
        ("Stage 3: Practical examples", [
            T("kf-cli", "Command-line quickstart", """
Run these from the Kafka folder on Linux/macOS/WSL after starting a broker (see the official quickstart):
```bash
bin/kafka-topics.sh --create --topic quickstart-events --partitions 3 --bootstrap-server localhost:9092
bin/kafka-console-producer.sh --topic quickstart-events --bootstrap-server localhost:9092
bin/kafka-console-consumer.sh --topic quickstart-events --from-beginning --bootstrap-server localhost:9092
```
Type a few lines in the producer window; they appear in the consumer window. Stop with Ctrl+C. Use `bin/kafka-topics.sh --describe --topic quickstart-events --bootstrap-server localhost:9092` to see partitions and leaders.
"""),
            T("kf-python", "Producer and consumer in Python", """
`pip install kafka-python`
```python
# producer.py
from kafka import KafkaProducer
producer = KafkaProducer(bootstrap_servers="localhost:9092")
producer.send("orders", key=b"cust-1", value=b'{"order_id": 101, "amount": 250}')
producer.flush()

# consumer.py
from kafka import KafkaConsumer
consumer = KafkaConsumer("orders", bootstrap_servers="localhost:9092",
                         group_id="billing", auto_offset_reset="earliest")
for msg in consumer:
    print(msg.partition, msg.offset, msg.key, msg.value)
```
Because both events use the key `cust-1`, they always land in the same partition and are read in the order they were sent.
"""),
        ]),
        ("Stage 4: Hands-on exercises", [
            T("kf-hands-on", "Build a mini streaming pipeline", """
1. Start Kafka locally (Docker image or the official quickstart).
2. Write a producer that sends a fake order every second to the topic `orders`.
3. Write a consumer that keeps a running total of amounts per customer.
4. Start two consumers in the same group and observe how partitions are shared; then stop one and watch the rebalance.
"""),
        ]),
        ("Stage 5: Revision and self-assessment", [
            T("kf-revision", "Common mistakes", """
- Expecting global ordering across partitions (only per-partition order exists).
- Too many consumers in a group: extra consumers beyond the partition count stay idle.
- Forgetting to commit offsets (or committing before processing), leading to lost or repeated messages.
- Using `localhost` as the advertised listener inside Docker/WSL setups, so clients cannot connect.
- Treating Kafka as a database for queries - it is a log; read it with consumers or stream-processing tools.
"""),
        ]),
    ],
    practice=[
        Q("Explain the roles of a topic, a partition and an offset.",
          "Log, parallelism, position.",
          "A topic is a named stream of events. It is divided into partitions, each an ordered, append-only log that allows parallel reading and writing. An offset is the sequential position of an event within a partition."),
        Q("How does Kafka guarantee that all events of the same customer are processed in order?",
          "Think about keys and partitions.",
          "Events with the same key are written to the same partition, and a partition preserves the order of its events and is read by one consumer of a group, so the customer's events are processed in order."),
        Q("What is a consumer group and what happens if you add more consumers than partitions?",
          "Each partition belongs to one consumer in the group.",
          "A consumer group divides a topic's partitions among its consumers so they share the work. If there are more consumers than partitions, the extra consumers sit idle because a partition is assigned to only one consumer in the group."),
        Q("How does replication help when a broker fails?",
          "Leaders and followers.",
          "Each partition has copies on other brokers. If the broker holding the leader fails, one of the in-sync followers is elected as the new leader, so data stays available without loss."),
    ],
    resources=[
        R("Apache Kafka introduction", "https://kafka.apache.org/intro", "docs"),
        R("Apache Kafka quickstart", "https://kafka.apache.org/quickstart", "docs"),
        R("Apache Kafka documentation", "https://kafka.apache.org/documentation/", "docs"),
    ],
)
