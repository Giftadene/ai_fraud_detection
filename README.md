# 🛡️ AI Fraud Detection System

> A web-based machine learning system for detecting suspicious online banking and mobile money transactions in real time.

The **AI Fraud Detection System** is an intelligent financial-security application designed to identify potentially fraudulent transactions before they are completed. It combines transaction-level information, customer transaction history, and contextual data to generate a fraud prediction and risk score for each transaction.

The system is designed for online banking platforms, mobile money transfer services, digital wallets, and other electronic payment environments.

---

## ✨ Key Features

* Real-time fraud prediction for online transactions
* Machine learning-based risk classification
* Fraud risk score from **0 to 100**
* Transaction monitoring dashboard
* Suspicious transaction alerts
* User transaction history analysis
* Device and location-based fraud checks
* Merchant category analysis
* Fraud analyst review support
* Transaction search and filtering
* Model performance monitoring
* Secure user authentication and access control
* Responsive web interface

---

## 🎯 Problem Statement

Online banking and mobile money systems are increasingly exposed to fraud such as account takeover, unauthorized transfers, unusual spending patterns, device spoofing, and rapid repeated transactions.

Traditional rule-based systems often fail because fraudsters change their methods frequently. This project applies Machine Learning to learn transaction patterns and identify suspicious behaviour more accurately.

---

## 🧠 Machine Learning Approach

The system treats fraud detection as a **binary classification problem**.

| Class | Meaning                |
| ----- | ---------------------- |
| `0`   | Legitimate Transaction |
| `1`   | Fraudulent Transaction |

The model analyses several categories of features before predicting whether a transaction is safe, suspicious, or fraudulent.

### Transaction-Level Features

* Transaction amount
* Transaction date and time
* Transaction location
* Transaction type
* Source account
* Destination account
* Transaction frequency
* Transaction velocity

### User Historical Features

* Average transaction amount
* Daily transaction frequency
* Weekly transaction frequency
* Monthly transaction frequency
* Previous fraud history
* Account age
* Normal transaction time
* Typical transaction location

### Contextual Features

* Merchant category
* Device type
* Device ID
* Browser type
* Operating system
* IP address
* VPN detection
* New or unknown device usage

---

## 📊 Fraud Risk Levels

| Risk Score | Risk Level    | System Action           |
| ---------: | ------------- | ----------------------- |
|       0-30 | Low Risk      | Approve transaction     |
|      31-60 | Medium Risk   | Monitor transaction     |
|      61-80 | High Risk     | Hold for analyst review |
|     81-100 | Critical Risk | Block transaction       |

---

## 🛠️ Technology Stack

| Category         | Technologies                         |
| ---------------- | ------------------------------------ |
| Frontend         | HTML, CSS, JavaScript, Bootstrap     |
| Backend          | Python, FastAPI / Flask              |
| Machine Learning | Scikit-learn, XGBoost, Pandas, NumPy |
| Database         | SQLite / MySQL                       |
| Model Storage    | Joblib / Pickle                      |
| Deployment       | Docker, Hugging Face Spaces          |
| Version Control  | Git and GitHub                       |

---

## 🚀 Installation and Local Setup

### Clone the Repository

```bash
git clone https://github.com/Giftadene/ai-fraud-detection.git
cd ai-fraud-detection
```

### Create a Virtual Environment

```bash
python -m venv venv
```

**Windows**

```bash
venv\Scripts\activate
```

**Linux/macOS**

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run the Application

For FastAPI:

```bash
uvicorn app:app --reload
```

For Flask:

```bash
python app.py

```

---

## 🔍 Sample Prediction Workflow

1. A customer initiates an online banking or mobile money transaction.
2. The system receives the amount, location, time, device information, and merchant category.
3. Historical customer behaviour is retrieved.
4. Features are processed and passed to the machine learning model.
5. The model predicts whether the transaction is legitimate or fraudulent.
6. A risk score is generated.
7. The system approves, monitors, holds, or blocks the transaction.
8. Suspicious transactions are displayed on the fraud analyst dashboard.

---

## 📈 Model Evaluation Metrics

* Accuracy
* Precision
* Recall
* F1-Score
* ROC-AUC Score
* Confusion Matrix
* False Positive Rate
* False Negative Rate

> Recall is especially important because the system must identify as many fraudulent transactions as possible.

---

## 🔐 Security Considerations

* Secure authentication
* Password hashing
* Role-based access control
* HTTPS deployment
* Input validation
* Audit logging
* Secure database access
* Environment variables for sensitive credentials
* Protection against unauthorized access

> This project is intended for academic, research, prototype, and demonstration purposes. A real banking deployment requires regulatory compliance, security testing, encryption controls, and formal approval from relevant financial authorities.

---

## 🔮 Future Improvements

* Real-time transaction streaming with Apache Kafka
* Deep learning fraud detection using LSTM networks
* Graph-based fraud ring detection
* Explainable AI using SHAP
* SMS and email fraud alerts
* Mobile application integration
* Biometric verification
* Multi-factor authentication
* Automatic model retraining
* PostgreSQL cloud database deployment

---

## 👩‍💻 Author

**Gift Adene**
Machine Learning and Web Application Developer

GitHub: https://github.com/Giftadene

---

## 📄 License

This project is licensed under the MIT License.

---

## ⭐ Support

If you find this project useful, kindly give the repository a star.
