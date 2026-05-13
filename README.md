# Apollo Metrics

**AI-Powered Full-Stack Data Analytics Platform**

Apollo Metrics is a professional portfolio-level AI/ML/Data Science project that enables users to upload CSV datasets and automatically perform data cleaning, exploratory data analysis (EDA), visualization, machine learning model training, natural language dataset querying, LLM-powered explanations, and PDF report generation.

Built with Python Flask, MySQL, HTML, CSS, JavaScript, and Chart.js, Apollo Metrics demonstrates a complete end-to-end data analytics workflow suitable for GitHub portfolio, resume, final-year project presentation, and technical interviews.

---

## Problem Statement

Many users and organizations have CSV data but cannot easily clean, understand, visualize, model, or extract insights from it. Traditional data analysis requires expertise in Python, Pandas, statistics, machine learning, and data visualization. Apollo Metrics solves this by acting as an **AI Data Analyst Agent** that automates the entire data analysis workflow from raw CSV upload to final insights and professional reports.

---

## Project Details

- **User Registration & Login**: Secure authentication system with password hashing and session management.
- **CSV Upload**: Upload datasets with automatic metadata extraction (rows, columns, data types, missing values).
- **Data Cleaning**: Automatic detection of numerical, categorical, and date columns. Missing values are filled (median for numerical, mode for categorical). Duplicate removal and IQR-based outlier detection.
- **Auto EDA**: Comprehensive exploratory analysis including statistical summaries, correlation matrices, categorical analysis, and auto-generated insights.
- **Chart Generation**: Dynamic bar, line, pie, histogram, scatter, box plot, and correlation heatmap generation using Chart.js.
- **Machine Learning**: Automatic task detection (classification, regression, clustering). Multiple model training with comparison metrics. Best model selection and saving.
- **LLM-Powered Q&A**: Ask natural language questions about datasets. Backend computes safe statistics and sends summarized context to LLM API.
- **LLM Model Explanation**: After ML training, LLM explains model performance, metrics, feature importance, and business implications.
- **PDF Report Generation**: Professional reports combining dataset overview, cleaning summary, EDA insights, ML results, and AI-generated recommendations.
- **MySQL Storage**: All users, uploads, analysis history, queries, model results, and reports are stored in MySQL.
- **Light/Dark Theme**: Full theme support with localStorage persistence across all pages.
- **Dashboard Analytics**: Central dashboard showing statistics, recent activity, and quick actions.

---

## Key Features

- Secure user registration and login with password hashing
- CSV dataset upload with validation and metadata extraction
- Automatic data cleaning (missing values, duplicates, outliers)
- Comprehensive automated EDA with insights generation
- Dynamic chart generation (7 chart types)
- Classification, regression, and clustering ML models
- Natural language query over datasets via LLM
- LLM-powered ML explanation and business recommendations
- Downloadable PDF analysis reports
- Light and dark theme support
- MySQL-based history tracking for all activities
- Automatic database setup using Python script
- Responsive design for desktop and mobile

---

## Tech Stack

### Frontend
- **HTML5** - Structure and markup
- **CSS3** - Styling with CSS variables for theming
- **JavaScript** - Client-side logic and API interactions
- **Chart.js** - Dynamic chart rendering

### Backend
- **Python Flask** - Web framework and REST API
- **Pandas** - Data manipulation and analysis
- **NumPy** - Numerical computing
- **Scikit-learn** - Machine learning models
- **Joblib** - Model persistence
- **fpdf** - PDF report generation
- **Requests** - HTTP client for LLM API calls

### Database
- **MySQL** - Relational database for persistent storage

### AI
- **LLM API** - Configurable through .env (supports any OpenAI-compatible API)

---

## System Architecture

```
User Interface (HTML/CSS/JS)
        |
        v
Flask Backend (REST API)
        |
        +---> Data Processing Services (Pandas, NumPy)
        |         |
        |         +---> Cleaning Service
        |         +---> EDA Service
        |         +---> Chart Service
        |
        +---> ML Service (Scikit-learn)
        |
        +---> LLM Service (API calls)
        |
        +---> Report Service (fpdf)
        |
        v
MySQL Database (Users, Uploads, Analysis, Queries, Models, Reports)
```

---

## Final Folder Structure

```
apollo-metrics/
├── app.py                          # Main Flask application entry point
├── setup_database.py               # Automatic database setup script
├── schema.sql                      # Manual MySQL schema for reference
├── requirements.txt                # Python package dependencies
├── .env.example                    # Environment variable template
├── README.md                       # Project documentation (this file)
│
├── backend/
│   ├── __init__.py
│   ├── config.py                   # Configuration from .env
│   ├── database/
│   │   ├── __init__.py
│   │   └── db.py                   # Database connection and initialization
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth_routes.py          # Registration, login, logout
│   │   ├── upload_routes.py        # File upload and management
│   │   ├── eda_routes.py           # EDA and data cleaning
│   │   ├── chart_routes.py         # Chart generation
│   │   ├── ml_routes.py            # ML model training
│   │   ├── query_routes.py         # LLM-powered Q&A
│   │   ├── report_routes.py        # PDF report generation
│   │   └── dashboard_routes.py     # Dashboard summary
│   ├── services/
│   │   ├── __init__.py
│   │   ├── cleaning_service.py     # Data cleaning logic
│   │   ├── eda_service.py          # EDA computation
│   │   ├── chart_service.py        # Chart data preparation
│   │   ├── ml_service.py           # ML model training
│   │   ├── llm_service.py          # LLM API interaction
│   │   └── report_service.py       # PDF report generation
│   └── utils/
│       ├── __init__.py
│       └── helpers.py              # Utility functions
│
├── static/
│   ├── css/
│   │   └── style.css               # Complete styling with themes
│   └── js/
│       ├── auth.js                 # Login/Register logic
│       ├── theme.js                # Theme management
│       ├── dashboard.js            # Dashboard page logic
│       ├── upload.js               # Upload page logic
│       ├── eda.js                  # EDA page logic
│       ├── charts.js               # Chart generation logic
│       ├── ml.js                   # ML training logic
│       ├── query.js                # AI query logic
│       └── reports.js              # Reports page logic
│
├── templates/
│   ├── login.html                  # Login page
│   ├── register.html               # Registration page
│   ├── dashboard.html              # Main dashboard
│   ├── upload.html                 # CSV upload page
│   ├── eda.html                    # EDA page
│   ├── charts.html                 # Chart generation page
│   ├── ml.html                     # ML training page
│   ├── query.html                  # Ask AI page
│   └── reports.html                # Reports page
│
├── sample_data/
│   ├── sales_data.csv              # Sales transaction sample data
│   ├── customer_churn.csv          # Customer churn sample data
│   └── employee_data.csv           # Employee attrition sample data
│
├── uploads/                        # Uploaded CSV files (auto-created)
├── cleaned/                        # Cleaned datasets (auto-created)
├── models/                         # Saved ML models (auto-created)
└── reports/                        # Generated PDF reports (auto-created)
```

---

## Database Tables

| Table | Purpose |
|-------|---------|
| **users** | Stores registered user information (name, email, hashed password) |
| **uploads** | Tracks uploaded CSV files with metadata (rows, columns, file path) |
| **analysis_history** | Stores cleaning and analysis results for each upload |
| **user_queries** | Records all AI questions and answers for each dataset |
| **model_results** | Stores trained model metadata, metrics, and file paths |
| **reports** | Tracks generated PDF reports with download paths |

---

## Algorithm: Apollo Metrics Data Analysis Workflow

**Step 1**: User registers or logs into the system.
**Step 2**: The system authenticates the user using hashed password verification.
**Step 3**: User uploads a CSV file.
**Step 4**: Backend validates the uploaded file format and stores it securely.
**Step 5**: Pandas reads the CSV file and extracts metadata such as rows, columns, data types, missing values, and duplicate rows.
**Step 6**: The data cleaning service detects numerical, categorical, and date columns.
**Step 7**: Missing numerical values are filled using median.
**Step 8**: Missing categorical values are filled using mode or "Unknown".
**Step 9**: Duplicate rows are removed.
**Step 10**: Outliers are detected using the IQR method.
**Step 11**: Cleaned dataset is saved separately.
**Step 12**: EDA service generates statistical summaries, correlation matrix, categorical summaries, and insights.
**Step 13**: Chart service generates visualization data for Chart.js.
**Step 14**: User selects ML task or target column.
**Step 15**: ML service preprocesses the data, trains suitable models, evaluates them, and selects the best model.
**Step 16**: Model results are saved in MySQL.
**Step 17**: User asks natural language questions about the dataset.
**Step 18**: Backend computes safe dataset statistics and sends summarized context to the LLM.
**Step 19**: LLM generates professional explanation and business insights.
**Step 20**: User generates a PDF report.
**Step 21**: Report service combines dataset summary, cleaning report, EDA insights, ML results, and LLM explanation into a downloadable PDF.
**Step 22**: All uploads, queries, model results, and reports are stored in MySQL for future access.

---

## Run Algorithm

**Step 1**: Clone or download the project.
**Step 2**: Open the project folder in VS Code.
**Step 3**: Open terminal in the project root.
**Step 4**: Create a Python virtual environment.
**Step 5**: Activate the virtual environment.
**Step 6**: Install dependencies using `requirements.txt`.
**Step 7**: Copy `.env.example` to `.env`.
**Step 8**: Add your MySQL credentials and LLM API key in `.env`.
**Step 9**: Start MySQL server (using XAMPP, WAMP, or local MySQL).
**Step 10**: Run `python setup_database.py` to create the database and tables.
**Step 11**: Run `python app.py` to start the Flask backend.
**Step 12**: Open `http://localhost:5000` in your browser.
**Step 13**: Register a new user account.
**Step 14**: Log in.
**Step 15**: Upload a sample CSV and test all modules.

---

## Installation and Running Instructions

### Prerequisites

- Python 3.8+
- MySQL server running locally
- VS Code (recommended) or any code editor

### Windows PowerShell Setup

```powershell
# Clone or navigate to the project
cd apollo-metrics

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env from example
copy .env.example .env
```

### Configure .env File

Edit the `.env` file and add your configuration:

```env
# Free provider: Get API key at https://console.groq.com (no credit card)
LLM_API_KEY=gsk_your_groq_api_key_here
LLM_API_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL_NAME=llama-3.3-70b-versatile

DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=apollo_metrics

SECRET_KEY=generate_a_random_secret_key_here
```

> **Note**: Apollo Metrics supports any OpenAI-compatible LLM API. **Groq is recommended for free usage** (sign up at https://console.groq.com, no credit card needed). You can also use OpenAI, Cerebras, or any other provider by changing `LLM_API_BASE_URL`, `LLM_API_KEY`, and `LLM_MODEL_NAME`.

### Automatic Database Setup (Recommended)

```powershell
python setup_database.py
```

This script will:
1. Connect to MySQL using credentials from `.env`
2. Create the `apollo_metrics` database if it doesn't exist
3. Create all 6 required tables
4. Create required folders: `uploads/`, `cleaned/`, `models/`, `reports/`

### Manual Database Setup (Alternative)

```bash
# Using MySQL CLI
mysql -u root -p
source schema.sql
```

Or via PowerShell:

```powershell
cmd /c "mysql -u root -p < schema.sql"
```

### Run the Application

```powershell
python app.py
```

The application will start at `http://localhost:5000`.

---

## API Routes

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register a new user |
| POST | `/api/auth/login` | Log in |
| GET | `/api/auth/logout` | Log out |
| GET | `/api/auth/me` | Get current user info |

### Upload

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload` | Upload a CSV file |
| GET | `/api/uploads` | List all uploads |
| GET | `/api/uploads/<id>` | Get upload details |

### EDA

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/eda/<upload_id>` | Run EDA and data cleaning |

### Charts

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/charts/generate` | Generate chart data |

### Machine Learning

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/ml/train` | Train ML models |
| GET | `/api/ml/results/<upload_id>` | Get ML results |

### Ask AI

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/query` | Ask a question about dataset |
| GET | `/api/query/history/<upload_id>` | Get query history |

### Reports

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/reports/generate` | Generate PDF report |
| GET | `/api/reports` | List all reports |
| GET | `/api/reports/download/<report_id>` | Download PDF report |

### Dashboard

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard/summary` | Get dashboard statistics |

---

## Sample Data

The project includes three sample CSV files in the `sample_data/` folder:

### 1. sales_data.csv
- **Columns**: date, product, region, units_sold, revenue, discount, profit
- **Description**: 52 records of sales transactions across products and regions
- **Use cases**: Trend analysis, product performance, regional analysis, regression

### 2. customer_churn.csv
- **Columns**: customer_id, gender, age, tenure, monthly_charges, contract_type, churn
- **Description**: 60 records of customer data with churn labels
- **Use cases**: Classification (predict churn), customer segmentation

### 3. employee_data.csv
- **Columns**: employee_id, department, age, salary, experience_years, performance_score, attrition
- **Description**: 50 records of employee data with attrition labels
- **Use cases**: Classification (predict attrition), regression (predict salary), clustering

---

## Screenshots

| Page | Description |
|------|-------------|
| Login Page | User authentication with email and password |
| Register Page | New user registration with name, email, password |
| Dashboard | Central hub with statistics, recent activity, quick actions |
| Upload Page | CSV file upload with drag-and-drop and preview |
| EDA Page | Automated exploratory data analysis with insights |
| Charts Page | Dynamic chart generation with multiple chart types |
| ML Training Page | Machine learning model training and comparison |
| Ask AI Page | Natural language questions about datasets |
| Reports Page | PDF report generation and download |

---

## Future Enhancements

- Role-based admin dashboard with user management
- Cloud deployment (AWS, GCP, or Azure)
- Advanced AutoML with hyperparameter tuning
- Additional chart types (area, radar, bubble)
- Support for more LLM providers (Claude, Gemini, local models)
- Dataset comparison and merging
- Team collaboration features
- Export to PowerPoint presentations
- Scheduled automated analysis reports
- Real-time data streaming support

---

## Resume Bullet Points

- **Developed Apollo Metrics**, a full-stack AI-powered data analyst platform using Python Flask, MySQL, HTML, CSS, JavaScript, and Chart.js, enabling automated CSV data analysis from upload to insights.
- **Implemented automated data cleaning**, EDA, outlier detection, and visualization pipeline using Pandas, NumPy, and Scikit-learn, processing datasets with 50+ columns and thousands of rows.
- **Integrated LLM API support** through secure .env configuration to generate natural language dataset insights, ML model explanations, and business recommendations.
- **Built secure user authentication** with Werkzeug password hashing, session management, and MySQL-based history tracking for all user activities.
- **Designed a responsive light/dark themed analytics dashboard** with sidebar navigation, real-time statistics, and 7 chart types suitable for real-world data science workflows.
- **Developed automated ML pipeline** supporting classification (Logistic Regression, Decision Tree, Random Forest, SVM), regression (Linear, Decision Tree, Random Forest), and clustering (K-Means) with performance metrics.
- **Created PDF report generation** system using fpdf that combines dataset summary, cleaning report, EDA insights, ML results, and AI-generated business recommendations into professional documents.

---

## License

This project is for educational and portfolio purposes.

---

## Author

Apollo Metrics - AI-Powered Data Analytics Platform
