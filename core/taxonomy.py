"""Skill taxonomy used for rule-based skill extraction and normalisation.

Each entry: (canonical display name, category, [aliases]).
An alias starting with "=" is matched case-sensitively (short acronyms such as ML).
All other aliases are matched case-insensitively on word boundaries.
"""

PROG = "Programming"
DATA = "Data & Analytics"
DB = "Databases"
BIG = "Big Data"
ML = "Machine Learning & AI"
CLOUD = "Cloud & DevOps"
WEB = "Web Development"
TOOLS = "Tools & Practices"
SOFT = "Soft Skills"

CATEGORIES = [PROG, DATA, DB, BIG, ML, CLOUD, WEB, TOOLS, SOFT]

TAXONOMY = [
    # Programming
    ("Python", PROG, ["python3", "python programming"]),
    ("Java", PROG, ["core java"]),
    ("JavaScript", PROG, ["js", "ecmascript", "es6"]),
    ("TypeScript", PROG, []),
    ("C++", PROG, ["cpp"]),
    ("C#", PROG, ["c sharp"]),
    ("R", PROG, ["=R programming", "rstudio", "r language"]),
    ("Scala", PROG, []),
    ("Go", PROG, ["golang"]),
    ("PHP", PROG, []),
    ("Kotlin", PROG, []),
    ("Bash", PROG, ["shell scripting", "bash scripting", "shell script"]),
    ("MATLAB", PROG, []),
    # Data & analytics
    ("Excel", DATA, ["ms excel", "microsoft excel", "advanced excel", "excel formulas", "vlookup", "pivot tables", "pivot table"]),
    ("Power BI", DATA, ["powerbi", "power-bi", "dax"]),
    ("Tableau", DATA, []),
    ("Looker", DATA, ["looker studio", "data studio"]),
    ("Pandas", DATA, []),
    ("NumPy", DATA, []),
    ("Matplotlib", DATA, []),
    ("Seaborn", DATA, []),
    ("Data Analysis", DATA, ["data analytics", "analyzing data", "analysing data", "exploratory data analysis", "=EDA"]),
    ("Data Visualization", DATA, ["data visualisation", "dashboards", "dashboarding", "data viz"]),
    ("Statistics", DATA, ["statistical analysis", "statistical", "hypothesis testing", "probability"]),
    ("Data Cleaning", DATA, ["data cleansing", "data wrangling", "data preprocessing", "data preparation"]),
    ("ETL", DATA, ["data pipelines", "data pipeline", "etl pipelines", "elt"]),
    ("Data Modeling", DATA, ["data modelling", "dimensional modeling", "star schema"]),
    ("Data Warehousing", DATA, ["data warehouse", "data warehouses", "dwh"]),
    ("A/B Testing", DATA, ["ab testing", "a/b tests", "split testing"]),
    ("Google Analytics", DATA, []),
    # Databases
    ("SQL", DB, ["sql queries", "t-sql", "tsql", "pl/sql", "structured query language"]),
    ("MySQL", DB, []),
    ("PostgreSQL", DB, ["postgres"]),
    ("SQLite", DB, []),
    ("SQL Server", DB, ["mssql", "microsoft sql server", "ms sql"]),
    ("Oracle", DB, ["oracle database", "oracle db"]),
    ("MongoDB", DB, ["mongo db"]),
    ("NoSQL", DB, ["no-sql"]),
    ("Redis", DB, []),
    ("Elasticsearch", DB, ["elastic search"]),
    # Big data
    ("Hadoop", BIG, ["hdfs", "mapreduce", "map reduce"]),
    ("Spark", BIG, ["apache spark", "pyspark"]),
    ("Kafka", BIG, ["apache kafka"]),
    ("Hive", BIG, ["apache hive", "hiveql"]),
    ("Airflow", BIG, ["apache airflow"]),
    ("Databricks", BIG, []),
    ("Snowflake", BIG, []),
    ("Big Data", BIG, ["big-data", "large-scale data", "distributed computing", "distributed systems"]),
    ("Flink", BIG, ["apache flink"]),
    # Machine learning & AI
    ("Machine Learning", ML, ["=ML", "ml models", "machine-learning", "predictive modeling", "predictive modelling"]),
    ("Deep Learning", ML, ["neural networks", "neural network"]),
    ("NLP", ML, ["natural language processing", "text mining"]),
    ("Scikit-learn", ML, ["scikit learn", "sklearn"]),
    ("TensorFlow", ML, ["tensor flow"]),
    ("PyTorch", ML, []),
    ("Keras", ML, []),
    ("Computer Vision", ML, ["image processing", "opencv"]),
    ("Generative AI", ML, ["genai", "gen ai", "llm", "llms", "large language models", "prompt engineering"]),
    ("Feature Engineering", ML, []),
    ("MLOps", ML, ["model deployment", "model serving"]),
    # Cloud & DevOps
    ("AWS", CLOUD, ["amazon web services", "ec2", "redshift"]),
    ("Azure", CLOUD, ["microsoft azure"]),
    ("GCP", CLOUD, ["google cloud", "google cloud platform", "bigquery"]),
    ("Docker", CLOUD, ["containers", "containerization", "containerisation"]),
    ("Kubernetes", CLOUD, ["k8s"]),
    ("Git", CLOUD, ["version control", "git flow", "gitflow"]),
    ("GitHub", CLOUD, ["gitlab", "bitbucket"]),
    ("CI/CD", CLOUD, ["continuous integration", "continuous delivery", "continuous deployment", "github actions", "jenkins"]),
    ("Linux", CLOUD, ["unix", "ubuntu"]),
    ("Terraform", CLOUD, ["infrastructure as code"]),
    # Web development
    ("HTML", WEB, ["html5"]),
    ("CSS", WEB, ["css3"]),
    ("React", WEB, ["reactjs", "react.js"]),
    ("Angular", WEB, ["angularjs"]),
    ("Vue", WEB, ["vue.js", "vuejs"]),
    ("Node.js", WEB, ["nodejs", "node js"]),
    ("Django", WEB, []),
    ("Flask", WEB, []),
    ("FastAPI", WEB, ["fast api"]),
    ("Streamlit", WEB, []),
    ("REST API", WEB, ["rest apis", "restful api", "restful apis", "restful services", "api development"]),
    ("Tailwind CSS", WEB, ["tailwind", "tailwindcss"]),
    ("Bootstrap", WEB, []),
    ("Next.js", WEB, ["nextjs"]),
    # Tools & practices
    ("Agile", TOOLS, ["agile methodology", "agile methodologies"]),
    ("Scrum", TOOLS, []),
    ("Jira", TOOLS, []),
    ("Unit Testing", TOOLS, ["pytest", "unit tests", "test-driven development", "=TDD"]),
    ("OOP", TOOLS, ["object oriented programming", "object-oriented programming", "object oriented design"]),
    ("Data Structures", TOOLS, ["data structures and algorithms", "algorithms"]),
    # Soft skills
    ("Communication", SOFT, ["communication skills", "written communication", "verbal communication"]),
    ("Teamwork", SOFT, ["team player", "collaboration", "collaborative", "team work"]),
    ("Problem Solving", SOFT, ["problem-solving", "analytical thinking", "analytical skills"]),
    ("Leadership", SOFT, ["team leadership", "mentoring"]),
    ("Critical Thinking", SOFT, []),
    ("Time Management", SOFT, ["time-management"]),
    ("Presentation Skills", SOFT, ["presenting", "public speaking", "stakeholder management"]),
]
