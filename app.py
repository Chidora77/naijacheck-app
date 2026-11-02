
import streamlit as st
from supabase import create_client

st.set_page_config(page_title="NaijaCheck - Verify Anything", page_icon="🇳🇬", layout="centered")

# --- SUPABASE CONNECTION - NO HARD CODE ---
# Add these in Streamlit Cloud Secrets
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

# --- FUNCTIONS - ALL DATA COMES FROM SUPABASE ---
def verify_product(code):
    """No hard-coded dict - directly queries Supabase products table"""
    try:
        # Trim and uppercase
        code = code.strip().upper()
        res = supabase.table("products").select("*").eq("code", code).execute()
        if res.data:
            return res.data[0]
        return None
    except Exception as e:
        st.error(f"Database error: {e}")
        return None

def log_scan(code, status, category="unknown"):
    """Logs every scan - this data is valuable for NAFDAC reports"""
    try:
        supabase.table("verifications").insert({
            "nafdac": code,
            "status": status,
            "location": category
        }).execute()
    except:
        pass

def get_doctors():
    try:
        res = supabase.table("doctors").select("*").eq("available", True).execute()
        return res.data
    except:
        return []

def search_products(query, category_filter="All"):
    """Search through your 10,000 products"""
    try:
        q = supabase.table("products").select("*").limit(50)
        if category_filter != "All":
            q = q.eq("category", category_filter.lower())
        if query:
            q = q.ilike("name", f"%{query}%")
        res = q.execute()
        return res.data
    except:
        return []

# --- UI ---
st.title("🇳🇬 NaijaCheck")
st.caption("Verify 10,000+ products - Drugs, Food, Drinks, Cosmetics, Building")

tab1, tab2, tab3 = st.tabs(["🔍 Verify by Code", "📦 Browse 10k Products", "👩‍⚕️ Doctors"])

with tab1:
    st.subheader("Enter NAFDAC / SON Code")
    st.write("Try: A4-123456 (real), A4-999999 (fake) - All 10,000 codes from your CSV work")
    code_input = st.text_input("Code", placeholder="e.g. A4-123456, A1-1001, SON-2001", key="verify_input").strip().upper()
    
    if st.button("Verify Now", type="primary", key="verify_btn"):
        if not code_input:
            st.warning("Please enter a code")
        else:
            with st.spinner("Checking Supabase database (10,000 products)..."):
                product = verify_product(code_input)
            
            if not product:
                st.error(f"🚨 Code {code_input} NOT FOUND in database of 10,000 products!")
                st.warning("High chance of FAKE product. Report to NAFDAC: 0800-1-NAFDAC")
                log_scan(code_input, "FAKE_NOT_FOUND", "unknown")
            elif product["status"] == "Authentic":
                st.success(f"✅ AUTHENTIC - {product['name']}")
                st.write(f"**Company:** {product['company']} | **Category:** {product['category'].upper()}")
                st.write(f"**Expiry:** {product['expiry']} | **Batch:** {product['batch']}")
                log_scan(code_input, "AUTHENTIC", product['category'])
                st.balloons()
            elif product["status"] == "FAKE":
                st.error(f"🚨 FAKE CONFIRMED: {product['name']} is NOT registered!")
                st.write(f"Category: {product['category']} - Do NOT buy/use")
                log_scan(code_input, "FAKE", product['category'])
            else:
                st.warning(f"⚠️ EXPIRED: {product['name']} expired on {product['expiry']}")
                log_scan(code_input, "EXPIRED", product['category'])

with tab2:
    st.subheader("Browse Your 10,000 Product Database")
    col1, col2 = st.columns([2,1])
    with col1:
        search_q = st.text_input("Search product name", placeholder="e.g. Paracetamol, Coke, Nivea")
    with col2:
        cat_filter = st.selectbox("Category", ["All", "Drug", "Food", "Drink", "Cosmetic", "Building"])
    
    if st.button("Search Database"):
        results = search_products(search_q, cat_filter)
        st.write(f"Found {len(results)} products (showing 50 max)")
        for p in results:
            icon = {"drug": "💊", "food": "🍲", "drink": "🥤", "cosmetic": "🧴", "building": "🧱"}.get(p['category'], "📦")
            status_emoji = "✅" if p['status'] == "Authentic" else "🚨" if p['status'] == "FAKE" else "⚠️"
            with st.container(border=True):
                st.write(f"{icon} {status_emoji} **{p['name']}** - {p['company']}")
                st.caption(f"Code: {p['code']} | {p['category']} | {p['status']} | Exp: {p['expiry']}")

with tab3:
    st.subheader("Doctors & Pharmacists (from Supabase)")
    doctors = get_doctors()
    if not doctors:
        st.info("No doctors found. Add them in Supabase doctors table.")
    for doc in doctors:
        with st.container(border=True):
            st.write(f"**{doc['name']}** - {doc['role']} ⭐ {doc.get('rating', 4.8)}")
            st.write(f"Fee: ₦{doc['price']:,} | Your profit: ₦{int(doc['price']*0.3):,}")
            wa_link = f"https://wa.me/{doc['whatsapp']}?text=Hello {doc['name']}, I need consultation from NaijaCheck. Code: {code_input if 'code_input' in locals() else ''}"
            st.link_button(f"Pay ₦{doc['price']:,} → WhatsApp", wa_link, type="primary")

st.divider()
st.caption("100% Supabase-powered - Zero hard-coded products. Add products in Supabase, app updates instantly. | 10,000 products ready to import.")
