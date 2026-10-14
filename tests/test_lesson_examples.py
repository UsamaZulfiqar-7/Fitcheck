"""Run the examples written in the lessons and check that the stated outputs are really correct."""
import sqlite3

import pytest

SETUP = """
CREATE TABLE customers (customer_id INTEGER PRIMARY KEY, name TEXT, city TEXT);
CREATE TABLE orders (order_id INTEGER PRIMARY KEY, customer_id INTEGER, amount REAL, order_date TEXT);
INSERT INTO customers VALUES (1,'Ayesha','Lahore'),(2,'Bilal','Karachi'),(3,'Chen','Lahore'),(4,'Dana','Islamabad');
INSERT INTO orders VALUES (101,1,250.00,'2024-01-05'),(102,1,100.00,'2024-01-20'),(103,2,75.50,'2024-02-02'),
 (104,3,300.00,'2024-02-14'),(105,3,50.00,'2024-03-01');
"""


@pytest.fixture()
def db():
    con = sqlite3.connect(":memory:")
    con.executescript(SETUP)
    yield con
    con.close()


def q(db, sql):
    return db.execute(sql).fetchall()


def test_sql_lesson_outputs(db):
    assert q(db, "SELECT name, city FROM customers WHERE city='Lahore' ORDER BY name") == [("Ayesha", "Lahore"), ("Chen", "Lahore")]
    assert q(db, "SELECT customer_id, COUNT(*), SUM(amount) FROM orders GROUP BY customer_id") == [(1, 2, 350.0), (2, 1, 75.5), (3, 2, 350.0)]
    assert q(db, "SELECT customer_id, SUM(amount) FROM orders GROUP BY customer_id HAVING SUM(amount) > 300") == [(1, 350.0), (3, 350.0)]
    rows = q(db, "SELECT c.name, o.order_id, o.amount FROM customers c INNER JOIN orders o ON c.customer_id=o.customer_id")
    assert len(rows) == 5 and ("Bilal", 103, 75.5) in rows
    assert q(db, "SELECT c.name FROM customers c LEFT JOIN orders o ON c.customer_id=o.customer_id WHERE o.order_id IS NULL") == [("Dana",)]
    assert q(db, "SELECT c.city, SUM(o.amount) AS t FROM customers c JOIN orders o ON o.customer_id=c.customer_id GROUP BY c.city ORDER BY t DESC") == [("Lahore", 700.0), ("Karachi", 75.5)]


def test_sql_practice_answers(db):
    assert q(db, "SELECT order_id, amount FROM orders WHERE amount > 100 ORDER BY amount DESC") == [(104, 300.0), (101, 250.0)]
    assert q(db, "SELECT customer_id, COUNT(*) FROM orders GROUP BY customer_id HAVING COUNT(*) > 1") == [(1, 2), (3, 2)]
    assert q(db, "SELECT AVG(amount) FROM orders")[0][0] == pytest.approx(155.1)


def test_python_pandas_statistics_examples():
    from collections import defaultdict
    import statistics as st

    import pandas as pd
    df = pd.DataFrame({"city": ["Lahore", "Karachi", "Lahore", "Islamabad"], "sales": [250, 75, 300, 120]})
    assert df.groupby("city")["sales"].sum().to_dict() == {"Islamabad": 120, "Karachi": 75, "Lahore": 550}
    assert df.groupby("city")["sales"].mean()["Lahore"] == 275
    assert len(df[(df["city"] == "Lahore") & (df["sales"] > 260)]) == 1
    managers = pd.DataFrame({"city": ["Lahore", "Karachi"], "manager": ["Sara", "Omar"]})
    merged = df.merge(managers, on="city", how="left")
    assert merged[merged.city == "Islamabad"]["manager"].isna().all()

    data = [2, 4, 4, 4, 5, 5, 7, 9]
    assert (st.mean(data), st.median(data), st.mode(data)) == (5, 4.5, 4)
    assert st.pstdev(data) == 2.0 and round(st.stdev(data), 2) == 2.14

    def count_values(items):
        counts = {}
        for item in items:
            counts[item] = counts.get(item, 0) + 1
        return counts
    assert count_values(["a", "b", "a", "c", "a", "b"]) == {"a": 3, "b": 2, "c": 1}

    lines = ["big data big", "data tools"]
    mapped = [(w, 1) for line in lines for w in line.split()]
    groups = defaultdict(list)
    for w, one in mapped:
        groups[w].append(one)
    assert {w: sum(v) for w, v in groups.items()} == {"big": 2, "data": 2, "tools": 1}
    assert sum(n for n in range(1, 21) if n % 2 == 0) == 110


def test_ml_metric_examples():
    tp, fp, fn = 40, 10, 20
    precision, recall = tp / (tp + fp), tp / (tp + fn)
    assert precision == 0.8 and round(recall, 2) == 0.67 and round(2 * precision * recall / (precision + recall), 2) == 0.73


def test_iris_example_accuracy_range():
    from sklearn.datasets import load_iris
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score
    from sklearn.model_selection import train_test_split
    X, y = load_iris(return_X_y=True)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    model = RandomForestClassifier(n_estimators=100, random_state=42).fit(X_train, y_train)
    assert 0.9 <= accuracy_score(y_test, model.predict(X_test)) <= 1.0
