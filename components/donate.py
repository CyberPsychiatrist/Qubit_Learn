# components/donate.py
import os
import requests
import streamlit as st

def _backend_url() -> str:
    # Prefer Streamlit secrets in cloud, fallback to env/local
    try:
        if "BACKEND_URL" in st.secrets:
            return st.secrets["BACKEND_URL"]
    except Exception:
        pass
    return os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

def render_donate_tab(user_email: str):
    st.subheader("💝 Donate")

    backend = _backend_url()
    st.caption(f"Backend: {backend}")

    amount = st.number_input("Amount", min_value=1.0, step=1.0)
    method = st.radio("Payment method", ["M-Pesa (STK Push – KES)", "Card/PayPal Checkout"])
    email = st.text_input("Your email", value=user_email or "")
    phone = None

    if method.startswith("M-Pesa"):
        phone = st.text_input("M-Pesa phone (2547XXXXXXXX)")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Donate"):
            if not email:
                st.error("Please enter your email.")
                return
            if method.startswith("M-Pesa") and not phone:
                st.error("Please enter your M-Pesa phone number.")
                return

            try:
                if method.startswith("M-Pesa"):
                    payload = {"email": email, "phone": phone, "amount": amount, "currency": "KES"}
                    r = requests.post(f"{backend}/donate/mpesa-stk", json=payload, timeout=30)
                    if r.ok:
                        data = r.json()
                        st.success("📲 STK Push sent. Confirm on your phone.")
                        st.info(f"Donation ID: {data.get('donation_id')}")
                    else:
                        st.error(f"Error: {r.text}")
                else:
                    payload = {"email": email, "amount": amount, "currency": "USD"}
                    r = requests.post(f"{backend}/donate/checkout", json=payload, timeout=30)
                    if r.ok:
                        data = r.json()
                        st.success("✅ Checkout created.")
                        st.markdown(f"[Open checkout link]({data.get('checkout_url')})", unsafe_allow_html=True)
                    else:
                        st.error(f"Error: {r.text}")
            except Exception as e:
                st.error(f"Request failed: {e}")

    with col2:
        if st.button("My Donations"):
            if not email:
                st.error("Enter your email to fetch donations.")
                return
            try:
                r = requests.get(f"{backend}/donations", params={"email": email}, timeout=30)
                if r.ok:
                    items = r.json().get("donations", [])
                    if not items:
                        st.info("No donations yet.")
                    else:
                        for d in items:
                            st.write(
                                f"• {d['created_at']} — {d['amount']} {d['currency']} via {d['method']} → **{d['status']}** (id: {d['id']})"
                            )
                else:
                    st.error(f"Error: {r.text}")
            except Exception as e:
                st.error(f"Request failed: {e}")
