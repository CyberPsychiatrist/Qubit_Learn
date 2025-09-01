# components/donate_section.py
import streamlit as st
import requests
import os
from dotenv import load_dotenv

# ✅ Load env vars from .env (for local dev)
load_dotenv()

# ✅ Backend URL (from env or default to localhost)
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")


def render_donate_section(user_email: str):
    st.subheader("💝 Support Our Mission")
    st.info("Your donation helps us advance **UNSDG4: Quality Education** 🌍📚")

    # Tabs for donation methods
    tab1, tab2 = st.tabs(["📲 M-Pesa STK Push", "💳 Card / PayPal Checkout"])

    # ---------- M-Pesa STK ----------
    with tab1:
        st.write("Enter your phone number (format: 2547XXXXXXXX) to donate via M-Pesa STK Push.")

        phone = st.text_input("Phone Number", "")
        amount = st.number_input("Amount (KES)", min_value=1, step=1, value=10)
        note = st.text_area("Optional note")

        if st.button("Donate via STK Push", key="stk_donate"):
            if not phone.strip():
                st.error("🚨 Please enter your phone number in format 2547XXXXXXXX.")
            else:
                payload = {
                    "email": user_email,
                    "phone": phone,
                    "amount": amount,
                    "note": note,
                }
                try:
                    resp = requests.post(f"{BACKEND_URL}/donate/mpesa-stk", json=payload, timeout=30)
                    data = resp.json()
                    if resp.ok and data.get("ok"):
                        st.success(data.get("message", "📲 STK Push sent! Confirm on your phone."))
                    else:
                        st.error(f"❌ Error: {data.get('detail', data)}")
                except Exception as e:
                    st.error(f"⚠️ Request failed: {e}")

    # ---------- Checkout ----------
    with tab2:
        st.write("Donate via hosted checkout (Card, PayPal, or browser-based M-Pesa).")

        amount_usd = st.number_input("Amount", min_value=1, step=1, value=5, key="checkout_amount")
        currency = st.selectbox("Currency", ["USD", "KES"])

        if st.button("Donate via Checkout", key="checkout_donate"):
            payload = {
                "email": user_email,
                "amount": amount_usd,
                "currency": currency,
            }
            try:
                resp = requests.post(f"{BACKEND_URL}/donate/checkout", json=payload, timeout=30)
                data = resp.json()
                if resp.ok and data.get("ok"):
                    checkout_url = data.get("checkout_url")
                    st.success("✅ Redirecting to checkout page...")
                    st.markdown(f"[👉 Complete your donation here]({checkout_url})", unsafe_allow_html=True)
                else:
                    st.error(f"❌ Error: {data.get('detail', data)}")
            except Exception as e:
                st.error(f"⚠️ Request failed: {e}")

    # ---------- Donation History ----------
    st.markdown("---")
    st.subheader("📊 Your Donation History")

    try:
        resp = requests.get(f"{BACKEND_URL}/donations", params={"email": user_email}, timeout=20)
        data = resp.json()
        if resp.ok and data.get("ok"):
            donations = data.get("donations", [])
            if donations:
                st.dataframe(
                    [
                        {
                            "Amount": f"{d['amount']} {d['currency']}",
                            "Method": d['method'],
                            "Status": d['status'],
                            "Reference": d.get("api_ref", ""),
                        }
                        for d in donations
                    ],
                    use_container_width=True,
                )
            else:
                st.info("ℹ️ No donations yet. Be the first to support!")
        else:
            st.error(f"❌ Could not fetch donation history: {data.get('detail', data)}")
    except Exception as e:
        st.error(f"⚠️ Request failed: {e}")
