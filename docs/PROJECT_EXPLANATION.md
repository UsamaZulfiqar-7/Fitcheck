# FitCheck - Academic Project Explanation

## Problem

Job seekers rarely know how closely their CV matches a job posting or which skills they should learn. Job postings are often
shared as images or scanned PDFs that software cannot read directly. Existing screening tools mostly return a score without
explaining the gap or helping the candidate close it.

## Aim

To build a web-based system that compares a CV with a job posting, explains the match, teaches the missing skills, and updates
the CV only after the candidate confirms that the skill has been learned.

## Objectives

1. Extract text from PDF, DOCX, TXT and image inputs (with OCR when needed).
2. Extract and normalise skills from both documents.
3. Compute a transparent match score from skill overlap and text similarity.
4. Show matched, missing and additional skills with an explanation of their importance for the job.
5. Provide structured, skill-specific learning material, practice questions and progress tracking.
6. Let the candidate add a learned skill to a new CV version after explicit confirmation, and recalculate the score.
7. Store all data in a relational database (PostgreSQL, with SQLite fallback) and export reports.

## Methodology

The system is organised as a modular pipeline: ingestion, raw storage, text extraction, skill extraction, scoring, gap analysis,
learning, progress storage, CV generation and reporting. Each stage is a separate Python module with a clear interface, and the
Streamlit user interface only calls these modules.

* **Skill extraction:** a rule-based taxonomy of about 100 skills with aliases and categories, with word-boundary matching and
  longest-match precedence. Required and preferred skills are separated using headings and phrases such as "nice to have".
* **Similarity:** TF-IDF with cosine similarity is the reliable baseline. Sentence-transformers embeddings can optionally be averaged in.
* **Score:** final = 0.7 x skill match + 0.3 x text similarity. The weights are configurable and documented.
* **Learning content:** written by hand for twelve skills (for example SQL, Python, Excel, Power BI, Spark, Kafka) and checked by
  executing the examples; other skills receive a clearly labelled starter path. An optional AI helper can add personalised notes.
* **Data:** the system does not need a large resume dataset because users upload their own CV. A reproducible, fictional
  synthetic dataset of 60 job postings is provided for development and demonstration.

## Tools

Python, Streamlit (interface), pdfplumber and python-docx (document reading), Tesseract OCR (images and scanned PDFs),
scikit-learn (TF-IDF), SQLAlchemy with PostgreSQL or SQLite (storage), Plotly (charts), ReportLab (PDF output), pytest (testing).

## Results and testing

Automated tests (63) cover the scoring arithmetic, extraction of all supported formats, the CV editing rules, the lesson examples
(executed and checked), the complete workflow against both PostgreSQL 16 and SQLite, and the Streamlit pages driven through
`streamlit.testing`. The recognition of the 60 synthetic jobs' labelled skills is verified exactly (0 mismatches).

## Limitations

* The score estimates keyword and text overlap; it does not measure experience level or hiring suitability.
* Skill detection is limited to the taxonomy.
* Updated PDF CVs are rebuilt from text and do not keep the original design.
* OCR quality depends on the image.
* The pipeline runs on one machine; distributed processing is not implemented.

## Future work

Skill verification quizzes, automatic job recommendations, resume rewriting, multi-language support (Urdu and Arabic), recruiter
mode with ranked candidates, larger labelled evaluation datasets with precision and recall, and online deployment with user accounts.

## Viva answers (short)

* **Why not a trained model?** The task needs explainable matching and teaching; a rule-based and TF-IDF baseline is transparent and works offline.
* **Is 90% accuracy?** It is a match estimate, not accuracy. Accuracy would need a labelled evaluation set, which is listed as future work.
* **Does the system add skills automatically?** No. Every addition needs confirmation and is stored as a new version.
