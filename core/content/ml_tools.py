"""Curated lesson: Machine Learning."""
from core.content._base import Q, R, T, register

register(
    "Machine Learning", level="Intermediate",
    overview=("Machine learning (ML) builds models that learn patterns from data instead of following hand-written rules. "
              "Supervised learning predicts a known target (price, spam/not spam); unsupervised learning finds structure "
              "(customer groups) without labels."),
    why=("ML engineer and data scientist roles expect you to prepare data, train and evaluate models correctly, and explain "
         "the results. Many analyst roles also use basic ML for forecasting and classification."),
    prerequisites=["Python (functions, lists, pandas)", "Basic statistics (mean, variance, correlation)"],
    stages=[
        ("Stage 1: Fundamentals", [
            T("ml-types", "Types of machine learning and the workflow", """
- **Supervised**: learn from labelled examples. *Regression* predicts a number (house price); *classification* predicts a category (fraud / not fraud).
- **Unsupervised**: no labels. *Clustering* groups similar rows (customer segments); *dimensionality reduction* compresses features.
- **Reinforcement learning**: an agent learns by reward (games, robotics).

Standard workflow: **define the problem -> collect/clean data -> split data -> choose features -> train -> evaluate -> improve -> deploy and monitor.**
A **feature** is an input column; the **target** (label) is what you predict.
"""),
        ]),
        ("Stage 2: Core concepts", [
            T("ml-split", "Train/test split, overfitting and data leakage", """
Never judge a model on the data it learned from. Split the data:
- **Training set** (for example 80%): the model learns from it.
- **Test set** (20%): used once at the end to estimate performance on new data.

**Overfitting**: the model memorises noise - excellent training score, poor test score. **Underfitting**: too simple - poor on both.
Remedies for overfitting: more data, simpler model, regularisation, cross-validation.

**Data leakage**: information from the test set (or from the future) sneaks into training - for example scaling using the full dataset before splitting. Always fit preprocessing on the training set only (use a scikit-learn `Pipeline`).
"""),
            T("ml-metrics", "Evaluation metrics", """
For classification count outcomes in a **confusion matrix**: TP, FP, FN, TN.

- **Accuracy** = (TP + TN) / all - misleading when classes are imbalanced (99% "no fraud" gives 99% accuracy with a useless model).
- **Precision** = TP / (TP + FP): of the cases predicted positive, how many were right?
- **Recall** = TP / (TP + FN): of all real positives, how many did we find?
- **F1** = harmonic mean of precision and recall.

Example: TP = 40, FP = 10, FN = 20 -> precision = 40/50 = **0.80**, recall = 40/60 ≈ **0.67**, F1 ≈ **0.73**.
For regression use **MAE** (average absolute error), **RMSE** and **R²**.
"""),
        ]),
        ("Stage 3: Practical examples", [
            T("ml-sklearn", "Your first model with scikit-learn", """
```python
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

X, y = load_iris(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y)

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

pred = model.predict(X_test)
print("accuracy:", accuracy_score(y_test, pred))
print(classification_report(y_test, pred))
```
**Expected output:** an accuracy of roughly 0.9-1.0 (iris is an easy dataset; the exact value depends on the split and library version) and a report with precision/recall per class.

Every scikit-learn model follows the same API: `fit(X, y)` to learn and `predict(X)` to use. Try swapping `RandomForestClassifier` for `LogisticRegression` or `KNeighborsClassifier` and compare.
"""),
            T("ml-improve", "Cross-validation and tuning", """
One split can be lucky or unlucky. **Cross-validation** trains/tests on several splits and averages the score:
```python
from sklearn.model_selection import cross_val_score
scores = cross_val_score(model, X, y, cv=5)
print(scores.mean(), scores.std())
```
**Hyperparameters** (like `n_estimators`) are settings you choose before training; tune them with `GridSearchCV`, always judging by cross-validation, never by the test set.
"""),
        ]),
        ("Stage 4: Hands-on exercises", [
            T("ml-hands-on", "End-to-end mini project", """
1. Pick a small tabular dataset (Titanic, house prices, or any CSV you know).
2. Explore it with pandas and charts; handle missing values.
3. Build a baseline model (for example predict the majority class) and then a real model.
4. Evaluate with the correct metric and cross-validation, and write 5 lines about what the model gets wrong.
5. Save the model with `joblib.dump` and keep the project in Git.

Then answer the **Practice** questions.
"""),
        ]),
        ("Stage 5: Revision and self-assessment", [
            T("ml-revision", "Common mistakes", """
- Evaluating on training data.
- Using accuracy for imbalanced data.
- Scaling or imputing before the train/test split (leakage).
- Tuning on the test set.
- Ignoring a simple baseline - a complex model must beat it to be worth using.
- Treating a model score as proof; check data quality and fairness.
"""),
        ]),
    ],
    practice=[
        Q("Why do we split data into training and test sets?",
          "What would happen if you evaluated on the training data?",
          "To estimate how the model performs on unseen data. Evaluating on training data hides overfitting because the model has already seen those examples."),
        Q("A fraud model has 99% accuracy on data where 99% of transactions are legitimate. Is it good? What would you check?",
          "A model that always predicts 'legitimate' gets 99%.",
          "Not necessarily. Always predicting 'legitimate' also scores 99%. Check precision, recall and F1 for the fraud class and the confusion matrix."),
        Q("Given TP = 30, FP = 10, FN = 10, compute precision and recall.",
          "Use the formulas.",
          "Precision = 30 / (30 + 10) = 0.75. Recall = 30 / (30 + 10) = 0.75."),
        Q("What is overfitting and how can you reduce it?",
          "Training score high, test score low.",
          "Overfitting is when a model learns noise in the training data and performs worse on new data. Reduce it with more data, a simpler model, regularisation, feature selection, early stopping and cross-validation."),
        Q("Give an example of data leakage and how to prevent it.",
          "Think about preprocessing before splitting.",
          "Scaling or imputing the whole dataset before the train/test split lets test-set statistics influence training. Split first and fit preprocessing inside a Pipeline on the training data only."),
    ],
    resources=[
        R("scikit-learn user guide", "https://scikit-learn.org/stable/user_guide.html", "docs"),
        R("Kaggle Learn - Intro to Machine Learning (free)", "https://www.kaggle.com/learn/intro-to-machine-learning", "interactive"),
        R("Google Machine Learning Crash Course (free)", "https://developers.google.com/machine-learning/crash-course", "course"),
    ],
)
