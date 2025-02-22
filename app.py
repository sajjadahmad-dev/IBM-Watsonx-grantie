# app.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import requests
import json

# IBM Watsonx API Configuration
API_KEY = "YOUR_KEY"  # Replace with your IBM Cloud API key
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
                # Example response: ".\n\n0.95" -> Extract "0.95"
                import re
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
st.set_page_config(page_title="Financial Crime Prevention Network", layout="wide")
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard", "Transaction Analysis", "Risk Assessment", "Reports"])

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
                        risk_score = float(response.strip()) * 100
                        st.subheader("Risk Assessment Results")
                        st.metric("Overall Risk Score", f"{risk_score:.2f}%")
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

# Page Navigation
if page == "Dashboard":
    show_dashboard()
elif page == "Transaction Analysis":
    show_transaction_analysis()
elif page == "Risk Assessment":
    show_risk_assessment()
elif page == "Reports":
    show_reports()
