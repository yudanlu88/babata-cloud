import streamlit as st
from openai import OpenAI
from docx import Document
import time
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go
import io # 新增：用于在内存中处理文件

# --- 1. 基础配置 ---
# 注意：在云端部署时，API Key 最好放在 Secrets 里，但为了方便你第一次部署，这里先保留。
# 如果部署后报错 Key 无效，需要在 Streamlit 后台重新填一下 Key。
client = OpenAI(api_key="sk-9f67a5b127014879b411c00a9b4a1cd9", base_url="https://api.deepseek.com")
st.set_page_config(page_title="商业灵感空间", page_icon="☁️", layout="wide")

# 初始化状态
if "history" not in st.session_state: st.session_state.history = []

# --- 2. 视觉系统 (V18 务实风格) ---
st.markdown("""
<style>
    .stApp { background-color: #F5F7FA; color: #333333; }
    [data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E0E0E0; }
    .stContainer, [data-testid="stExpander"], .css-card {
        background-color: #FFFFFF; border: 1px solid #DCDFE6; border-radius: 6px; 
        padding: 24px; box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .stButton>button {
        background-color: #0052D9; color: white; border: none; border-radius: 6px;
        height: 45px; font-weight: 600; letter-spacing: 1px;
    }
    .stButton>button:hover { background-color: #003CAB; color: white; }
    h1, h2, h3, p, div { font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif !important; }
    header {visibility: hidden;}
    [data-testid="stMetricValue"] { color: #0052D9 !important; font-weight: bold; }
    .stTextInput>div>div>input { border: 1px solid #DCDFE6; border-radius: 6px; padding: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 3. 侧边栏 ---
with st.sidebar:
    st.image("https://api.iconify.design/icon-park-solid:brain.svg?color=%230052D9", width=50)
    st.title("云端控制台")
    st.caption("版本: V20 Cloud Native")
    
    st.markdown("### ⚙️ 参数设定")
    industry = st.selectbox("行业赛道", ["🚀 TMT / 人工智能", "🛒 消费 / 零售连锁", "⚙️ 高端制造 / 硬件", "🏥 医疗 / 大健康"])
    style_mode = st.radio("AI 风格", ["麦肯锡 (专业)", "巴巴塔 (毒舌)", "硅谷教父 (激进)"])
    st.markdown("---")
    creativity = st.slider("💡 创造力", 0.0, 1.0, 0.7)
    word_count = st.slider("📝 字数", 800, 3000, 1500)
    
    st.markdown("---")
    if st.session_state.history:
        for item in reversed(st.session_state.history[-5:]): 
            st.text(f"{item['time']} | {item['topic']}")

# --- 4. 数据逻辑 ---
def generate_data(industry_str, years=5):
    base = 100 
    if "AI" in industry_str: rate, vol = 0.55, 0.25 
    elif "零售" in industry_str: rate, vol = 0.15, 0.05 
    elif "制造" in industry_str: rate, vol = 0.10, 0.03 
    else: rate, vol = 0.30, 0.10 
    data = []; curr = base
    for _ in range(years):
        curr = curr * (1 + rate + np.random.normal(0, vol))
        data.append(int(curr))
    return data, rate

def plot_radar(industry_str):
    cats = ['技术', '市场', '资金', '团队', '政策', '竞争']
    if "AI" in industry_str: vals = [9, 10, 8, 9, 6, 9]
    elif "消费" in industry_str: vals = [5, 9, 7, 7, 4, 10]
    else: vals = [7, 8, 9, 6, 5, 8]
    fig = go.Figure(go.Scatterpolar(
        r=vals, theta=cats, fill='toself', line_color='#0052D9', fillcolor='rgba(0, 82, 217, 0.1)'
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 10], linecolor='#DCDFE6')),
        showlegend=False, margin=dict(l=40, r=40, t=20, b=20),
        font=dict(family="Microsoft YaHei", size=12),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

# --- 5. 主界面 ---
st.title("商业灵感空间 (云端版)")

with st.form("cloud_form"):
    col1, col2 = st.columns([3, 1])
    with col1:
        topic = st.text_input("💡 核心商业构想", placeholder="例如：脑机接口...", key="cloud_topic")
    with col2:
        st.write("")
        st.write("")
        start_btn = st.form_submit_button("🚀 启动推演", use_container_width=True)

if start_btn and topic:
    bar = st.progress(0, text="DeepSeek 正在接入...")
    
    try:
        # Phase 1: AI
        time.sleep(0.2)
        prompt = """
        【强制中文】输出商业策划案(Markdown)。结构：🎯摘要、⚡痛点、💎方案、💰模式、🛡️壁垒。
        """
        res = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role":"system","content":f"角色:{style_mode}\n{prompt}\n字数:{word_count}"},
                      {"role":"user","content":f"项目:{topic} 赛道:{industry}"}],
            temperature=creativity
        )
        content = res.choices[0].message.content
        
        # Phase 2: Data & Files
        bar.progress(60, text="构建模型...")
        rev_data, rate = generate_data(industry)
        radar_fig = plot_radar(industry)
        
        # 生成 Word (内存流)
        doc = Document()
        doc.add_heading(topic, 0)
        doc.add_paragraph(content)
        bio_doc = io.BytesIO()
        doc.save(bio_doc)
        bio_doc.seek(0)
        
        # 生成 Markdown (内存流)
        bio_md = io.BytesIO()
        bio_md.write(f"# {topic}\n\n{content}".encode('utf-8'))
        bio_md.seek(0)
        
        st.session_state.history.append({"topic": topic, "time": datetime.now().strftime('%H:%M')})
        bar.progress(100, text="完成"); time.sleep(0.5); bar.empty()

        # Phase 3: Display
        st.success("✅ 推演完成")
        with st.expander("🤖 核心摘要", expanded=True):
            st.markdown(content[:200] + "...")
            
        st.write("---")
        k1, k2, k3 = st.columns(3)
        k1.metric("第5年营收", f"¥{rev_data[-1]}00万", f"+{int(rate*100)}%")
        k2.metric("复合增长率", f"{int(rate*100)}%")
        k3.metric("创造力", creativity)
        st.write("---")
        
        t1, t2 = st.tabs(["📄 报告 & 下载", "📈 数据模型"])
        with t1:
            c1, c2 = st.columns(2)
            c1.download_button("📥 Word 报告", bio_doc, f"{topic}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
            c2.download_button("📝 Markdown", bio_md, f"{topic}.md", "text/markdown", use_container_width=True)
            st.markdown(content)
        with t2:
            st.plotly_chart(radar_fig, use_container_width=True)
            st.area_chart(pd.DataFrame(rev_data, columns=["营收"]), color="#0052D9")

    except Exception as e:
        st.error(f"错误: {e}")