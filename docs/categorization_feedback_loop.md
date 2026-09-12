# Categorization Active Learning & Feedback Loop Architecture (Task 3.7)

## 1. Overview & Purpose

In real-world personal finance applications, transaction descriptions exhibit continuous concept drift:
- New merchant names emerge (e.g. new local stores, new quick-commerce platforms).
- Ambiguous abbreviations (e.g. *HPCL LPG* vs *HPCL Fuel*, *Spencer Retail* vs *Spencer Supermarket*).
- User-specific vendor relationships (e.g. landlord names, gym memberships, private tutors).

The **Feedback Loop** allows user confirmations and manual category corrections from the UI review queue to flow systematically into the ML pipeline, continuously expanding the labeled training dataset and retraining the model without regressing production accuracy.

```mermaid
flowchart TD
    A[Parsed Bank Statement Rows] --> B[TransactionCategorizer (Logistic Regression)]
    B -->|Confidence >= 0.60| C[Categorized Transaction (Needs Review = False)]
    B -->|Confidence < 0.60| D[Uncategorized Transaction (Needs Review = True)]
    D --> E[User Review Queue / Frontend UI]
    E -->|User confirms / overrides category| F[Feedback Ingestion API /record_feedback]
    F --> G[Sanitization & PII Masking]
    G --> H[(user_feedback_dataset.csv / DB Feedback Table)]
    H -->|Trigger Threshold (e.g. >= 50 reviews)| I[Retraining Pipeline]
    I --> J[Combined Dataset: 720 Base + Feedback]
    J --> K[Candidate Classifier Training]
    K --> L{Holdout Benchmark Gate (Accuracy >= 88%, F1 >= 0.88)}
    L -->|Passes Gate| M[Hot-Reload Production Model: logistic_regression.joblib]
    L -->|Fails Gate| N[Alert & Reject Deployment (Zero Regression)]
```

---

## 2. Feedback Lifecycle Stages

### Stage 1: Inference & Confidence Thresholding
1. When statements or transactions are parsed, `TransactionCategorizer` predicts the class and softmax probability score.
2. If `confidence < 0.60` (or if parse confidence $< 0.85$), the system sets:
   - `category = "Uncategorized"`
   - `needs_review = True`
3. These transactions appear prominently in the user's **Reconciliation / Needs Review** dashboard.

### Stage 2: User Correction & Confirmation
1. In the frontend review view, the user is shown:
   - Original narration (e.g., `POS POORVIKA MOBILES ELECTRONICS`).
   - Suggested category and confidence (e.g. `Shopping (42%)`).
   - Dropdown with the **12 canonical categories**:
     `Dining`, `Entertainment`, `Groceries`, `Medical`, `Miscellaneous`, `Rent`, `Salary Credit`, `Self-Transfer`, `Shopping`, `Subscriptions`, `Transport`, `Utilities`.
2. When the user confirms or changes the category, the frontend invokes `PATCH /api/v1/transactions/{id}` or `POST /api/v1/categorization/feedback`.

### Stage 3: Ingestion & PII Sanitation
To prevent sensitive user information from polluting training artifacts:
- **Phone Number Masking**: 10-digit phone numbers in UPI narrations (`9876543210`) are masked to `XXXXXXXXXX`.
- **Account Number Masking**: 12–16 digit account or card numbers are masked to `XXXXXXXXXXXX`.
- **Whitespace & Control Character Normalization**: Strips excessive spacing, tabs, and unprintable characters.
- **Canonical Label Enforcement**: Strictly rejects any category string not in the 12 canonical categories.

The sanitized record is appended to `data/categorization/user_feedback_dataset.csv` with fields:
`timestamp, user_id, description, confirmed_category, original_predicted_category, original_confidence`.

### Stage 4: Dataset Synthesis & Deduplication
When retraining:
1. The base training dataset (`data/categorization/transactions_labeled_dataset.csv`, 720 samples) is loaded.
2. The user feedback dataset is concatenated.
3. Descriptions are deduplicated (`drop_duplicates(subset=['description'], keep='last')`), giving precedence to the user-confirmed ground truth over initial heuristics.

### Stage 5: Gated Retraining & Safety Barrier
A fundamental risk of automated feedback loops is "data poisoning" or regression on edge cases.
To guarantee safety:
- Retraining is triggered only after a minimum threshold of feedback items (e.g., $\ge 50$ samples in production, $\ge 5$ in testing).
- The candidate model is trained on an 80% train split and evaluated on the 20% holdout benchmark test split.
- **Validation Gate**:
  - `accuracy >= 0.88`
  - `macro_f1 >= 0.88`
- If the candidate fails the gate, the deployment is rejected, the previous model is retained, and an alert is logged.
- If the candidate passes, the model is trained on the full combined dataset and serialized to `data/categorization/models/logistic_regression.joblib`.

### Stage 6: Hot Reloading
- The singleton `get_trained_logistic_classifier()` supports an atomic file swap reload without service restart.
- Downstream endpoints immediately benefit from improved accuracy on user-specific merchant vocabulary.

---

## 3. Data Schema Specifications

### Feedback Record Schema
| Field | Type | Description |
| :--- | :--- | :--- |
| `timestamp` | ISO 8601 String | UTC timestamp of the user review action |
| `user_id` | Integer / String | ID of the reviewing user (scoped per tenant) |
| `description` | String | Sanitized narration text |
| `confirmed_category` | String | Validated canonical category chosen by user |
| `original_predicted_category` | String | Model's top prediction before user review |
| `original_confidence` | Float | Confidence probability score at inference time |

---

## 4. Verification & Testing

The feedback loop is verified in [`backend/tests/test_feedback_loop.py`](file:///F:/TaxPlanner/backend/tests/test_feedback_loop.py):
1. User feedback record ingestion and canonical category validation.
2. PII phone and account number masking sanitization.
3. Combining and deduplicating feedback with the base dataset.
4. Validation gate enforcement rejecting degrading models.
5. Retraining and model deployment when validation criteria are satisfied.
