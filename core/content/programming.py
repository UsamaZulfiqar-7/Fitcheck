"""Curated lessons: Python, Git, Docker."""
from core.content._base import Q, R, T, register

# =====================================================================================================
# PYTHON
# =====================================================================================================
register(
    "Python", level="Beginner",
    overview=("Python is a readable, general-purpose programming language. It is the main language of data analysis, "
              "machine learning, automation and many backend systems."),
    why=("Python is requested in most data, ML and backend job postings. Libraries such as pandas, NumPy and scikit-learn "
         "are built on it, so Python is the gateway to many other skills."),
    prerequisites=["Basic computer skills", "Python 3.10+ installed (python.org) and VS Code"],
    stages=[
        ("Stage 1: Fundamentals", [
            T("py-basics", "Variables, types and printing", """
```python
name = "Ayesha"        # str
age = 24               # int
height = 1.62          # float
is_student = True      # bool

print(name, age)                       # Ayesha 24
print(f"{name} is {age} years old")    # Ayesha is 24 years old
print(type(height))                    # <class 'float'>
```
Python is **dynamically typed**: a variable can hold any type and gets the type of its value. Use `input()` to read text and convert with `int()` / `float()`.
Indentation (4 spaces) is part of the syntax - it defines blocks.
"""),
            T("py-control", "Decisions and loops", """
```python
score = 72
if score >= 80:
    grade = "A"
elif score >= 60:
    grade = "B"
else:
    grade = "C"
print(grade)            # B

total = 0
for n in range(1, 6):   # 1,2,3,4,5
    total += n
print(total)            # 15

count = 3
while count > 0:
    print(count)        # 3, 2, 1
    count -= 1
```
`range(1, 6)` stops *before* 6. Use `break` to leave a loop and `continue` to skip to the next iteration.
"""),
        ]),
        ("Stage 2: Core concepts", [
            T("py-collections", "Lists, dictionaries and sets", """
```python
nums = [3, 1, 4, 1, 5]
nums.append(9)           # [3, 1, 4, 1, 5, 9]
print(nums[0], nums[-1]) # 3 9
print(sorted(nums))      # [1, 1, 3, 4, 5, 9]
print(len(set(nums)))    # 5  (unique values)

person = {"name": "Bilal", "city": "Karachi"}
person["age"] = 30
print(person.get("email", "n/a"))   # n/a
for key, value in person.items():
    print(key, value)
```
- **list**: ordered and changeable. **tuple**: ordered, not changeable. **set**: unique items, no order. **dict**: key -> value lookups.
"""),
            T("py-functions", "Functions", """
```python
def average(values):
    if not values:
        return 0
    return sum(values) / len(values)

print(average([2, 4, 6]))   # 4.0
```
A function groups reusable logic: parameters go in, `return` sends a value out. Add default values (`def greet(name="friend")`) and docstrings to describe what the function does.
"""),
        ]),
        ("Stage 3: Practical examples", [
            T("py-counting", "Counting repeated values", """
```python
def count_values(items):
    counts = {}
    for item in items:
        counts[item] = counts.get(item, 0) + 1
    return counts

data = ["a", "b", "a", "c", "a", "b"]
counts = count_values(data)
print(counts)                                           # {'a': 3, 'b': 2, 'c': 1}
repeated = {k: v for k, v in counts.items() if v > 1}   # dict comprehension
print(repeated)                                         # {'a': 3, 'b': 2}
```
The standard library already has this: `from collections import Counter; Counter(data)`.
"""),
            T("py-files", "Reading files and handling errors", """
```python
import csv

try:
    with open("scores.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(len(rows), "rows")
except FileNotFoundError:
    print("File not found - check the path")
```
`with` closes the file automatically. `try/except` lets the program react to errors instead of crashing. Use `pathlib.Path` for file paths and `venv` (`python -m venv .venv`) for project environments.
"""),
        ]),
        ("Stage 4: Hands-on exercises", [
            T("py-hands-on", "Write small programs", """
Write each program yourself, run it, and then compare it to the solution in the **Practice** tab:
1. Word counter for a text file.
2. Function that removes duplicates but keeps order.
3. Mini "expense tracker" that stores items in a list of dictionaries and prints totals per category.

Habit: run code often, read error messages from the **last line upwards**, and use `print()` or the VS Code debugger to inspect variables.
"""),
        ]),
        ("Stage 5: Revision and self-assessment", [
            T("py-revision", "Common mistakes", """
- Mixing tabs and spaces / wrong indentation -> `IndentationError`.
- `=` (assignment) vs `==` (comparison).
- Mutable default argument: `def f(x, items=[])` shares one list between calls - use `None` and create the list inside.
- Modifying a list while looping over it.
- Off-by-one errors with `range()` and slicing (`a[0:3]` has 3 items).
- Forgetting `return` (the function then returns `None`).
"""),
        ]),
    ],
    practice=[
        Q("Write a function that counts how many times each value appears in a list and returns only the values that repeat.",
          "Use a dictionary and .get(), then filter counts > 1.",
          "```python\ndef repeated_values(items):\n    counts = {}\n    for item in items:\n        counts[item] = counts.get(item, 0) + 1\n    return {k: v for k, v in counts.items() if v > 1}\n\nprint(repeated_values([1, 2, 2, 3, 3, 3]))   # {2: 2, 3: 3}\n```"),
        Q("Write a function that removes duplicates from a list but keeps the original order.",
          "Keep a set of items already seen.",
          "```python\ndef dedupe(items):\n    seen, result = set(), []\n    for item in items:\n        if item not in seen:\n            seen.add(item)\n            result.append(item)\n    return result\n\nprint(dedupe([3, 1, 3, 2, 1]))   # [3, 1, 2]\n```"),
        Q("Print the sum of all even numbers from 1 to 20.",
          "Use range and the % operator.",
          "```python\nprint(sum(n for n in range(1, 21) if n % 2 == 0))   # 110\n```"),
        Q("What does this print? `x = [1, 2, 3]; y = x; y.append(4); print(x)`",
          "Are x and y two lists or two names for one list?",
          "`[1, 2, 3, 4]`. `y = x` does not copy the list; both names refer to the same object. Use `y = x.copy()` for a separate copy."),
        Q("What is wrong with `def add(item, bucket=[]): bucket.append(item); return bucket`?",
          "Call it twice without bucket.",
          "The default list is created once and shared by all calls, so `add(1)` then `add(2)` returns `[1, 2]`. Use `bucket=None` and create `bucket = []` inside the function when it is None."),
    ],
    resources=[
        R("Official Python tutorial", "https://docs.python.org/3/tutorial/", "docs"),
        R("Automate the Boring Stuff with Python (free online book)", "https://automatetheboringstuff.com/", "book"),
        R("Learn Python (interactive)", "https://www.learnpython.org/", "interactive"),
    ],
)

# =====================================================================================================
# GIT
# =====================================================================================================
register(
    "Git", level="Beginner",
    overview=("Git is a version control system: it records the history of your project so you can undo mistakes, work on "
              "features in parallel and collaborate with others (usually through GitHub or GitLab)."),
    why=("Teams expect every developer and data professional to store code in Git, open pull requests and resolve conflicts."),
    prerequisites=["Comfort with a terminal (PowerShell is fine)", "Git installed from git-scm.com"],
    stages=[
        ("Stage 1: Fundamentals", [
            T("git-basics", "Repository, commit and the three areas", """
A **repository** is a project folder tracked by Git. Changes move through three areas: **working directory** -> **staging area** -> **repository (commits)**.

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
git init
git status
git add app.py          # stage a file (or: git add .)
git commit -m "Add first version of app"
git log --oneline
```
A **commit** is a snapshot with a message. Write messages that explain *why* (for example "Fix crash when CSV is empty").
"""),
        ]),
        ("Stage 2: Core concepts", [
            T("git-branches", "Branches and merging", """
```bash
git switch -c feature/report     # create + switch to a new branch
# ...edit files, then:
git add . && git commit -m "Add report page"
git switch main
git merge feature/report
git branch -d feature/report
```
A **branch** is a separate line of work. Keep `main` stable and build features on branches. If both branches changed the same lines, Git stops with a **merge conflict**.
"""),
        ]),
        ("Stage 3: Practical examples", [
            T("git-remote", "GitHub: clone, push, pull and pull requests", """
```bash
git clone https://github.com/<user>/<repo>.git
git remote -v
git push -u origin feature/report     # first push of a branch
git pull                              # fetch + merge the latest changes
```
Workflow on GitHub: push your branch -> open a **Pull Request** -> teammates review -> merge. Add a `.gitignore` so you never commit virtual environments, `.env` files or secrets.
"""),
            T("git-conflicts", "Resolving a merge conflict", """
Git marks conflicts inside the file:
```
<<<<<<< HEAD
total = price * quantity
=======
total = price * qty
>>>>>>> feature/report
```
Edit the file to keep the correct version, delete the marker lines, then:
```bash
git add app.py
git commit
```
Undo helpers: `git restore file` (discard unstaged edits), `git restore --staged file` (unstage), `git revert <commit>` (safe undo of a commit that is already shared).
"""),
        ]),
        ("Stage 4: Hands-on exercises", [
            T("git-hands-on", "Practice workflow", """
1. Create a repo with a `README.md`, make 3 commits.
2. Create a branch, change a line, merge it back.
3. Create a deliberate conflict (change the same line on two branches) and resolve it.
4. Push the project to GitHub and open a pull request from a branch.
"""),
        ]),
        ("Stage 5: Revision and self-assessment", [
            T("git-revision", "Common mistakes", """
- Committing secrets (API keys, passwords). If it happens, rotate the secret - deleting the commit is not enough.
- Working directly on `main`.
- Huge commits with unrelated changes; commit small logical steps.
- Using `git push --force` on shared branches.
"""),
        ]),
    ],
    practice=[
        Q("What is the difference between git add, git commit and git push?",
          "Staging area, local history, remote.",
          "`git add` stages changes, `git commit` records the staged snapshot in your local history, and `git push` uploads your local commits to a remote repository such as GitHub."),
        Q("Write the commands to create a branch called fix/login, commit a change on it and merge it into main.",
          "git switch -c ...",
          "```bash\ngit switch -c fix/login\ngit add .\ngit commit -m \"Fix login validation\"\ngit switch main\ngit merge fix/login\n```"),
        Q("What causes a merge conflict and how do you resolve it?",
          "Two changes to the same lines.",
          "It happens when two branches change the same lines (or one deletes what the other edits). Open the file, choose/combine the correct lines, remove the conflict markers, `git add` the file and commit."),
        Q("What is the difference between git pull and git fetch?",
          "One of them also merges.",
          "`git fetch` downloads new commits without changing your working files. `git pull` is fetch followed by a merge (or rebase) into your current branch."),
    ],
    resources=[
        R("Pro Git book (free)", "https://git-scm.com/book/en/v2", "book"),
        R("GitHub Docs - Get started", "https://docs.github.com/en/get-started", "docs"),
        R("Git official documentation", "https://git-scm.com/doc", "docs"),
    ],
)

# =====================================================================================================
# DOCKER
# =====================================================================================================
register(
    "Docker", level="Beginner",
    overview=("Docker packages an application with everything it needs (runtime, libraries, settings) into a container so it runs "
              "the same way on any machine."),
    why=("Data and backend teams use Docker to share reproducible environments and to deploy applications and pipelines."),
    prerequisites=["Comfort with a terminal", "Basic Linux ideas", "Docker Desktop installed (Windows: WSL 2 backend)"],
    stages=[
        ("Stage 1: Fundamentals", [
            T("dk-concepts", "Images, containers and registries", """
- **Image**: a read-only template (for example `python:3.12-slim`).
- **Container**: a running instance of an image - lightweight and isolated.
- **Registry**: where images are stored (Docker Hub).
- Containers share the host kernel, so they start faster and use fewer resources than virtual machines.

```bash
docker --version
docker run hello-world
docker ps            # running containers
docker ps -a         # all containers
docker images
```
"""),
        ]),
        ("Stage 2: Core concepts", [
            T("dk-dockerfile", "Writing a Dockerfile", """
A Dockerfile describes how to build an image. Example for a Streamlit app:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]
```
Copy `requirements.txt` and install first, so Docker can **cache** that layer when only your code changes. Add a `.dockerignore` (like `.gitignore`) to keep the image small.
```bash
docker build -t fitcheck:1.0 .
docker run -p 8501:8501 fitcheck:1.0
```
`-p host:container` publishes a container port on your machine (open http://localhost:8501).
"""),
        ]),
        ("Stage 3: Practical examples", [
            T("dk-volumes", "Volumes, environment variables and Compose", """
Container storage disappears when the container is removed, so use **volumes** for data you need to keep:
```bash
docker run -d --name db -e POSTGRES_PASSWORD=secret -p 5432:5432 -v pgdata:/var/lib/postgresql/data postgres:16
```
`-e` sets an environment variable and `-v name:path` mounts a volume.

**Docker Compose** starts several containers together (`compose.yaml`):
```yaml
services:
  app:
    build: .
    ports: ["8501:8501"]
    depends_on: [db]
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: secret
    volumes: [pgdata:/var/lib/postgresql/data]
volumes:
  pgdata:
```
Run with `docker compose up -d` and stop with `docker compose down`.
"""),
        ]),
        ("Stage 4: Hands-on exercises", [
            T("dk-hands-on", "Containerise a small app", """
1. Write a tiny Python or Streamlit app and a `requirements.txt`.
2. Write a Dockerfile and build the image.
3. Run it with a published port and open it in the browser.
4. Add a PostgreSQL container with Compose and connect your app to it using the service name as the host.
"""),
        ]),
        ("Stage 5: Revision and self-assessment", [
            T("dk-revision", "Common mistakes", """
- Storing important data inside a container without a volume.
- Putting secrets in the image (use environment variables or secret stores).
- `localhost` inside a container means the container itself - use the Compose service name to reach another container.
- Forgetting `0.0.0.0` as the bind address, so the app is unreachable from outside.
- Very large images: use slim base images and `.dockerignore`.
"""),
        ]),
    ],
    practice=[
        Q("Explain the difference between a Docker image and a container.",
          "Template vs running instance.",
          "An image is an immutable template (code, libraries, settings). A container is a running (or stopped) instance created from an image; you can start many containers from one image."),
        Q("Why does a Dockerfile usually copy requirements.txt and install packages before copying the rest of the code?",
          "Layer caching.",
          "Docker caches each layer. Dependencies change rarely, so installing them in an early layer lets Docker reuse the cache when only your source code changes, making rebuilds much faster."),
        Q("How do you keep database data after a container is deleted?",
          "Think about volumes.",
          "Mount a named volume or a host folder at the database data directory (for example `-v pgdata:/var/lib/postgresql/data`)."),
        Q("Write the command to run an image called fitcheck:1.0 and make port 8501 available on your computer.",
          "-p host:container",
          "```bash\ndocker run -p 8501:8501 fitcheck:1.0\n```"),
    ],
    resources=[
        R("Docker - Get started", "https://docs.docker.com/get-started/", "docs"),
        R("Dockerfile reference", "https://docs.docker.com/reference/dockerfile/", "docs"),
        R("Docker Compose documentation", "https://docs.docker.com/compose/", "docs"),
    ],
)
