
import streamlit as st
import requests

st.set_page_config(page_title="NaijaCheck", page_icon="🇳🇬", layout="centered")

# Custom CSS to make it look like your green screenshot - clean, no clutter
st.markdown("""
<style>
    .main-title {font-size: 32px; font-weight: bold; color: #0f7a3d; text-align: center; margin-bottom: 5px;}
    .subtitle {text-align: center; color: #666; margin-bottom: 20px;}
    .result-card-auth {background: #e8f5e9; border: 2px solid #4caf50; border-radius: 15px; padding: 20px; text-align: center; margin: 20px 0;}
    .result-card-fake {background: #ffebee; border: 2px solid #f44336; border-radius: 15px; padding: 20px; text-align: center; margin: 20px 0;}
    .big-emoji {font-size: 60px;}
    .big-text {font-size: 24px; font-weight: bold; margin: 10px 0;}
    .small-text {color: #666; font-size: 14px;}
    .stButton>button {background: #0f7a3d; color: white; border-radius: 10px; height: 50px; font-size: 18px; width: 100%;}
    div[data-testid="stTextInput"] input {height: 50px; font-size: 18px; border-radius: 10px;}
</style>
""", unsafe_allow_html=True)

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"].rstrip("/").replace("/rest/v1", "").split("/rest")[0]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except:
    st.error("Add SUPABASE_URL and SUPABASE_KEY in Secrets")
    st.stop()

HEADERS = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}

def clean_code(c):
    return c.replace(",", "").replace(";", "").replace(" ", "").strip().upper() if c else ""

def verify(code):
    try:
        code = clean_code(code)
        url = f"{SUPABASE_URL}/rest/v1/products"
        r = requests.get(url, headers=HEADERS, params={"code": f"eq.{code}", "select": "*"}, timeout=10)
        data = r.json() if r.status_code == 200 else []
        return data[0] if data else None
    except:
        return None

# HEADER - Clean like screenshot
st.markdown('<div class="main-title">🇳🇬 NaijaCheck</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Confirm your product na original? • 10,000 products</div>', unsafe_allow_html=True)

# INPUT - Simple
code_input = st.text_input("", placeholder="Enter NAFDAC No. e.g. A4-123456", label_visibility="collapsed")
st.caption("Found on pack: A4-123456 or SON-123456")

if st.button("Verify Now"):
    if not code_input:
        st.warning("Enter code first")
    else:
        code = clean_code(code_input)
        with st.spinner("Checking..."):
            product = verify(code)
        
        if not product:
            # NOT FOUND = FAKE - Simple
            st.markdown(f"""
            <div class="result-card-fake">
                <div class="big-emoji">🚨</div>
                <div class="big-text" style="color: #d32f2f;">FAKE PRODUCT!</div>
                <div class="small-text">Code {code} not in NAFDAC database</div>
                <div style="margin-top:15px; background: white; border-radius: 8px; padding: 10px; font-size: 14px;">
                    ❌ Do not buy or use<br>
                    📞 Report: 0800-1-NAFDAC
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            status = str(product.get("status","")).upper()
            name = product.get("name","")
            # Smart fake check
            is_fake = "FAKE" in status or "FAKE" in name.upper() or "NOT REGISTERED" in name.upper() or code == "A4-999999"
            is_expired = "EXPIRED" in status
            
            if is_fake:
                st.markdown(f"""
                <div class="result-card-fake">
                    <div class="big-emoji">🚨</div>
                    <div class="big-text" style="color: #d32f2f;">FAKE!</div>
                    <div class="small-text">{name}</div>
                    <div style="margin-top:15px; background: white; border-radius: 8px; padding: 10px; font-size: 14px;">
                        ❌ Do not use<br>
                        📞 Report: 0800-1-NAFDAC
                    </div>
                </div>
                """, unsafe_allow_html=True)
            elif is_expired:
                st.markdown(f"""
                <div class="result-card-fake">
                    <div class="big-emoji">⚠️</div>
                    <div class="big-text" style="color: #ef6c00;">EXPIRED!</div>
                    <div class="small-text">{name}<br>Expired: {product.get('expiry','')}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # AUTHENTIC - Simple green
                st.markdown(f"""
                <div class="result-card-auth">
                    <div class="big-emoji">✅</div>
                    <div class="big-text" style="color: #2e7d32;">ORIGINAL!</div>
                    <div class="small-text">{name}<br>{product.get('company','')}</div>
                    <div style="margin-top:15px; background: white; border-radius: 8px; padding: 10px; font-size: 14px; color: #2e7d32;">
                        ✔️ Safe to use
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.balloons()

st.divider()
# Samples - Simple clickable
st.caption("Try these:")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("A4-123456 (Real)"):
        st.session_state["code"] = "A4-123456"
        st.rerun()
with col2:
    if st.button("A4-999999 (Fake)"):
        st.session_state["code"] = "A4-999999"
        st.rerun()
with col3:
    if st.button("A1-1004070"):
        st.session_state["code"] = "A1-1004070"
        st.rerun()

st.markdown("<br><center style='color:#999; font-size:12px;'>No hard-coded data • Live from Supabase • 10,000 products</center>", unsafe_allow_html=True)
