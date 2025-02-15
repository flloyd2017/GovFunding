import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from google.oauth2.service_account import Credentials

# Google Sheets API setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Load credentials correctly
creds_dict = st.secrets["google_sheets"]
creds = Credentials.from_service_account_info(dict(creds_dict))

# Authenticate and connect to Google Sheets
client = gspread.authorize(creds)


# Open your Google Sheet
SHEET_ID = "15NR5PCoUTNVjTueWwwIhB4EwyCqj3BOJKj9f2FhkeGA"  # Replace with your actual Google Sheet ID
sheet = client.open_by_key(SHEET_ID).sheet1

# Set wide page layout
st.set_page_config(layout="wide")

# Display banner image at the top
#st.image("/Users/forresthansen/Desktop/GitHubProjects/GovFunding/Screenshot 2025-02-14 at 14.50.25.png", use_column_width=True)

USPop = 334.9

# Combined agency data sorted from high to low
agencies = {
    k: v for k, v in sorted({
        "Medicare": 848200,
        "Medicaid": 592000,
        "Social Security": 400000,
        "Dept of Agriculture": 213000,
        "Dept of Commerce": 11400,
        "Dept of Education": 82400,
        "Dept of Energy": 31700,
        "Dept of Justice": 37800,
        "Dept of Labor": 13900,
        "Dept of State": 53000,
        "Dept of Air Force": 217000,
        "Dept of Army": 185000,
        "Dept of Navy": 257600,
        "Dept of Interior": 75510,
        "Dept of Transportation": 109300,
        "Dept of Veteran Affairs": 369300,
        "Dept of Health and Human Services": 130700,
        "Dept of Homeland Security": 165730,
        "Dept of Housing and Urban Development": 73000,
        "Dept of Treasury": 14000,
        "Consumer Financial Protection Bureau": 310.9,
        "Court Services and Offender Supervision (DC)": 125.9,
        "Environmental Protection Agency": 2200,
        "Equal Employment Opportunity Commission": 248.7,
        "Federal Communications Commission": 257.3,
        "Federal Deposit Insurance Corporation": 1000,
        "Federal Trade Commission": 210.6,
        "General Services Administration": 1700,
        "Government Printing Office": 177.3,
        "NASA": 2700,
        "National Archives and Records Administration": 252.6,
        "National Credit Union Administration": 0,
        "National Labor Relations Board": 172.2,
        "National Science Foundation": 263.9,
        "Nuclear Regulatory Commission": 406.6,
        "Office of Personnel Management": 338.9,
        "Securities and Exchange Commission": 1000,
        "Small Business Administration": 726.1,
        "Smithsonian Institution": 371.4,
        "Social Security Administration": 5800,
        "US Agency for Global Media": 176.2,
        "US Agency for International Development": 694.6
    }.items(), key=lambda item: item[1], reverse=True)
}

# Function to calculate cost per citizen
def cost_per_citizen(cost):
    return round(cost / USPop, 2)

st.title("US Government Agency Costs Per Citizen")

st.markdown(
    """
    It’s easy to call for increased government funding or criticize program cuts, but have you ever considered how much these programs actually cost you?

    Below is a breakdown of various government programs and their cost per citizen per year. Given that these expenses are covered by taxpayers, what programs would you choose to fund, and how much would you personally be willing to contribute?

    At the end, we’ll collect the data to see which programs citizens value the most.
    """
)

name = st.text_input("Name")
email = st.text_input("Email")

selected_agencies = {}

st.header("Select Programs to Fund (not all programs are listed)")
col1, col2 = st.columns([2, 3])
with col1:
    for agency, cost in agencies.items():
        cost_citizen = cost_per_citizen(cost)
        if st.checkbox(f"{agency} (${cost_citizen} per year)", key=agency):
            selected_agencies[agency] = cost
with col2:
    fig = go.Figure(go.Pie(
        labels=list(agencies.keys()),
        values=[v / 1000 for v in agencies.values()],  # Convert to millions
        textinfo='label+percent+value',
        hoverinfo='label+percent+value',
        textposition='inside',  # Moves labels inside slices
        pull=[0.1 if v / 1000 < 5 else 0 for v in agencies.values()]  # Separates small slices
    ))

    fig.update_traces(hole=0.3)
    fig.add_annotation(
        text=f"Total Budget<br>${sum(agencies.values()) / 1e6:.2f} Trillion",
        x=0.5, y=0.5, showarrow=False, font_size=20
    )

    fig.update_layout(
        title_text="Total Agency Cost Breakdown",
        height=1000, width=1000,
        showlegend=True
    )

    with st.container():
        st.plotly_chart(fig, use_container_width=True)

# Calculate total cost
selected_total = sum(selected_agencies.values())
selected_cost_per_person = round(selected_total / USPop, 2)

# Save data to Google Sheets
def save_data(name, email, selected_agencies):
    selected_agency_list = ", ".join(selected_agencies.keys())
    new_entry = [name, email, selected_agency_list, selected_total, selected_cost_per_person]

    try:
        sheet.append_row(new_entry)
        st.success("Your selections have been recorded in Google Sheets.")
    except Exception as e:
        st.error(f"Failed to save data: {e}")

if st.button("Submit Selection"):
    if not name or not email:
        st.error("Name and Email are required to submit your selection.")
    elif not selected_agencies:
        st.error("Please select at least one program to fund.")
    else:
        save_data(name, email, selected_agencies)
        save_data(name, email, selected_agencies)

# Sankey Diagram
if selected_agencies:
    st.markdown("<h1 style='text-align: center;'>🔥 <strong>TOTAL SELECTED PROGRAM COST PER CITIZEN</strong> 🔥</h1>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='text-align: center; color: red; font-size: 40px;'>🚨 ${selected_cost_per_person} PER YEAR! 🚨</h1>", unsafe_allow_html=True)

    def generate_sankey(selected_agencies):
        labels = ["Total Budget"] + list(selected_agencies.keys())
        sources = [0] * len(selected_agencies)
        targets = list(range(1, len(selected_agencies) + 1))
        values = [cost_per_citizen(cost) for cost in selected_agencies.values()]

        fig = go.Figure(go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                label=labels
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values
            )
        ))

        fig.update_layout(title_text="Selected Programs Cost Breakdown", font_size=10)
        return fig

    st.plotly_chart(generate_sankey(selected_agencies))
