import streamlit as st
from openai import OpenAI
from docx import Document
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import io
import asyncio
import edge_tts # 🔥 新增：微软超拟真语音库
from datetime import datetime

# --- 1. 基础配置 ---
st.set_page_config(page_title="商业灵感空间", page_icon="☁️", layout="wide")

# 检查 Secrets 是否配置 (防报错机制)
if "DEEPSEEK_KEY" in st.secrets:
    api_key = st.secrets["DEEPSEEK_KEY"]
else:
    st.error("⚠️ 请先在 Streamlit 后台配置 Secrets！")
    st.stop()

client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

# 初始化状态
if "history" not in st.session_state: st.session_state.history = []

# --- 2. 视觉系统 ---
st.markdown("""
<style>
    .stApp { background-color: #F5F7FA; color: #333333; }
    [data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E0E0E0; }
    .stContainer, [data-testid="stExpander"], .css-card {
        background-color: #FFFFFF; border: 1px solid #DCDFE6; border-radius: 8px; 
        padding: 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    .stButton>button {
        background-color: #0052D9; color: white; border: none; border-radius: 6px;
        height: 48px; font-weight: 600; letter-spacing: 1px; width: 100%;
    }
    .stButton>button:hover { background-color: #003CAB; color: white; }
    h1, h2, h3 { font-family: 'PingFang SC', sans-serif !important; }
    /* 播放器样式微调 */
    audio { width: 100%; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 3. 核心功能函数 ---

# 🔥 异步语音生成函数 (解决云端发声难题)
async def generate_audio_file(text, filename="output.mp3"):
    # 使用微软 Edge 的免费语音接口，声音非常自然
    # zh-CN-XiaoxiaoNeural 是目前最自然的中文女声
    communicate = edge_tts.Communicate(text, "zh-CN-XiaoxiaoNeural")
    await communicate.save(filename)

# 数据模拟
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

# 雷达图
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

# --- 4. 侧边栏 ---
with st.sidebar:
    st.image("https://api.iconify.design/icon-park-solid:brain.svg?color=%230052D9", width=50)
    st.title("云端控制台")
    st.caption("V21 Ultimate Cloud")
    
    industry = st.selectbox("行业赛道", ["🚀 TMT / 人工智能", "🛒 消费 / 零售连锁", "⚙️ 高端制造 / 硬件", "🏥 医疗 / 大健康"])
    style_mode = st.radio("AI 风格", ["麦肯锡 (专业)", "巴巴塔 (毒舌)", "硅谷教父 (激进)"])
    enable_voice = st.toggle("🔊 启用语音汇报", value=True) # 语音开关
    
    st.divider()
    creativity = st.slider("💡 创造力", 0.0, 1.0, 0.7)
    word_count = st.slider("📝 字数", 800, 3000, 1500)

# --- 5. 主界面 ---
st.title("商业灵感空间 (云端版)")

with st.form("cloud_form"):
    topic = st.text_input("💡 核心商业构想", placeholder="例如：火星奶茶店、全自动洗猫机...", key="cloud_topic_v21")
    start_btn = st.form_submit_button("🚀 启动推演 (流式生成)", use_container_width=True)

if start_btn and topic:
    # 1. 创建占位符 (用于流式显示)
    output_container = st.empty()
    full_content = ""
    
    try:
        # Phase 1: AI 流式生成 (Streaming)
        prompt = """
        【强制中文】输出商业策划案(Markdown)。结构：🎯摘要、⚡痛点、💎方案、💰模式、🛡️壁垒。
        """
        stream = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role":"system","content":f"角色:{style_mode}\n{prompt}\n字数:{word_count}"},
                      {"role":"user","content":f"项目:{topic} 赛道:{industry}"}],
            temperature=creativity,
            stream=True # 🔥 开启流式开关
        )
        
        # 实时把字打印在屏幕上
        for chunk in stream:
            if chunk.choices[0].delta.content:
                text_chunk = chunk.choices[0].delta.content
                full_content += text_chunk
                output_container.markdown(full_content + "▌") # 加个光标特效
        
        output_container.markdown(full_content) # 最后移除光标
        
        # Phase 2: 数据与图表
        rev_data, rate = generate_data(industry)
        radar_fig = plot_radar(industry)
        
        # Phase 3: 生成语音 (如果开启)
        if enable_voice:
            with st.spinner("正在合成语音汇报..."):
                # 提取摘要用于朗读
                summary_text = full_content[:150].replace("#", "").replace("*", "") + "..."
                intro = "大炉，方案已生成！" if "巴巴塔" in style_mode else "推演报告如下："
                
                # 运行异步语音生成
                asyncio.run(generate_audio_file(f"{intro} {summary_text}", "report.mp3"))
                st.audio("report.mp3", format="audio/mp3", autoplay=True) # 🔥 自动播放

        # Phase 4: 生成下载文件 (内存流)
        doc = Document()
        doc.add_heading(topic, 0)
        doc.add_paragraph(full_content)
        bio_doc = io.BytesIO()
        doc.save(bio_doc)
        bio_doc.seek(0)
        
        bio_md = io.BytesIO()
        bio_md.write(f"# {topic}\n\n{full_content}".encode('utf-8'))
        bio_md.seek(0)
        
        st.session_state.history.append({"topic": topic, "time": datetime.now().strftime('%H:%M')})

        # --- 结果展示 ---
        st.divider()
        k1, k2, k3 = st.columns(3)
        k1.metric("第5年营收", f"¥{rev_data[-1]}00万", f"+{int(rate*100)}%")
        k2.metric("复合增长率", f"{int(rate*100)}%")
        k3.metric("创造力", creativity)
        
        t1, t2 = st.tabs(["📥 下载报告", "📊 数据分析"])
        with t1:
            c1, c2 = st.columns(2)
            c1.download_button("📘 Word 报告", bio_doc, f"{topic}.docx", use_container_width=True)
            c2.download_button("📝 Markdown", bio_md, f"{topic}.md", use_container_width=True)
        with t2:
            st.plotly_chart(radar_fig, use_container_width=True)
            st.area_chart(pd.DataFrame(rev_data, columns=["营收"]), color="#0052D9")

    except Exception as e:
        st.error(f"发生错误: {e}")
