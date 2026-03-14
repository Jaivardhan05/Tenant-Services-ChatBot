# Tenant Services Chatbot

A full-stack property management portal built with Streamlit, 
Supabase, ScaleDown compression and Google Gemini AI. Designed 
for Indian residential properties — supports tenant login, admin 
dashboard, AI chat assistant, rent payments, complaints, and 
community announcements.

---

## Features

### Tenant Portal
- Secure login and self-registration
- Personalized dashboard with rent status, lease info, building alerts
- AI chat assistant answering questions from real lease and policy documents
- Rent payment portal with card details form
- Payment history tracking
- Feedback submission
- Complaint filing with reference number

### Admin Dashboard
- Separate admin login with elevated access
- Overview metrics — total tenants, rent collected, pending payments, open complaints
- Tenant management table with overdue status highlighting
- Full payment history and manual payment recording
- Complaint resolution system
- Community announcement posting

### AI & Compression
- ScaleDown API compresses knowledge base before every Gemini call (~50% token reduction)
- Google Gemini answers questions exclusively from lease and policy documents
- Compression stats shown below every chat response
- Guardrails prevent hallucination — AI only answers from injected documents

---

## Tech Stack

- Python 3.9+
- Streamlit
- Supabase (PostgreSQL cloud database)
- Google Generative AI (gemini-2.5-flash)
- ScaleDown API (prompt compression)
- bcrypt (password hashing)
- python-dotenv
- pandas

---

## Project Structure

tenant-services-chatbot/
├── app.py                      # Main Streamlit application
├── database.py                 # Supabase database functions
├── requirements.txt            # Python dependencies
├── .env                        # API keys (not committed)
├── .env.example                # Environment variable template
├── data/
│   ├── lease_agreement.txt     # Lease document knowledge base
│   └── building_policies.txt   # Building rules knowledge base
└── README.md

---

## Setup Instructions

### 1. Clone the repository

git clone https://github.com/Jaivardhan05/Tenant-Services-ChatBot.git
cd Tenant-Services-ChatBot

### 2. Create and activate a virtual environment

python3 -m venv venv
source venv/bin/activate

### 3. Install dependencies

pip install -r requirements.txt

### 4. Set up Supabase

1. Create a free project at supabase.com
2. Go to SQL Editor and run the schema setup:

```sql
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'tenant',
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    unit TEXT NOT NULL,
    phone TEXT,
    rent REAL DEFAULT 1850,
    balance REAL DEFAULT 0,
    lease_end TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE payments (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    tenant_name TEXT,
    unit TEXT,
    amount REAL,
    date TEXT,
    status TEXT DEFAULT 'Paid',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE complaints (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    tenant_name TEXT,
    unit TEXT,
    subject TEXT,
    category TEXT,
    message TEXT,
    status TEXT DEFAULT 'Open',
    date TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE feedback (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    tenant_name TEXT,
    unit TEXT,
    topic TEXT,
    rating INTEGER,
    details TEXT,
    follow_up BOOLEAN DEFAULT FALSE,
    date TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE announcements (
    id BIGSERIAL PRIMARY KEY,
    title TEXT,
    message TEXT,
    priority TEXT DEFAULT 'Normal',
    date TIMESTAMPTZ DEFAULT NOW()
);
```

3. Create the admin account — run this in SQL Editor:

```sql
INSERT INTO users 
(username, password_hash, role, name, email, unit, phone)
VALUES (
    'admin',
    'YOUR_BCRYPT_HASH_HERE',
    'admin',
    'Property Manager',
    'admin@riversideapts.com',
    'Office',
    '+91 98765 43210'
);
```

Generate your bcrypt hash by running:
```bash
python3 -c "import bcrypt; print(bcrypt.hashpw('YourPassword'.encode(), bcrypt.gensalt()).decode())"
```

### 5. Set up environment variables

cp .env.example .env

Fill in your keys in .env:

```
SCALEDOWN_API_KEY=your_scaledown_key_here
SCALEDOWN_API_URL=https://api.scaledown.xyz/compress/raw/
GEMINI_API_KEY=your_gemini_key_here
SUPABASE_URL=your_supabase_project_url_here
SUPABASE_KEY=your_supabase_anon_key_here
PORT=3001
PROPERTY_NAME=Riverside Apartments
UPLOAD_DIR=./uploads
MAX_FILE_SIZE_MB=10
```

### 6. Run the app

streamlit run app.py

Open your browser at http://localhost:8501

---

## API Keys

Key                  | Where to get it              | Required
SCALEDOWN_API_KEY    | scaledown.xyz dashboard      | Yes
GEMINI_API_KEY       | aistudio.google.com          | Yes
SUPABASE_URL         | supabase.com project settings| Yes
SUPABASE_KEY         | supabase.com project settings| Yes

---

## How It Works

### Authentication Flow
1. Tenant registers with name, email, phone, unit number
2. Password stored as bcrypt hash in Supabase
3. On login, bcrypt verifies password against stored hash
4. Role-based routing — admin sees management dashboard, tenant sees personal portal

### AI Chat Flow
1. Tenant types a question
2. ScaleDown API compresses the full knowledge base + question
3. Compressed context sent to Gemini with document-only instructions
4. Gemini returns precise answer from lease and building policies
5. Token compression stats shown below each response

---

## Default Credentials

Role     | Username | Password
Admin    | admin    | Set during setup (see step 4)
Tenant   | Register via Create Account tab

---

## Knowledge Base

The chatbot answers from two documents in the /data folder:

- lease_agreement.txt — rent, deposits, pets, parking, 
  maintenance, move-out, early termination
- building_policies.txt — quiet hours, amenities, smoking, 
  visitors, emergencies, fines

To use for a different property, update these two files.

---

## Screenshots

Add screenshots here after deployment

---

## License

MIT License — free to use and modify
