# streamlit_app.py
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

st.set_page_config(layout="wide")
st.title("Hugging Face AI模型供应链可视化")

# 读取可视化HTML
with open("output/html/supply_chain.html", "r", encoding="utf-8") as f:
    html = f.read()

# 展示
components.html(html, height=800)

# 展示数据
st.subheader("核心数据预览")
df = pd.read_csv("data/processed/hf_top1000_model_full.csv")
st.dataframe(df.head(20))