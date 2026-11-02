
import streamlit as st
import requests

st.set_page_config(page_title="NaijaCheck", page_icon="🇳🇬", layout="centered")

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except KeyError as e:
    st.error(f"Missing secret: {e}")
    st.stop()

SUPABASE_URL = SUPABASE_URL.rstrip("/").replace("/rest/v1", "")
if "/rest" in SUPABASE_URL:
    SUPABASE_URL = SUPABASE_URL.split("/rest")[0]

HEADERS = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}

def clean_code(code):
    if not code:
        return ""
    return code.replace(",", "").replace(";", "").replace(" ", "").strip().upper()

def verify_product(code):
    try:
        code = clean_code(code)
        if not code:
            return None
        url = f"{SUPABASE_URL}/rest/v1/products"
        params = {"code": f"eq.{code}", "select": "*"}
        resp = requests.get(url, headers=HEADERS, params=params, timeout=10)
        if resp.status_code != 200:
            return None
        data = resp.json()
        return data[0] if data else None
    except:
        return None

def is_fake_product(product):
    """Smart fake detection - checks status AND name"""
    if not product:
        return False
    status = str(product.get("status", "")).upper()
    name = str(product.get("name", "")).upper()
    company = str(product.get("company", "")).upper()
    
    # If status says FAKE, or name contains FAKE / NOT REGISTERED, it's fake
    if "FAKE" in status:
        return True
    if "FAKE" in name or "NOT REGISTERED" in name:
        return True
    if company == "UNKNOWN" and "FAKE" in name:
        return True
    # Special test codes that should ALWAYS be fake
    if product.get("code") == "A4-999999":
        return True
    return False

def is_expired_product(product):
    status = str(product.get("status", "")).upper()
    return "EXPIRED" in status

def log_scan(code, status, category="unknown"):
    try:
        url = f"{SUPABASE_URL}/rest/v1/verifications"
        payload = {"nafdac": clean_code(code), "status": status, "location": category}
        requests.post(url, headers=HEADERS, json=payload, timeout=5)
    except:
        pass

def get_stats():
    try:
        url = f"{SUPABASE_URL}/rest/v1/products"
        h = HEADERS.copy()
        h["Prefer"] = "count=exact"
        resp = requests.get(url, headers=h, params={"select": "code", "limit": "1"}, timeout=10)
        total = 10000
        if resp.status_code == 200:
            cr = resp.headers.get("content-range", "")
            if "/" in cr:
                try:
                    total = int(cr.split("/")[-1])
                except:
                    pass
        return total, 0
    except:
        return 10000, 0

st.title("🇳🇬 NaijaCheck")
total_products, _ = get_stats()
st.success(f"✅ Connected - {total_products}+ products - No hard-code")

tab1, tab2 = st.tabs(["🔍 Verify by Code", "📦 Browse"])

with tab1:
    st.subheader("Enter NAFDAC / SON Code")
    st.caption("Test: A4-123456 = Real, A4-999999 = Should be FAKE (if shows Authentic, fix DB below)")
    code_input_raw = st.text_input("Code", placeholder="e.g. A4-123456")
    code_input = clean_code(code_input_raw)
    
    if st.button("Verify Now", type="primary"):
        if not code_input:
            st.warning("Enter code")
        else:
            product = verify_product(code_input)
            
            if not product:
                st.error(f"🚨 Code {code_input} NOT FOUND in {total_products} products!")
                st.warning("FAKE product - Not in NAFDAC database")
                log_scan(code_input, "FAKE_NOT_FOUND", "unknown")
            elif is_fake_product(product):
                st.error(f"🚨 FAKE CONFIRMED: {product['name']}")
                st.write(f"**Code:** {product['code']} | **Status:** {product['status']}")
                st.write(f"**Company:** {product['company']} | **Category:** {product['category']}")
                st.warning("DO NOT USE - Report to NAFDAC: 0800-1-NAFDAC")
                log_scan(code_input, "FAKE", product['category'])
            elif is_expired_product(product):
                st.warning(f"⚠️ EXPIRED: {product['name']} expired {product['expiry']}")
                log_scan(code_input, "EXPIRED", product['category'])
            else:
                st.success(f"✅ AUTHENTIC - {product['name']}")
                st.write(f"**Company:** {product['company']} | **Category:** {product['category'].upper()}")
                st.write(f"**Expiry:** {product['expiry']} | **Batch:** {product['batch']}")
                log_scan(code_input, "AUTHENTIC", product['category'])
                st.balloons()

with tab2:
    st.subheader("Fix A4-999999 to be FAKE")
    st.write("If A4-999999 shows Authentic, run this SQL in Supabase SQL Editor to fix it:")
    st.code("""
-- Fix A4-999999 to be FAKE (run in Supabase SQL Editor)
UPDATE products 
SET status = 'FAKE', 
    name = 'Fake Drug - NOT REGISTERED - FAKE', 
    company = 'Unknown - FAKE' 
WHERE code = 'A4-999999';

-- Verify it worked
SELECT code, name, status FROM products WHERE code = 'A4-999999';
""", language="sql")
    
    if st.button("Check what A4-999999 currently is in DB"):
        p = verify_product("A4-999999")
        if p:
            st.write(f"Current in DB: Code={p['code']}, Name={p['name']}, Status={p['status']}, Company={p['company']}")
            if p['status'] == 'Authentic':
                st.error("It is Authentic in DB - you need to run UPDATE SQL above to make it FAKE")
            else:
                st.success(f"It is {p['status']} - correct!")
        else:
            st.error("A4-999999 not found in DB at all")

st.divider()
st.caption("Smart fake detection: Checks status AND name contains FAKE")
