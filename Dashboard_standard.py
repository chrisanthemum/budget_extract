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

# Mainpage
        
st.title(":sparkles: Budgeting :sparkles:")
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

hide_table_row_index = """
            <style>
            tbody tr td: first-child {display:none}
            </style>
            """
st.markdown(hide_table_row_index, unsafe_allow_html=True)

# table_style = """
#             <style>
#             table.dataframe {
#                 background-color: #e5f1ff; /* Replace with your desired color */
#             }
#             </style>
#             """

# st.markdown(table_style, unsafe_allow_html=True)

## Initialise export info
file_format = 'csv'

# Set the appropriate MIME type based on the file format
mime_type = 'text/csv' 

## read in data
# Create a file uploader
uploaded_file = st.file_uploader("Upload a dataset", type=["pdf"])
date_pattern = r"\b(\d{2}/\d{2}/\d{4})\b"
# Check if a file was uploaded

if uploaded_file is not None:
    # Read the uploaded file into a DataFrame
    pdf = uploaded_file.read()  # Use pd.read_excel() for Excel files
    pdf_file = io.BytesIO(pdf)
    pdf_reader = PyPDF2.PdfReader(pdf_file)

    lines = []
    for page in pdf_reader.pages:
        page_text = page.extract_text()
        matches = re.findall(date_pattern, page_text)

        for match in matches:
            page_text = page_text.replace(match, "|" + match)

        split_text = page_text.split("|")
        lines.extend(split_text)
        
    # Create a DataFrame with 'Line' column
    df = pd.DataFrame({'Line': lines})

    # Remove leading/trailing whitespaces from 'Line' column
    df['Line'] = df['Line'].str.strip()

    # Remove empty lines
    df = df[df['Line'] != '']

    # Reset the index
    df = df.reset_index(drop=True)

    # Define regular expression pattern to match numbers
    df['Day'] = pd.to_numeric(df['Line'].str[:2],errors = 'coerce')
    mask = (df['Day'].between(1, 30, inclusive='both'))
    df = df[mask]
    df.drop(columns=['Day'], inplace=True)

    df['Amount'] = df['Line'].str.extract(r'(-?\d{1,3}(?:,\d{3})*\.\d{2})')

    # Create 'Debit' and 'Credit' columns based on the extracted amounts
    df['Debit'] = df['Amount'].where(~pd.isna(df['Amount']) & df['Amount'].str.startswith('-'))
    df['Credit'] = df['Amount'].where(pd.isna(df['Debit']))
    df['Text'] = df['Line'].str.split(' ', n = 2).str[2]
    df['Text'] = df['Text'].str.replace(r'^\d+(,\d+)?(.\d+)', '', regex=True).str.strip()
    df.drop(columns=['Amount'], inplace=True)
    df.fillna(0, inplace=True)
    df = df.reset_index(drop=True)

    # Create date
    df['Date'] = df['Line'].str.extract(r'(\d{2}/\d{2}/\d{4})')
    df['Date_new'] = pd.to_datetime(df['Date'].str.split().str[0],format='%d/%m/%Y')

    # df['Date_new'] = pd.to_datetime(df['Date']).date
    df['Date_new'] = df['Date_new'].dt.strftime('%Y-%m-%d')
    # df['Date_new'] = df['Date_new'].dt.strftime('%d/%m/%Y')
    df.drop(columns=['Date'], inplace=True)
    df.rename(columns={'Date_new': 'Date'}, inplace=True)

    # Reset the index
    df = df.reset_index(drop=True)

    # Drop the first two rows
    df = df.drop([0, 1])
    
    df = df.reset_index(drop=True)
    ## Sidebar

    # Create data
    day = list(range(1, 31))
    month = sorted(['Jan','Feb','Mar','Apr','May', 'Jun','Jul','Aug','Sep','Oct','Nov','Dec'], key = lambda m:['Jan','Feb','Mar','Apr','May', 'Jun','Jul','Aug','Sep','Oct','Nov','Dec'].index(m)) 
    year = [2022,2023]

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
    # Convert string to datetime object
    # compare_date = pd.to_datetime('{start_year_choice}-{start_month_choice}-{start_day_choice}')

    # Compare Date_new column with the datetime object
    # mask = df['Date'] >= compare_date

    # Filter the dataframe based on the comparison
    # filtered_df = df[mask]


    # Create a formatted string representing the date
    # start_date_string = f"{start_year_choice} {start_month_choice} {start_day_choice}"
    # end_date_string = f"{end_year_choice} {end_month_choice} {end_day_choice}"

    start_date_string = f"{start_year_choice}-{start_month_choice}-{start_day_choice}"
    end_date_string = f"{end_year_choice}-{end_month_choice}-{end_day_choice}"


    # Parse the string into a datetime object
    # start_date = datetime.strptime(start_date_string, "%Y %b %d")
    # end_date = datetime.strptime(end_date_string, "%Y %b %d")

    start_date = pd.to_datetime(start_date_string).strftime('%Y-%m-%d')
    end_date = pd.to_datetime(end_date_string).strftime('%Y-%m-%d')
    
    df_selection = df.query(
        "Date >= @start_date & Date <= @end_date"
    )
    
    
    st.write(df_selection)

    # Prepare the file name and content
    file_name = f'dataset.{file_format}'
    file_content = df_selection.to_csv(index=False) 
    st.download_button(label='Download Dataset', data=file_content, file_name=file_name, mime=mime_type)


    st.write(df)
# st.table gives you variable row sizes where text flows over but doesn't include colour in headings. st.write does

    # Prepare the file name and content
    file_name_full = f'full_dataset.{file_format}'
    file_content_full = df.to_csv(index=False) 
    st.download_button(label='Download Full Dataset', data=file_content_full, file_name=file_name_full,mime=mime_type)

        
else:
    st.write("Please upload a file to continue.")


