## model setup
# !pip install PyPDF2
# !pip install --user --upgrade scikit-learn

import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import datetime
import io

import PyPDF2
import pandas as pd
import re
from IPython.display import display
from sklearn.feature_extraction.text import CountVectorizer

st.set_page_config(page_title = "Budgeting extract",
                  page_icon = ":bar_chart:",
                  layout = 'wide'
)

## Initialise export info
file_format = 'csv'

# Set the appropriate MIME type based on the file format
mime_type = 'text/csv' 

## read in data
# Create a file uploader
uploaded_file = st.file_uploader("Upload a dataset", type=["pdf"])

# Check if a file was uploaded
if uploaded_file is not None:
    # Read the uploaded file into a DataFrame
    pdf = uploaded_file.read()  # Use pd.read_excel() for Excel files
    pdf_file = io.BytesIO(pdf)
    pdf_reader = PyPDF2.PdfReader(pdf_file)
# df = pd.read_excel(io='C:\\Users\\chris\\Desktop\\NLP\\Budgeting\\2. Output\\ing statement.xlsx')
    lines = []
    for page in pdf_reader.pages:
        lines.extend(page.extract_text().split('\n'))

# Create a DataFrame with 'Line' column
df = pd.DataFrame({'Line': lines})

# Remove leading/trailing whitespaces from 'Line' column
df['Line'] = df['Line'].str.strip()

# Remove empty lines
df = df[df['Line'] != '']

# Reset the index
df = df.reset_index(drop=True)

# Print the long-format DataFrame
# print(df)

# Define regular expression pattern to match numbers
pattern = r'\d+'

# Function to extract first number from a string
def extract_date(text):
    match = re.search(pattern, text)
    if match:
        return match.group()
    else:
        return None

# Apply the function to the 'Line' column to extract the first number
df['Day'] = df['Line'].apply(extract_date)

# Print the updated DataFrame
# print(df)


# Define regular expression pattern to match months
# Given list of strings
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Function to extract the word before the specified words in a given string
def extract_month(line):
    
    for month in months:
        if month in line:
            return month
    return None

# Apply the function to the 'Line' column to extract the word before the specified words
df['Month'] = df['Line'].apply(extract_month)

# Print the updated DataFrame
# print(df)

# Define regular expression pattern to match years
# Given list of strings
years = ["2022","2023"]

# Function to extract the word before the specified words in a given string
def extract_year(line):
    
    for year in years:
        if year in line:
            return year
    return None

# Apply the function to the 'Line' column to extract the word before the specified words
df['Year'] = df['Line'].apply(extract_year)

# Print the updated DataFrame
# print(df)

df.dropna(subset=['Day', 'Month', 'Year'], inplace=True)
# Convert 'Day' and 'Year' column to numeric values
df['Day'] = pd.to_numeric(df['Day'], errors='coerce')
df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
df = df.drop(df[df['Day'] > 31].index)

df['Amount'] = df['Line'].str.extract(r'(-?\$[\d.,]+)')

# Create 'Debit' and 'Credit' columns based on the extracted amounts
df['Debit'] = df['Amount'].where(~pd.isna(df['Amount']) & df['Amount'].str.startswith('-'))
df['Credit'] = df['Amount'].where(pd.isna(df['Debit']))
df['Text'] = df['Line'].str.extract(r'\d{4}\s((?:\w+\s?)+)')

# Drop the 'Amount' column
df.drop(columns=['Amount'], inplace=True)
df.fillna(0, inplace=True)
df = df.reset_index(drop=True)

month_mapping = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}

# Map the month names to numeric values and combine day, month, and year columns into a single date column
df['Date'] = pd.to_datetime(df['Day'].astype(str) + '-' + df['Month'].map(month_mapping).astype(str) + '-' + df['Year'].astype(str), format='%d-%m-%Y')





## Sidebar

# Create data
day = sorted(df['Day'].drop_duplicates())
month = sorted(df['Month'].drop_duplicates(), key = lambda m:['Jan','Feb','Mar','Apr','May', 'Jun','Jul','Aug','Sep','Oct','Nov','Dec'].index(m))         
year = sorted(df['Year'].drop_duplicates())

st.sidebar.header("Please filter start date")

start_day_choice = st.sidebar.selectbox('Select your day:', day,
    key = "start_day")
start_month_choice = st.sidebar.selectbox('Select your month', month,
    key = "start_month")
start_year_choice = st.sidebar.selectbox('Select your year', year,
    key = "start_year")

st.sidebar.header("Please filter end date")

end_day_choice = st.sidebar.selectbox('Select your day:', day,
    key = "end_day")
end_month_choice = st.sidebar.selectbox('Select your month', month,
    key = "end_month")
end_year_choice = st.sidebar.selectbox('Select your year', year,
    key = "end_year")

## Execute filters
# Create a formatted string representing the date
start_date_string = f"{start_year_choice} {start_month_choice} {start_day_choice}"
end_date_string = f"{end_year_choice} {end_month_choice} {end_day_choice}"

# Parse the string into a datetime object
start_date = datetime.strptime(start_date_string, "%Y %b %d")
end_date = datetime.strptime(end_date_string, "%Y %b %d")

df_selection = df.query(
    "Date >= @start_date & Date <= @end_date"
)

st.dataframe(df_selection)

# Prepare the file name and content
file_name = f'dataset.{file_format}'
file_content = df_selection.to_csv(index=False) 
st.download_button(label='Download Dataset', data=file_content, file_name=file_name, mime=mime_type)


st.dataframe(df)

# Prepare the file name and content
file_name_full = f'full_dataset.{file_format}'
file_content_full = df.to_csv(index=False) 
st.download_button(label='Download Full Dataset', data=file_content_full, file_name=file_name_full,mime=mime_type)


