# app.py
import os
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import requests
import json

# IBM Watsonx API Configuration
API_KEY = os.getenv("YOUR_KEY")  # Replace with your IBM Cloud API key
IAM_TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"
WATSONX_API_URL = "https://us-south.ml.cloud.ibm.com/ml/v1/text/generation?version=2023-05-29"

# Function to get IAM access token
def get_iam_token(api_key):
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
        "apikey": api_key
    }
    response = requests.post(IAM_TOKEN_URL, headers=headers, data=data)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        st.error(f"Failed to get IAM token: {response.text}")
        return None

# Function to get IAM access token
def get_iam_token(api_key):
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
        "apikey": api_key
    }
    response = requests.post(IAM_TOKEN_URL, headers=headers, data=data)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        st.error(f"Failed to get IAM token: {response.text}")
        return None

# Function to query IBM Watsonx API
def query_granite(prompt):
    iam_token = get_iam_token(API_KEY)
    if not iam_token:
        return None
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {iam_token}"
    }
    
    data = {
        "input": f"<|start_of_role|>system<|end_of_role|>You are Granite, an AI language model developed by IBM in 2024. You are a cautious assistant. You carefully follow instructions. You are helpful and harmless and you follow ethical guidelines and promote positive behavior.<|end_of_text|>\n<|start_of_role|>assistant<|end_of_role|>{prompt}",
        "parameters": {
            "decoding_method": "greedy",
            "max_new_tokens": 50,
            "min_new_tokens": 0,
            "stop_sequences": [],
            "repetition_penalty": 1
        },
        "model_id": "ibm/granite-3-8b-instruct",
        "project_id": "ae88d700-6356-46b0-8aae-a32e6f1932df",  # Replace with your project ID
        "moderations": {
            "hap": {
                "input": {"enabled": True, "threshold": 0.5, "mask": {"remove_entity_value": True}},
                "output": {"enabled": True, "threshold": 0.5, "mask": {"remove_entity_value": True}}
            },
            "pii": {
                "input": {"enabled": True, "threshold": 0.5, "mask": {"remove_entity_value": True}},
                "output": {"enabled": True, "threshold": 0.5, "mask": {"remove_entity_value": True}}
            }
        }
    }
    
    try:
        response = requests.post(WATSONX_API_URL, headers=headers, json=data)
        if response.status_code == 200:
            return response.json().get("results", [{}])[0].get("generated_text", "")
        else:
            st.error(f"API Error: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error querying API: {str(e)}")
        return None

# Transaction analysis function
def analyze_transaction(transaction_text):
    prompt = f"""Analyze the following financial transaction and provide a risk score between 0 and 1, 
    where 0 is lowest risk and 1 is highest risk. Only return the numerical score.
    Transaction: {transaction_text}"""
    
    try:
        with st.spinner("Analyzing transaction..."):  # Add a loading spinner
            response = query_granite(prompt)
            if response:
                # Extract the numerical value from the response
                match = re.search(r"\d+\.\d+", response)  # Find a floating-point number in the response
                if match:
                    risk_score = float(match.group())  # Convert the matched number to float
                    risk_score = max(0, min(1, risk_score))  # Ensure the score is between 0 and 1
                    return risk_score
                else:
                    st.error("Failed to extract a valid risk score from the response.")
                    return 0.5
    except Exception as e:
        st.error(f"Error analyzing transaction: {str(e)}")
        return 0.5

# Sample transaction data
sample_transactions = [
    {"id": 1, "date": "2025-02-21", "amount": 5000, "sender": "John Doe", "receiver": "Jane Smith", "description": "Business payment for services"},
    {"id": 2, "date": "2025-02-20", "amount": 10000, "sender": "Alice Johnson", "receiver": "Bob Brown", "description": "International wire transfer"},
    {"id": 3, "date": "2025-02-19", "amount": 1500, "sender": "Charlie Davis", "receiver": "Eve White", "description": "Cash withdrawal"}
]

# Streamlit App Configuration
st.set_page_config(page_title="FraudShield", layout="wide")

st.markdown(
    """
    <style>
    /* Background and text colors */
    .stApp {
        background-color: #eef2f7; /* Light grey-blue */
        color: #343a40; /* Dark grey */
    }

    /* Buttons */
    .stButton>button {
        background-color: #007BFF; /* Primary blue */
        color: white;
        border-radius: 5px;
        padding: 10px 15px;
        font-size: 16px;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #0056b3; /* Darker blue on hover */
    }

    /* Input fields */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: #ffffff; /* White */
        border-radius: 5px;
        border: 1px solid #007BFF; /* Blue border */
        padding: 8px;
    }

    /* Chat messages */
    .stChatMessage {
        background-color: white;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 10px;
        box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.1);
    }

    /* Sidebar */
    .stSidebar {
        background-color: #ffffff; /* Pure white */
        padding: 20px;
        border-right: 1px solid #ddd;
    }

    /* Titles and headings */
    h1, h2, h3 {
        color: #0056b3; /* Dark blue */
    }

    /* Metrics box */
    .stMetric {
        background-color: rgba(255, 255, 255, 0.9);
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", [
    "Home", "Dashboard", "Transaction Analysis", "Risk Assessment", 
    "Reports", "Fraud Map", "Fraud Alerts", "Chatbot", 
    "Feedback", "Help"
])

# Landing Page
def show_landing_page():
    st.title("Welcome to FraudShield 🛡️")
    st.write("""
    **FraudShield** is an AI-powered platform designed to detect and prevent financial crimes. 
    Our solution leverages **IBM Granite AI models** to analyze transactions, assess risks, and generate actionable insights.
    """)
    
    st.subheader("Key Features")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Real-Time Analysis**")
        st.write("Analyze transactions in real-time to detect fraudulent activities.")
    with col2:
        st.markdown("**Risk Assessment**")
        st.write("Evaluate customer profiles and assign risk scores for compliance.")
    with col3:
        st.markdown("**Detailed Reports**")
        st.write("Generate comprehensive reports for audits and decision-making.")
    
    st.subheader("Meet the Team: The Code Titans")
    st.write("""
    - **Sajjad Ahmad**: AI/ML Engineer
    - **[Team Member 2]**: Data Scientist
    - **[Team Member 3]**: UI/UX Designer
    - **[Team Member 4]**: Backend Developer
    """)

# Dashboard
def show_dashboard():
    st.title("Financial Crime Prevention Dashboard")
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Total Transactions", len(sample_transactions))
    with col2: st.metric("High Risk Alerts", "3")
    with col3: st.metric("Medium Risk Alerts", "5")
    with col4: st.metric("Low Risk Alerts", "8")
    
    st.subheader("Transaction Risk Trends")
    dates = pd.date_range(start="2025-02-01", end="2025-02-21")
    risk_scores = np.random.rand(len(dates)) * 100
    df = pd.DataFrame({"Date": dates, "Risk Score": risk_scores})
    fig = px.line(df, x="Date", y="Risk Score")
    st.plotly_chart(fig)

# Transaction Analysis
def show_transaction_analysis():
    st.title("Transaction Analysis")
    sender = st.text_input("Sender Name")
    receiver = st.text_input("Receiver Name")
    amount = st.number_input("Amount", min_value=0.0)
    description = st.text_area("Transaction Description")
    
    if st.button("Analyze Transaction"):
        if sender and receiver and amount and description:
            transaction_text = f"Sender: {sender}, Receiver: {receiver}, Amount: {amount}, Description: {description}"
            risk_score = analyze_transaction(transaction_text)
            
            st.subheader("Analysis Results")
            risk_percentage = risk_score * 100
            fig = go.Figure(go.Indicator(
                mode = "gauge+number", value = risk_percentage,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Risk Score"},
                gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': "darkblue"},
                         'steps': [{'range': [0, 30], 'color': "green"},
                                   {'range': [30, 70], 'color': "yellow"},
                                   {'range': [70, 100], 'color': "red"}]}
            ))
            st.plotly_chart(fig)
            if risk_percentage < 30:
                st.success("Low Risk Transaction")
            elif risk_percentage < 70:
                st.warning("Medium Risk Transaction")
            else:
                st.error("High Risk Transaction - Further Investigation Required")

# Risk Assessment
def show_risk_assessment():
    st.title("Risk Assessment")
    with st.form("risk_assessment_form"):
        business_type = st.selectbox("Business Type", ["Individual", "Small Business", "Corporation"])
        transaction_volume = st.slider("Monthly Transaction Volume", 0, 1000000, 10000)
        country_risk = st.selectbox("Country Risk Level", ["Low", "Medium", "High"])
        if st.form_submit_button("Calculate Risk Score"):
            assessment_prompt = f"""Calculate a risk score between 0 and 1 for the following customer profile:
            Business Type: {business_type}
            Monthly Transaction Volume: ${transaction_volume}
            Country Risk Level: {country_risk}
            Only return the numerical score."""
            try:
                with st.spinner("Calculating risk score..."):  # Add a loading spinner
                    response = query_granite(assessment_prompt)
                    if response:
                        match = re.search(r"\d+\.\d+", response)  # Find a floating-point number in the response
                        if match:
                            risk_score = float(match.group()) * 100
                            st.subheader("Risk Assessment Results")
                            st.metric("Overall Risk Score", f"{risk_score:.2f}%")
                        else:
                            st.error("Failed to extract a valid risk score from the response.")
            except Exception as e:
                st.error(f"Error calculating risk score: {str(e)}")

# Reports
def show_reports():
    st.title("Reports")
    report_type = st.selectbox("Select Report Type", ["Transaction Summary", "Risk Analysis", "Suspicious Activity"])
    date_range = st.date_input("Select Date Range", [datetime.now(), datetime.now()])
    if st.button("Generate Report"):
        st.subheader(f"{report_type} Report")
        st.write(f"Date Range: {date_range[0]} to {date_range[1]}")
        if report_type == "Transaction Summary":
            summary_data = pd.DataFrame({"Date": pd.date_range(date_range[0], date_range[1]),
                                         "Total Transactions": np.random.randint(100, 1000, len(pd.date_range(date_range[0], date_range[1]))),
                                         "Average Amount": np.random.randint(1000, 10000, len(pd.date_range(date_range[0], date_range[1])))})
            st.dataframe(summary_data)
            fig = px.bar(summary_data, x="Date", y="Total Transactions")
            st.plotly_chart(fig)

# Fraud Map
def show_fraud_map():
    st.title("Fraud Hotspots Map")
    st.write("Visualize regions with high fraud activity.")
    
    # Sample data for fraud hotspots
    fraud_data = pd.DataFrame({
        "latitude": [37.7749, 34.0522, 40.7128, 51.5074, 48.8566],
        "longitude": [-122.4194, -118.2437, -74.0060, -0.1278, 2.3522],
        "city": ["San Francisco", "Los Angeles", "New York", "London", "Paris"],
        "fraud_cases": [120, 95, 150, 80, 60]
    })
    
    # Display the map
    st.map(fraud_data)

# Fraud Alerts
def show_fraud_alerts():
    st.title("Fraud Alerts")
    st.write("View real-time alerts for suspicious transactions.")
    
    # Sample fraud alerts
    fraud_alerts = [
        {"id": 1, "date": "2025-02-21", "amount": 5000, "sender": "John Doe", "receiver": "Jane Smith", "status": "High Risk"},
        {"id": 2, "date": "2025-02-20", "amount": 10000, "sender": "Alice Johnson", "receiver": "Bob Brown", "status": "Medium Risk"},
        {"id": 3, "date": "2025-02-19", "amount": 1500, "sender": "Charlie Davis", "receiver": "Eve White", "status": "Low Risk"}
    ]
    
    # Display alerts in a table
    st.table(fraud_alerts)

# Chatbot Page
def show_chatbot():
    st.title("Chat with FraudShield AI 🤖")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display previous chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input field
    user_input = st.chat_input("Ask me anything...")
    
    if user_input:
        # Display user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Get AI response
        with st.chat_message("assistant"):
            response = query_granite(user_input)
            if response:
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            else:
                st.markdown("Sorry, I couldn't process your request.")

# Feedback
def show_feedback():
    st.title("Feedback")
    st.write("We value your feedback! Let us know how we can improve FraudShield.")
    
    feedback = st.text_area("Enter your feedback here:")
    if st.button("Submit Feedback"):
        st.success("Thank you for your feedback! We'll review it soon.")

# Help & Documentation
def show_help():
    st.title("Help & Documentation")
    st.write("Find answers to common questions and learn how to use FraudShield.")
    
    st.subheader("FAQs")
    st.write("""
    **Q: How does FraudShield detect fraud?**  
    A: FraudShield uses advanced AI models to analyze transaction patterns and identify suspicious activities.
    
    **Q: Can I customize the risk assessment criteria?**  
    A: Yes, you can adjust the parameters in the Risk Assessment section.
    
    **Q: How does FraudShield detect fraud?**
    A: It uses machine learning algorithms to monitor transaction behaviors, flag anomalies, and assign risk scores.

    **Q: Is FraudShield suitable for small businesses?**
    A: Yes, FraudShield is scalable and can be used by both small businesses and large enterprises.

    **Q: What industries can use FraudShield?**
    A: It can be used in banking, e-commerce, insurance, fintech, and any business dealing with financial transactions.

    **Q: Does FraudShield work in real time?**
    A: Yes, it provides real-time fraud detection to prevent suspicious transactions before they are processed."""
          )

# Page Navigation
if page == "Home":
    show_landing_page()
elif page == "Dashboard":
    show_dashboard()
elif page == "Transaction Analysis":
    show_transaction_analysis()
elif page == "Risk Assessment":
    show_risk_assessment()
elif page == "Reports":
    show_reports()
elif page == "Fraud Map":
    show_fraud_map()
elif page == "Fraud Alerts":
    show_fraud_alerts()
elif page == "Chatbot":
    show_chatbot()
elif page == "Feedback":
    show_feedback()
elif page == "Help":
    show_help()
