# Lab 4 — Production Monitoring Analysis Report

**Course**: DDM501 — AI in DevOps, DataOps, MLOps  
**Module**: Production ML Monitoring & Observability  
**Dataset**: UCI Credit Card Default Distribution (30,000 baseline samples)  
**Evaluation Target**: Credit Risk Scoring Microservice  

---

## 1. Executive Summary & Experimental Methodology

In production credit risk scoring, model accuracy cannot be evaluated in real time because credit outcomes (defaults) are delayed by months, and counterfactual outcomes for declined applicants are permanently unobservable. To guarantee operational reliability, compliance, and ethical fairness, we instrumented the credit risk scoring service with Prometheus metrics, statistical population drift monitoring (Population Stability Index - PSI), demographic fairness tracking (selection rate parity), and explainability latency tracking.

We conducted controlled load tests with $N = 400$ requests per profile, resetting the sliding observation window ($W = 400$, minimum valid statistical threshold $W_{min} = 200$) between test cycles. The five evaluated profiles are:
1. **Normal**: Baseline applicant population sampled directly from the training distribution.
2. **Drifted ($\text{strength} = 0.05$)**: A subtle demographic and capacity shift.
3. **Drifted ($\text{strength} = 0.15$)**: A moderate population shift.
4. **Drifted (Full, $\text{strength} = 1.0$)**: Complete population shift (younger applicants, constrained credit limits, higher revolving balance utilization).
5. **Unfair**: Targeted repayment distortion applied strictly to group `SEX = 1`, holding population baseline constant.

---

## 2. Experimental Results & Metric Summary

| Profile | Mean Score | APPROVE (%) | REVIEW (%) | DECLINE (%) | Drift Score (PSI) | Status | Fairness Gap |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Normal** | 0.2355 | 77.8% | 14.2% | 8.0% | **0.0301** | Stable | **0.0188** |
| **Drifted (0.05)** | 0.2437 | 77.5% | 14.0% | 8.5% | **0.1885** | Moderate | **0.0149** |
| **Drifted (0.15)** | 0.2609 | 74.0% | 16.2% | 9.8% | **1.1518** | Significant | **0.0357** |
| **Drifted (Full)** | 0.5897 | 15.5% | 29.8% | 54.8% | **4.2510** | Significant | **0.0376** |
| **Unfair** | 0.3966 | 52.2% | 15.8% | 32.0% | **0.3526** | Significant | **0.7222** |

### Per-Feature PSI Breakdown

| Monitored Feature | Normal | Drifted (0.05) | Drifted (0.15) | Drifted (Full) | Unfair |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `payment_ratio` | 0.0131 | **0.1885** | **1.1518** | **4.2510** | 0.2879 |
| `utilisation_ratio` | 0.0288 | 0.0673 | **0.2611** | **3.0921** | 0.0288 |
| `LIMIT_BAL` | 0.0152 | 0.0512 | 0.0572 | **2.0426** | 0.0152 |
| `AGE` | 0.0301 | 0.0366 | 0.0446 | **1.7084** | 0.0301 |
| `PAY_0` | 0.0059 | 0.0059 | 0.0059 | 0.8262 | 0.2791 |
| `max_delay` | 0.0036 | 0.0036 | 0.0036 | 0.7825 | **0.3526** |

---

## 3. Analysis & Responses to Core Evaluation Questions

### Question 1: Which signal moved first, and by how much before anything else did?

**Empirical Finding**: **Input feature drift (`ml_feature_drift_psi` on `payment_ratio`) moved first, dramatically outpacing all service, decision, and score metrics.**

- **At subtle shift ($\text{strength} = 0.05$)**:
  - The business-level decision mix was essentially indistinguishable from normal operation: `APPROVE` was $77.5\%$ (vs $77.8\%$ baseline), `REVIEW` was $14.0\%$ (vs $14.2\%$ baseline), and `DECLINE` was $8.5\%$ (vs $8.0\%$ baseline). A business stakeholder reviewing approval rates or underwriter queues would observe zero operational anomaly ($< 0.5\%$ fluctuation).
  - The mean predicted default probability shifted by only $+0.0082$ (from $0.2355$ to $0.2437$, a modest $+3.48\%$ variation).
  - In direct contrast, `ml_feature_drift_psi{feature="payment_ratio"}` surged from **$0.0131$ to $0.1885$**, representing a **$1,339\%$ increase** and immediately crossing into the **Moderate Drift band ($0.10 \le \text{PSI} < 0.25$)**. The aggregate drift score climbed from $0.0301$ to $0.1885$ (**$+526\%$ increase**).

**Engineering Takeaway**: Input drift monitoring serves as an early warning proxy. When applicant characteristics begin shifting, the input distribution breaches stability thresholds weeks or months before the model's output score distribution or manual underwriter decline counts deviate measurably.

---

### Question 2: Which signal would have paged you, given your own alert thresholds?

**Alerting Policy Architecture**:
In `monitoring/prometheus/alerts/ml_alerts.yml`, our alerting rules adhere to strict SRE disciplines:
- `ModerateFeatureDrift` ($\text{PSI} \ge 0.10$ for $15\text{m}$): `severity: warning` (non-paging, ticket generated for investigation).
- `SignificantFeatureDrift` ($\text{PSI} \ge 0.25$ for $15\text{m}$): `severity: critical` (pages on-call engineer for potential model invalidation).
- `FairnessGapWidened` ($\text{gap} > 0.10$ for $20\text{m}$): `severity: critical`, `signal: fairness` (pages on-call engineer for regulatory compliance violation).
- `DecisionMixShift` ($\text{DECLINE rate} > 20\%$ for $30\text{m}$): `severity: warning`.

**Simulation Behavior**:
1. **Under `drifted (0.05)`**:
   - The drift score reaches $0.1885$.
   - **No pager is triggered**. The `ModerateFeatureDrift` rule fires as a `warning`, notifying the data science team via Slack/ticket to investigate underlying demographic shifts without disturbing an engineer at night.
2. **Under `drifted (0.15)` & `drifted (Full)`**:
   - At strength $0.15$, drift score reaches $1.1518 \ge 0.25$. At full drift, it hits $4.2510$.
   - **`SignificantFeatureDrift` PAGES ON-CALL (`severity: critical`)**.
   - Under full drift, `DecisionMixShift` also fires (decline rate = $54.8\% > 20\%$) and `HighErrorRate` remains clear because the service processes requests correctly.
3. **Under `unfair`**:
   - **`FairnessGapWidened` PAGES ON-CALL (`severity: critical`)** because the selection rate gap reaches **$0.7222 \gg 0.10$**.
   - Concurrently, `SignificantFeatureDrift` pages because drift score is $0.3526 \ge 0.25$.

---

### Question 3: Which signal told you what was wrong, rather than only that something was? Compare `drifted` and `unfair` specifically.

**The Diagnostic Problem**:
Both the `drifted (0.15)` and `unfair` profiles produce elevated aggregate drift scores in the significant band ($1.1518$ and $0.3526$ respectively), and both cause elevated decline rates ($9.8\%$ and $32.0\%$). An aggregate drift metric merely signals *that* an anomaly exists. It cannot determine root cause.

**What Distinguishes Them on the Model Behaviour Dashboard**:

1. **Feature-Level PSI Breakdown (`ml_feature_drift_psi`)**:
   - In `drifted` profiles, financial capacity features lead the drift:
     - `payment_ratio` ($\text{PSI} = 1.1518$ to $4.2510$)
     - `utilisation_ratio` ($\text{PSI} = 0.2611$ to $3.0921$)
     - `LIMIT_BAL` ($\text{PSI} = 0.0572$ to $2.0426$)
     - `AGE` ($\text{PSI} = 0.0446$ to $1.7084$)
     - Crucially, delinquency history (`PAY_0`, `max_delay`) remains virtually unchanged at low strengths ($\text{PSI} = 0.0036 \text{ to } 0.0059$).
     - **Diagnosis**: The incoming demographic consists of younger borrowers with lower credit lines and high credit card utilization (e.g., student or young professional credit card campaign).
   - In the `unfair` profile, demographic and capacity features are **completely stable**:
     - `AGE`: $\text{PSI} = 0.0301$ (identical to normal baseline)
     - `utilisation_ratio`: $\text{PSI} = 0.0288$ (baseline)
     - `LIMIT_BAL`: $\text{PSI} = 0.0152$ (baseline)
     - Drift is entirely driven by repayment history: `max_delay` ($\text{PSI} = 0.3526$) and `PAY_0` ($\text{PSI} = 0.2791$).
     - **Diagnosis**: Repayment records are deteriorating while applicant demographics are identical.

2. **Fairness & Demographic Selection Rates (`ml_fairness_gap` & `ml_selection_rate`)**:
   - In `drifted` profiles, the fairness gap remains flat at **$0.0357 - 0.0376$** (comparable to baseline $0.0188$). Both genders experience the economic shift proportionally.
   - In the `unfair` profile, the fairness gap explodes to **$0.7222$** ($72.2\%$ disparate impact).
     - Group 1 (Male) selection rate: **$78.6\%$** flagged for review or decline.
     - Group 2 (Female) selection rate: **$6.4\%$** flagged for review or decline.
     - **Definitive Diagnosis**: The model or upstream data pipeline is applying disparate treatment or biased penalties to Group 1, creating an acute regulatory fairness violation.

---

## 4. Verification Checklist & Deliverables

- [x] **Task 1-4**: `app/monitoring.py` PSI formula, drift scoring, fairness gap, and gauge publication.
- [x] **Task 5-8**: `app/main.py` observation pipeline with feature derivation, `/metrics`, `/monitoring`, and `/explain`.
- [x] **Task 9**: `app/middleware.py` Prometheus HTTP metrics with route templates and latency recording.
- [x] **Task 10**: `app/explain.py` TreeExplainer integration returning human-readable feature values and directions.
- [x] **Task 11**: `scripts/make_reference.py` Quantile bin reference generation with open outer edges.
- [x] **Task 12**: `monitoring/prometheus/alerts/ml_alerts.yml` 7 alert rules matching promtool unit tests.
- [x] **Task 13**: `monitoring/grafana/dashboards/model-behaviour.json` full dashboard provisioning.
- [x] **CI Test Suite**: 79/79 unit tests passing ($100\%$), test coverage $91.47\%$ ($> 85\%$ threshold).
- [x] **Written Analysis**: Complete report answering all 3 core evaluation questions with exact empirical data.
