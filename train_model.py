"""
train_model.py
==============
Trains a simple TF-IDF + Logistic Regression ATS classifier and saves it.
Run once before starting the app:
    python train_model.py

This is a demo training set — expand with real resume data for production.
"""

import os
import joblib
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models', 'ats_classifier.pkl')
os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)

# ─── Synthetic training data ──────────────────────────────────────────────────
# Labels: 0 = low ATS, 1 = medium ATS, 2 = high ATS
SAMPLES = [
    # High-ATS resumes (label 2)
    ("Developed Python Flask REST APIs deployed on AWS Docker Kubernetes. Led agile sprint cycles.",  2),
    ("Built machine learning models with scikit-learn TensorFlow. Improved accuracy by 18%.",        2),
    ("Implemented CI/CD pipelines with Jenkins GitHub Actions. Reduced deployment time by 40%.",     2),
    ("Designed React TypeScript frontend with Tailwind. Increased user engagement by 25%.",          2),
    ("Architected microservices with Go PostgreSQL Redis. Handled 1M requests/day.",                 2),
    ("Data analysis with pandas numpy matplotlib. Created Power BI dashboards for 5 departments.",  2),
    ("NLP pipeline using spaCy transformers HuggingFace BERT. F1 score 0.92.",                      2),
    ("DevOps: Terraform Ansible cloud infrastructure. Zero-downtime deployments.",                   2),

    # Medium-ATS resumes (label 1)
    ("Experience with Python and some web development. Used SQL for queries.",                       1),
    ("Worked on various software projects. Familiar with JavaScript and HTML.",                      1),
    ("Knowledge of machine learning concepts. Did some data analysis projects.",                     1),
    ("Used Git for version control. Participated in team projects.",                                 1),
    ("Built websites using React. Some experience with Node.js.",                                    1),
    ("Completed internship in software company. Worked with databases.",                             1),

    # Low-ATS resumes (label 0)
    ("Hard worker. Quick learner. Good communication skills. Team player.",                          0),
    ("Responsible for various tasks in the company. Helped colleagues.",                             0),
    ("References available upon request. Interested in technology sector.",                          0),
    ("Experienced professional seeking opportunity. Open to relocation.",                            0),
]

texts  = [s[0] for s in SAMPLES]
labels = [s[1] for s in SAMPLES]

# ─── Train ────────────────────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    texts, labels, test_size=0.2, random_state=42
)

pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(ngram_range=(1, 2), max_features=5000)),
    ('clf',   LogisticRegression(max_iter=500, C=1.0)),
])

pipeline.fit(X_train, y_train)

# ─── Evaluate ─────────────────────────────────────────────────────────────────
if X_test:
    y_pred = pipeline.predict(X_test)
    print("Classification Report:")
    print(classification_report(y_test, y_pred, target_names=['Low','Medium','High']))

# ─── Save ─────────────────────────────────────────────────────────────────────
joblib.dump(pipeline, MODEL_PATH)
print(f"\n✓ Model saved to {MODEL_PATH}")


def load_model():
    """Load the saved ATS classifier pipeline."""
    return joblib.load(MODEL_PATH)


def predict_ats_category(text: str) -> dict:
    """
    Predict ATS category (Low / Medium / High) for a resume text.
    Returns label name and class probabilities.
    """
    model = load_model()
    proba = model.predict_proba([text])[0]
    label_idx = int(np.argmax(proba))
    labels = {0: 'Low', 1: 'Medium', 2: 'High'}
    return {
        'category':     labels[label_idx],
        'probabilities': {
            'Low':    round(float(proba[0]), 3),
            'Medium': round(float(proba[1]), 3),
            'High':   round(float(proba[2]), 3),
        }
    }


if __name__ == '__main__':
    # Quick smoke test
    sample = "Python developer with experience in Flask, SQL, and machine learning."
    result = predict_ats_category(sample)
    print(f"\nSample prediction: {result}")
