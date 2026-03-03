import streamlit as st
import pandas as pd

st.set_page_config(page_title="AI模型供应链数据展示", layout="wide")
st.title("模型数据表格")

# 缓存加载+极简预处理
@st.cache_data
def load_data():
    df = pd.read_csv("data/models.csv", encoding="utf-8-sig")
    df["base_model"] = df["base_model"].fillna("无基础模型").replace("无", "无基础模型")
    df["downloads"] = pd.to_numeric(df["downloads"], errors="coerce").fillna(0).astype(int)
    df["library_name"] = df["library_name"].fillna("未知框架")
    return df

df = load_data()
col1, col2, col3 = st.columns([2,1,1])

# 1. 全局搜索
with col1:
    key = st.text_input("全局搜索", placeholder="模型ID/基础模型/框架")
    f_df = df[df.id.str.contains(key, case=False, na=False)|df.base_model.str.contains(key, case=False, na=False)|df.library_name.str.contains(key, case=False, na=False)].copy() if key else df.copy()

# 2. 框架筛选
with col2:
    fw = st.selectbox("框架筛选", ["全部"]+sorted(df.library_name.unique()))
    if fw != "全部": f_df = f_df[f_df.library_name==fw]

# 3. 基础模型筛选
with col3:
    bm = st.radio("基础模型", ["全部", "有", "无"], horizontal=True)
    if bm == "有": f_df = f_df[f_df.base_model!="无基础模型"]
    elif bm == "无": f_df = f_df[f_df.base_model=="无基础模型"]

# 4. 下载量筛选
max_dl = df.downloads.max() or 10000
min_d, max_d = st.slider("下载量范围（次）", 0, int(max_dl), (0, int(max_dl)), step=1000)
f_df = f_df[(f_df.downloads>=min_d)&(f_df.downloads<=max_d)]

# 核心表格展示
st.dataframe(f_df[["id","downloads","library_name","base_model"]], use_container_width=True, hide_index=True)

# 极简统计
st.divider()
c1,c2,c3 = st.columns(3)
with c1: st.metric("最高下载量模型", df.loc[df.downloads.idxmax(),"id"], f"{df.downloads.max():,}")
with c2: st.metric("有基础模型数", len(df[df.base_model!="无基础模型"]), f"{len(df[df.base_model!='无基础模型'])/len(df)*100:.1f}%")
with c3: st.metric("主流框架", df.library_name.value_counts().index[0], df.library_name.value_counts().iloc[0])

# 数据导出
st.download_button("导出筛选后CSV", f_df[["id","downloads","library_name","base_model"]].to_csv(index=False, encoding="utf-8-sig"), "ai_model_filtered.csv", "text/csv")