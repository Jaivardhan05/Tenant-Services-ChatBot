import os
import bcrypt
from supabase import create_client, Client
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def register_user(username, password, name, email, unit, phone):
    try:
        # Check if username already exists
        existing = supabase.table("users")\
            .select("id")\
            .eq("username", username)\
            .execute()
        if existing.data:
            return False, "Username already taken"
        
        # Check if email already exists
        existing_email = supabase.table("users")\
            .select("id")\
            .eq("email", email)\
            .execute()
        if existing_email.data:
            return False, "Email already registered"
        
        # Hash password
        hashed = bcrypt.hashpw(
            password.encode(), bcrypt.gensalt()
        ).decode()
        
        # Insert new user
        supabase.table("users").insert({
            "username": username,
            "password_hash": hashed,
            "role": "tenant",
            "name": name,
            "email": email,
            "unit": unit,
            "phone": phone,
            "rent": 1850,
            "balance": 1850
        }).execute()
        
        return True, "Account created successfully"
    except Exception as e:
        return False, f"Registration failed: {str(e)}"

def login_user(username, password):
    try:
        result = supabase.table("users")\
            .select("*")\
            .eq("username", username)\
            .execute()
        
        if not result.data:
            return None
        
        user = result.data[0]
        
        if bcrypt.checkpw(
            password.encode(), 
            user["password_hash"].encode()
        ):
            return user
        return None
    except Exception as e:
        return None

def get_all_tenants():
    try:
        result = supabase.table("users")\
            .select("*")\
            .eq("role", "tenant")\
            .execute()
        return result.data
    except Exception:
        return []

def get_all_payments():
    try:
        result = supabase.table("payments")\
            .select("*")\
            .order("created_at", desc=True)\
            .execute()
        return result.data
    except Exception:
        return []

def get_tenant_payments(user_id):
    try:
        result = supabase.table("payments")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .execute()
        return result.data
    except Exception:
        return []

def add_payment(user_id, tenant_name, unit, amount):
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        supabase.table("payments").insert({
            "user_id": user_id,
            "tenant_name": tenant_name,
            "unit": unit,
            "amount": amount,
            "date": today,
            "status": "Paid"
        }).execute()
        supabase.table("users")\
            .update({"balance": 0})\
            .eq("id", user_id)\
            .execute()
        return True
    except Exception as e:
        return False

def record_manual_payment(user_id, tenant_name, unit, amount, date):
    try:
        supabase.table("payments").insert({
            "user_id": user_id,
            "tenant_name": tenant_name,
            "unit": unit,
            "amount": amount,
            "date": date,
            "status": "Paid"
        }).execute()
        supabase.table("users")\
            .update({"balance": 0})\
            .eq("id", user_id)\
            .execute()
        return True
    except Exception:
        return False

def update_user_balance(user_id, balance):
    try:
        supabase.table("users")\
            .update({"balance": balance})\
            .eq("id", user_id)\
            .execute()
        return True
    except Exception:
        return False

def add_complaint(user_id, tenant_name, unit, 
                  subject, category, message):
    try:
        supabase.table("complaints").insert({
            "user_id": user_id,
            "tenant_name": tenant_name,
            "unit": unit,
            "subject": subject,
            "category": category,
            "message": message,
            "status": "Open"
        }).execute()
        return True
    except Exception:
        return False

def get_all_complaints():
    try:
        result = supabase.table("complaints")\
            .select("*")\
            .order("date", desc=True)\
            .execute()
        return result.data
    except Exception:
        return []

def resolve_complaint(complaint_id):
    try:
        supabase.table("complaints")\
            .update({"status": "Resolved"})\
            .eq("id", complaint_id)\
            .execute()
        return True
    except Exception:
        return False

def add_feedback(user_id, tenant_name, unit, 
                 topic, rating, details, follow_up):
    try:
        supabase.table("feedback").insert({
            "user_id": user_id,
            "tenant_name": tenant_name,
            "unit": unit,
            "topic": topic,
            "rating": rating,
            "details": details,
            "follow_up": follow_up
        }).execute()
        return True
    except Exception:
        return False

def get_all_feedback():
    try:
        result = supabase.table("feedback")\
            .select("*")\
            .order("date", desc=True)\
            .execute()
        return result.data
    except Exception:
        return []

def add_announcement(title, message, priority):
    try:
        supabase.table("announcements").insert({
            "title": title,
            "message": message,
            "priority": priority
        }).execute()
        return True
    except Exception:
        return False

def get_announcements():
    try:
        result = supabase.table("announcements")\
            .select("*")\
            .order("date", desc=True)\
            .execute()
        return result.data
    except Exception:
        return []
