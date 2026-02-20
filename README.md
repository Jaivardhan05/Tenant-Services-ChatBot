# Tenant Services Chatbot

This workspace contains a Node.js Express server (`/server`) and a minimal React client (`/client`) for a tenant services chatbot demo.

Quick start:

1. Install server dependencies:

```bash
cd server
npm install
npm run dev
---
# Tenant Services Chatbot

A property management chatbot built with Streamlit, powered by ScaleDown compression and Google Gemini AI. Helps tenants get instant answers about their lease, building policies, maintenance, payments and amenities.

---

## Features

- AI chat assistant powered by Google Gemini
- ScaleDown API compresses knowledge base before every AI call (reducing token usage by ~50%)
- Dashboard with rent status, lease info, and building alerts
- Rent & Payments history panel
- Feedback form with session tracking
- Sidebar quick actions for common tenant questions
- Dark themed professional UI

---

## Tech Stack

- Python 3.9+
- Streamlit
- Google Generative AI (gemini-2.5-flash)
- ScaleDown API (prompt compression)
- python-dotenv

---

## Project Structure

tenant-services-chatbot/
├── app.py                      # Main Streamlit application
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

git clone https://github.com/yourusername/tenant-services-chatbot.git
cd tenant-services-chatbot

### 2. Create and activate a virtual environment

python3 -m venv venv
source venv/bin/activate

### 3. Install dependencies

pip install -r requirements.txt

### 4. Set up environment variables

Copy the example file and fill in your API keys:

cp .env.example .env

Open .env and add your keys:

SCALEDOWN_API_KEY=your_scaledown_key_here
SCALEDOWN_API_URL=https://api.scaledown.xyz/compress/raw/
GEMINI_API_KEY=your_gemini_key_here
PORT=3001
PROPERTY_NAME=Riverside Apartments
UPLOAD_DIR=./uploads
MAX_FILE_SIZE_MB=10

### 5. Run the app

streamlit run app.py

Open your browser at http://localhost:8501

---

## API Keys

Key                  | Where to get it           | Required
SCALEDOWN_API_KEY    | scaledown.xyz dashboard   | Yes
GEMINI_API_KEY       | aistudio.google.com       | Yes

---

## How It Works

1. Tenant types a question in the chat
2. ScaleDown API compresses the full knowledge base and question to reduce token count
3. Compressed context is sent to Gemini with instructions to answer only from the documents
4. Gemini returns a precise answer based on the lease and building policies
5. Compression stats are shown below each answer

---

## Knowledge Base

The chatbot answers questions using two documents in the /data folder:

- lease_agreement.txt — covers rent, deposits, pets, parking, maintenance responsibilities, move-out procedures, and early termination
- building_policies.txt — covers quiet hours, amenity hours, smoking policy, visitor rules, emergency procedures, and fine schedule

To customize for a different property, update these two files with your own lease and policy details.

---

## Screenshots

Add screenshots here after deployment

---

## License

MIT License — free to use and modify (See <attachments> above for file contents. You may not need to search or read the file again.)
