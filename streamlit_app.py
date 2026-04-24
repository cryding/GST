# This file is for Streamlit Cloud deployment
# Streamlit Cloud looks for streamlit_app.py as the entry point

import os
import streamlit as st

# Fix for deployment path issues
def get_install_path():
    """
    Safely get the install path for different deployment environments.
    This fixes the '/mount/admin/install_path: No such file or directory' error.
    """
    
    # Try to use environment variable if set
    if 'INSTALL_PATH' in os.environ:
        install_path = os.environ['INSTALL_PATH']
        if os.path.exists(install_path):
            return install_path
    
    # Try the original path (might work in some environments)
    original_path = '/mount/admin/install_path'
    if os.path.exists(original_path):
        return original_path
    
    # Fallback: use app directory
    app_dir = os.path.dirname(os.path.abspath(__file__))
    install_path = os.path.join(app_dir, 'data')
    
    # Create directory if it doesn't exist
    os.makedirs(install_path, exist_ok=True)
    return install_path

# Initialize Streamlit page config
st.set_page_config(
    page_title="E-commerce",
    page_icon="🛍️",
    layout="wide"
)

# Get the safe install path
install_path = get_install_path()

# Your e-commerce application code goes here
st.title("E-commerce Application")
st.write(f"Data directory: {install_path}")

# Add your main app logic below
# ...