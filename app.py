import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile
from pathlib import Path

st.set_page_config(
    page_title="Icon Grid Printer",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    :root {
        --primary-color: #007bff;
        --primary-hover: #0056b3;
        --success-color: #28a745;
        --success-hover: #218838;
        --border-radius: 8px;
        --padding: 1rem;
    }

    .main {
        padding: 2rem;
    }
    
    .stButton>button {
        background-color: var(--primary-color);
        color: white;
        border-radius: var(--border-radius);
        padding: 0.5rem 2rem;
        font-size: 16px;
        border: none;
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stButton>button:hover {
        background-color: var(--primary-hover);
        transform: translateY(-2px);
    }
    
    /* Info & success boxes - auto adjust for dark/light mode */
    .info-box, .success-box {
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 4px;
    }
    
    .info-box {
        background-color: rgba(0, 123, 255, 0.1);
        border-left: 4px solid var(--primary-color);
    }
    
    .success-box {
        background-color: rgba(40, 167, 69, 0.1);
        border-left: 4px solid var(--success-color);
    }
    
    .stDownloadButton>button {
        background-color: var(--success-color);
        color: white;
        width: 100%;
        padding: 0.75rem;
        font-size: 16px;
        border-radius: var(--border-radius);
    }
    
    .stDownloadButton>button:hover {
        background-color: var(--success-hover);
    }
    
    .upload-section {
        border: 2px dashed #888;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        margin: 2rem 0;
    }
</style>
""", unsafe_allow_html=True)