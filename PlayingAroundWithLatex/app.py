import streamlit as st
import pandas as pd

# Set page configuration first
st.set_page_config(layout="wide")

# Set page title
st.title("LaTeX Content Display")

# Read the Excel file
def read_excel():
    df = pd.read_excel('LatexConvert.xlsx', header=None)
    return df  # Return the entire dataframe

# Function to process LaTeX content
def process_latex(content):
    # Convert the content to regular math expressions that MathJax can handle
    processed = str(content).replace('\\(', '$').replace('\\)', '$')
    return processed

# Get all the data
df = read_excel()

# Create expander for each column
for col_idx in range(len(df.columns)):
    with st.expander(f"Column {col_idx + 1}", expanded=True):
        # Display all non-null values in this column
        for row_idx in range(len(df)):
            if pd.notna(df.iloc[row_idx, col_idx]):  # Check if cell is not empty
                content = df.iloc[row_idx, col_idx]
                processed_content = process_latex(content)
                st.markdown(processed_content)
                st.divider()

# Add MathJax support for better LaTeX rendering
st.markdown("""
<script type="text/javascript" async
  src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-MML-AM_CHTML">
</script>
""", unsafe_allow_html=True)