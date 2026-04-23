import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime

# Page Configuration
st.set_page_config(page_title="Ecommerce GST Assistant", layout="wide")

# --- CSS for Mobile Optimization ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; background-color: #4F46E5; color: white; }
    .stDownloadButton>button { width: 100%; border-radius: 8px; height: 3em; background-color: #059669; color: white; }
    div[data-testid="stExpander"] { background-color: white; border-radius: 10px; }
    </style>
    """, unsafe_base_code=True)

# --- State Management ---
if 'orders' not in st.session_state:
    st.session_state.orders = []

# --- Business Logic Functions ---
def calculate_gst(row, home_state):
    taxable = row['Taxable Value']
    rate = row['GST Rate']
    total_gst = (taxable * rate) / 100
    
    is_interstate = row['Customer State'].strip().lower() != home_state.strip().lower()
    
    if is_interstate:
        return pd.Series([total_gst, 0, 0, 'IGST'])
    else:
        return pd.Series([0, total_gst/2, total_gst/2, 'CGST/SGST'])

# --- Sidebar / Settings ---
st.sidebar.header("⚙️ Settings")
home_state = st.sidebar.text_input("Your Business State", value="West Bengal")
st.sidebar.info("Ekhane apnar nijo state likhun jate application automatic IGST/CGST detect korte pare.")

# --- UI Header ---
st.title("📦 Ecommerce GST Calculator")
st.markdown("Amazon, Flipkart, Meesho sellers-der jonno manual entry system.")

# --- Data Input Section ---
with st.expander("➕ Add New Order Details", expanded=len(st.session_state.orders) == 0):
    col1, col2 = st.columns(2)
    
    with col1:
        platform = st.selectbox("Platform", ["Amazon", "Flipkart", "Meesho", "Other"])
        order_id = st.text_input("Order ID / Invoice No")
        order_date = st.date_input("Order Date", datetime.now())
        cust_state = st.text_input("Customer State (Place of Supply)", placeholder="e.g. Maharashtra")

    with col2:
        taxable_val = st.number_input("Taxable Value (Item Price)", min_value=0.0, step=1.0)
        gst_rate = st.selectbox("GST Rate (%)", [5, 12, 18, 28], index=2)
        commission = st.number_input("Marketplace Commission Fee", min_value=0.0)
        tcs = st.number_input("TCS (Tax Collected by Platform)", min_value=0.0)

    if st.button("Add to List"):
        if order_id and cust_state and taxable_val > 0:
            new_order = {
                "Platform": platform,
                "Order ID": order_id,
                "Date": order_date,
                "Customer State": cust_state,
                "Taxable Value": taxable_val,
                "GST Rate": gst_rate,
                "Commission": commission,
                "TCS": tcs
            }
            st.session_state.orders.append(new_order)
            st.success("Order Added!")
        else:
            st.error("Please fill required fields (Order ID, State, Taxable Value)")

# --- Data Table & Excel Generation ---
if st.session_state.orders:
    st.subheader("📋 Order Records")
    df = pd.DataFrame(st.session_state.orders)
    
    # Apply Calculations
    df[['IGST', 'CGST', 'SGST', 'Type']] = df.apply(lambda x: calculate_gst(x, home_state), axis=1)
    df['Commission GST (18%)'] = df['Commission'] * 0.18
    df['Total Tax'] = df['IGST'] + df['CGST'] + df['SGST']
    
    st.dataframe(df, use_container_width=True)

    if st.button("🗑️ Clear All Entries"):
        st.session_state.orders = []
        st.rerun()

    # --- Excel Preparation ---
    st.divider()
    st.subheader("📂 Report Generation")
    
    # 1. State-wise Summary for GSTR-1
    gstr1_summary = df.groupby(['Customer State', 'GST Rate']).agg({
        'Taxable Value': 'sum',
        'IGST': 'sum',
        'CGST': 'sum',
        'SGST': 'sum'
    }).reset_index()

    # 2. GSTR-3B Summary
    total_taxable = df['Taxable Value'].sum()
    total_tax = df['Total Tax'].sum()
    total_itc = df['Commission GST (18%)'].sum()

    gstr3b_data = pd.DataFrame([
        {"Description": "3.1(a) Outward Taxable Supplies", "Value": total_taxable, "Tax Amount": total_tax},
        {"Description": "4(A) ITC Available (Commission)", "Value": df['Commission'].sum(), "Tax Amount": total_itc},
        {"Description": "Net GST Payable", "Value": "-", "Tax Amount": total_tax - total_itc}
    ])

    # Function to create Excel
    def to_excel(df_list, sheet_names):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            for d, name in zip(df_list, sheet_names):
                d.to_excel(writer, sheet_name=name, index=False)
        return output.getvalue()

    excel_data = to_excel(
        [df, gstr1_summary, gstr3b_data], 
        ['Detailed Sales', 'State-wise Summary', 'GSTR-3B Summary']
    )

    st.download_button(
        label="📥 Download Ready-made GST Excel",
        data=excel_data,
        file_name=f"GST_Report_{datetime.now().strftime('%d_%m_%Y')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("Ekhono kono data entry kora hoyni. Uporer form theke order details add korun.")

# --- Footer Info ---
st.markdown("---")
st.caption("Developed for Ecommerce Sellers | GST Calculation based on Place of Supply rules.")
