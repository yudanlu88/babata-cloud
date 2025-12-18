import streamlit as st
from openai import OpenAI
from docx import Document
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import io
import asyncio
import edge_tts
from datetime import datetime

# --- 1. 基础配置 ---
st.set_page_config(page_title="巴巴塔万能助手", page_icon="⚡", layout="wide")

# 检查 Secrets 密码
if "DEEPSEEK_KEY" in st.secrets:
    api_key = st.secrets["DEEPSEEK_KEY"]
else:
    st.error("⚠️ 请先在 Streamlit 后台配置 Secrets！")
    st.stop()

client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

if "history" not in st.session_state: st.session_state.history = []

# --- 2. 视觉系统 ---
st.markdown("""
<style>
    .stApp { background-color: #F5F7FA; }
    .stButton>button {
        background-color: #0052D9; color: white; border-radius: 6px;
        height: 48px; font-weight: 600; width: 100%;
    }
    .stButton>button:hover { background-color: #003CAB; }
</style>
""", unsafe_allow_html=True)

# --- 3. 异步语音函数 (已解锁时长限制) ---
async def generate_audio_file(text, filename="output.mp3"):
    # zh-CN-XiaoxiaoNeural 是目前最自然的中文女声
    communicate = edge_tts.Communicate(text, "zh-CN-XiaoxiaoNeural")
    await communicate.save(filename)

# --- 4. 侧边栏 (控制台) ---
with st.sidebar:
    st.title("⚡ 巴巴塔控制台")
    st.caption("V23 Unlocked Voice")
    
    # 功能模式选择
    app_mode = st.selectbox("切换功能模式", 
        ["💼 商业策划案", "📕 小红书爆款", "📊 职场周报大师", "❤️ 情感/哄人专家"]
    )
    
    st.divider()
    
    # 商业模式专属选项
    if app_mode == "💼 商业策划案":
        industry = st.selectbox("行业赛道", ["🚀 AI/科技", "🛒 消费/零售", "🏥 医疗", "⚙️ 制造"])
    
    style_mode = st.radio("AI 语气风格", ["专业理性", "毒舌巴巴塔", "温柔贴心", "热情激昂"])
    word_count = st.slider("生成字数", 200, 3000, 800) # 字数上限调高到3000
    enable_voice = st.toggle("🔊 开启语音朗读", value=True)

# --- 5. 智能 Prompt (核心大脑) ---
def get_prompt(mode):
    if mode == "💼 商业策划案":
        return """【强制中文】输出商业策划案(Markdown)。结构：🎯摘要、⚡痛点、💎方案、💰模式。请表现得极具商业洞察力。"""
    elif mode == "📕 小红书爆款":
        return """你是小红书爆款博主。要求：1.标题带emoji极其抓眼球。2.正文多emoji，语气像闺蜜安利。3.包含：🌟亮点、📝感受、💡避雷。4.结尾带#标签。"""
    elif mode == "📊 职场周报大师":
        return """你是互联网大厂P8。请把用户输入的简单内容扩写成高大上的周报。多用黑话：赋能、闭环、抓手、沉淀、复盘。结构：✅产出、🚧卡点、📅规划。"""
    elif mode == "❤️ 情感/哄人专家":
        return """你是顶级情感专家。如果是哄人，要温柔体贴，提供情绪价值；如果是分析感情，要一针见血但充满关怀。请给出具体的行动建议。"""

# --- 6. 主界面 ---
st.title(f"{app_mode}") 

with st.form("universal_form"):
    if app_mode == "💼 商业策划案":
        placeholder = "输入项目点子，如：火星奶茶店..."
    elif app_mode == "❤️ 情感/哄人专家":
        placeholder = "输入情感困惑，如：女朋友生气了怎么哄？..."
    else:
        placeholder = "输入核心主题..."
        
    user_input = st.text_input("💡 请输入内容", placeholder=placeholder)
    submitted = st.form_submit_button("🚀 立即生成")

# --- 7. 执行逻辑 ---
if submitted and user_input:
    output_container = st.empty()
    full_text = ""
    
    # (1) AI 生成
    prompt_sys = get_prompt(app_mode)
    try:
        stream = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": f"{prompt_sys}\n语气:{style_mode}\n字数:{word_count}"},
                {"role": "user", "content": user_input}
            ],
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                full_text += chunk.choices[0].delta.content
                output_container.markdown(full_text + "▌")
        output_container.markdown(full_text)
        
        # (2) 语音朗读 (关键修改处)
        if enable_voice:
            # 提示语变了，告诉用户因为字多需要等一下
            with st.spinner("正在合成完整语音 (字数较多，请稍等 5-10 秒)..."):
                
                # 🔥 修改处：去掉了切片限制，现在会读完全文
                # 为了防止特殊符号导致语音库报错，还是建议简单清洗一下
                read_text = full_text.replace("#", "").replace("*", "").replace("=", "").replace("-", "")
                
                # 生成完整文件
                asyncio.run(generate_audio_file(read_text, "voice.mp3"))
                st.audio("voice.mp3", autoplay=True)
        
        # (3) 商业图表 (仅商业模式显示)
        if app_mode == "💼 商业策划案":
            st.divider()
            st.subheader("📊 商业数据模型")
            data = [100, 150, 230, 350, 500]
            df = pd.DataFrame(data, columns=["预估营收(万)"])
            st.area_chart(df)
