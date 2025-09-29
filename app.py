import os
import re
import streamlit as st
import matplotlib.pyplot as plt
from tavily import TavilyClient
from dotenv import load_dotenv
from streamlit_mic_recorder import speech_to_text   # 🎤 Mic Recorder import

# -------------------------------
# Load API Keys
# -------------------------------
load_dotenv()
tavily_key = os.getenv("TAVILY_API_KEY")

if not tavily_key:
    st.error("❌ Tavily API key not found! Please check your .env file.")
    st.stop()

client_tavily = TavilyClient(api_key=tavily_key)

# -------------------------------
# Helper functions
# -------------------------------
def clean_name(text):
    return re.split(r"\||-|:", text)[0].strip()

def tavily_search(query, max_results=5):
    try:
        result = client_tavily.search(query)
        return result.get("results", [])[:max_results]
    except Exception as e:
        return [{"title": "Error", "content": str(e)}]

def extract_price(text):
    match = re.search(r"(\d{2,6})", text.replace(",", ""))
    if match:
        return int(match.group(1))
    return None

def market_research(product_name):
    competitors_query = f"Top smartwatches competing with {product_name} in 2025"
    competitors_data = tavily_search(competitors_query)
    competitors = [clean_name(item["title"]) for item in competitors_data[:3]]

    report = {"competitors": []}

    for comp in competitors:
        comp_data = {"name": comp, "features": [], "price": [], "reviews": [], "avg_price": None}

        # Features
        features = tavily_search(f"{comp} smartwatch features 2025")
        comp_data["features"] = [f["title"] + ": " + f["content"][:120] for f in features]

        # Price
        price_results = tavily_search(f"{comp} smartwatch price in Pakistan 2025 PKR")
        comp_data["price"] = [p["title"] + ": " + p["content"][:120] for p in price_results]

        extracted_prices = [extract_price(p["content"]) for p in price_results if "content" in p]
        extracted_prices = [p for p in extracted_prices if p]
        if extracted_prices:
            comp_data["avg_price"] = sum(extracted_prices) // len(extracted_prices)

        # Reviews
        reviews = tavily_search(f"{comp} smartwatch customer reviews 2025")
        comp_data["reviews"] = [r["title"] + ": " + r["content"][:120] for r in reviews]

        report["competitors"].append(comp_data)

    return report

# -------------------------------
# Streamlit UI
# -------------------------------
st.set_page_config(page_title="🏪 Market Research Agent", layout="wide")
st.title("🏪 Market Research Agent")
st.markdown("This app researches smartwatch competitors using Tavily API and generates a structured market analysis report with *charts & graphs*.")

# Sidebar
st.sidebar.header("⚙️ Controls")
uploaded_pdf = st.sidebar.file_uploader("📑 Upload your report (PDF)", type=["pdf"])
if uploaded_pdf:
    st.sidebar.success(f"✅ Uploaded: {uploaded_pdf.name}")

if st.sidebar.button("🧹 Clear All"):
    st.cache_data.clear()
    st.cache_resource.clear()
    st.rerun()

# -------------------------------
# Product input with Mic Option
# -------------------------------
col1, col2 = st.columns([3,1])

with col1:
    product_name = st.text_input("✍️ Enter Product Name:", "Nexus Smartwatch Pro 2")

with col2:
    st.write("🎙️ Speak instead:")
    voice_input = speech_to_text(
        language='en',
        use_container_width=True,
        just_once=True,
        key='STT'
    )
    if voice_input:
        product_name = voice_input
        st.success(f"✅ You said: {product_name}")

# -------------------------------
# Run Research
# -------------------------------
if st.button("Run Research"):
    with st.spinner("Researching live market data... 🔎"):
        report = market_research(product_name)

        st.success(f"✅ Market Research Completed for {product_name}")

        avg_prices = {}
        for comp in report["competitors"]:
            with st.expander(f"📌 {comp['name']}"):
                if comp["avg_price"]:
                    st.caption(f"💰 Estimated Avg Price: PKR {comp['avg_price']:,}")
                    avg_prices[comp["name"]] = comp["avg_price"]

                st.subheader("Key Features")
                for f in comp["features"]:
                    st.write("- " + f)

                st.subheader("Price in PKR")
                for p in comp["price"]:
                    st.write("- " + p)

                st.subheader("Customer Sentiment")
                for r in comp["reviews"]:
                    st.write("- " + r)

        if avg_prices:
            st.subheader("📊 Price Comparison Chart")
            fig, ax = plt.subplots()
            ax.bar(avg_prices.keys(), avg_prices.values(), color="skyblue")
            ax.set_ylabel("Price (PKR)")
            ax.set_title("Average Price Comparison of Competitors")
            st.pyplot(fig)

        st.subheader("🧭 Customer Sentiment Overview (Example Data)")
        sentiment_labels = ["Positive", "Neutral", "Negative"]
        sentiment_values = [60, 25, 15]

        fig2, ax2 = plt.subplots()
        wedges, texts, autotexts = ax2.pie(sentiment_values, labels=sentiment_labels, autopct='%1.1f%%',
                                           colors=["#4CAF50","#FFC107","#F44336"])
        for text in texts + autotexts:
            text.set_color("black")
        ax2.set_title("Customer Sentiment Distribution")
        st.pyplot(fig2)

        st.download_button(
            label="📥 Download Research Report (Text)",
            data=str(report),
            file_name="market_research_report.txt",
            mime="text/plain"
        )
