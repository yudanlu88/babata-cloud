import streamlit as st
from openai import OpenAI
from docx import Document
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import io
import asyncio
import edge_tts
import os
from datetime import datetime

# --- 1. 基础配置 ---
st.set_page_config(page_title="巴巴塔万能助手", page_icon="⚡", layout="wide")

if "DEEPSEEK_KEY" in st.secrets:
    api_key = st.secrets["DEEPSEEK_KEY"]
else:
    st.error("⚠️ 请先配置 Secrets！")
    st.stop()

client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

# --- 2. 数据库逻辑 (新增核心模块) ---
DB_FILE = "babata_memory.csv"

def init_db():
    """初始化数据库：如果文件不存在，就创建一个新的"""
    if not os.path.exists(DB_FILE):
        df = pd.DataFrame(columns=["时间", "模式", "主题", "摘要"])
        df.to_csv(DB_FILE, index=False)

def save_to_db(mode, topic, content):
    """保存记忆：把新的记录追加到 CSV 文件末尾"""
    init_db()
    # 截取前30个字作为摘要
    summary = content[:30].replace("#", "").replace("*", "") + "..."
    new_data = pd.DataFrame([{
        "时间": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "模式": mode,
        "主题": topic,
        "摘要": summary
    }])
    new_data.to_csv(DB_FILE, mode='a', header=False, index=False)

def load_from_db():
    """读取记忆：加载所有历史记录"""
    init_db()
    try:
        return pd.read_csv(DB_FILE)
    except:
        return pd.DataFrame(columns=["时间", "模式", "主题", "摘要"])

# --- 3. 异步语音函数 ---
async def generate_audio_file(text, filename="output.mp3"):
    communicate = edge_tts.Communicate(text, "zh-CN-XiaoxiaoNeural")
    await communicate.save(filename)

# --- 4. 侧边栏 ---
with st.sidebar:
    st.title("⚡ 巴巴塔控制台")
    st.caption("V24 Memory Activated")
    
    app_mode = st.selectbox("切换功能模式", 
        ["💼 商业策划案", "📕 小红书爆款", "📊 职场周报大师", "❤️ 情感/哄人专家"]
    )
    
    st.divider()
    
    if app_mode == "💼 商业策划案":
        industry = st.selectbox("行业赛道", ["🚀 AI/科技", "🛒 消费/零售", "🏥 医疗", "⚙️ 制造"])
    
    style_mode = st.radio("AI 语气风格", ["专业理性", "毒舌巴巴塔", "温柔贴心", "热情激昂"])
    word_count = st.slider("生成字数", 200, 3000, 800)
    enable_voice = st.toggle("🔊 开启语音朗读", value=True)

# --- 5. 智能 Prompt ---
def get_prompt(mode):
    if mode == "💼 商业策划案":
        return """【强制中文】输出商业策划案(Markdown)。结构：🎯摘要、⚡痛点、💎方案、💰模式。"""
    elif mode == "📕 小红书爆款":
        return """你是小红书爆款博主。要求：1.标题带emoji极其抓眼球。2.正文多emoji。3.包含：🌟亮点、📝感受、💡避雷。"""
    elif mode == "📊 职场周报大师":
        return """你是互联网大厂P8。请把用户输入的简单内容扩写成高大上的周报。多用黑话。"""
    elif mode == "❤️ 情感/哄人专家":
        return """你是顶级情感专家。如果是哄人，要温柔体贴；如果是分析感情，要一针见血。"""

# --- 6. 主界面 ---
st.title(f"{app_mode}") 

# 历史记录预览 (侧边栏小彩蛋)
history_df = load_from_db()
with st.sidebar:
    st.divider()
    st.metric("📚 记忆库", f"已存储 {len(history_df)} 条")

with st.form("universal_form"):
    if app_mode == "💼 商业策划案": placeholder = "输入项目点子..."
    elif app_mode == "❤️ 情感/哄人专家": placeholder = "输入情感困惑..."
    else: placeholder = "输入核心主题..."
    
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
        
        # 🔥 (2) 存入记忆库 (关键动作)
        save_to_db(app_mode, user_input, full_text)
        st.toast("✅ 已存入历史档案！") # 弹窗提示
        
        # (3) 语音朗读
        if enable_voice:
            with st.spinner("正在合成完整语音..."):
                read_text = full_text.replace("#", "").replace("*", "").replace("=", "")
                asyncio.run(generate_audio_file(read_text, "voice.mp3"))
                st.audio("voice.mp3", autoplay=True)
        
        # (4) 结果展示区 (新增历史档案 Tab)
        st.divider()
        if app_mode == "💼 商业策划案":
            t1, t2, t3 = st.tabs(["📥 下载报告", "📊 数据分析", "📜 历史档案"])
        else:
            t1, t2 = st.tabs(["📥 下载内容", "📜 历史档案"])
            
        with t1:
            st.markdown("### 📝 文档下载")
            # Word生成逻辑略...
            bio_md = io.BytesIO()
            bio_md.write(full_text.encode('utf-8'))
            st.download_button("下载 Markdown", bio_md, "report.md")

        with t2 if app_mode != "💼 商业策划案" else t3:
            # 🔥 历史记录展示区
            st.markdown("### 📜 记忆回溯")
            # 重新加载最新数据
            latest_df = load_from_db()
            # 显示漂亮的表格
            st.dataframe(
                latest_df.iloc[::-1], # 倒序显示，新的在上面
                column_config={
                    "时间": st.column_config.TextColumn("生成时间", width="medium"),
                    "模式": st.column_config.TextColumn("类型", width="small"),
                    "主题": st.column_config.TextColumn("Prompt", width="medium"),
                    "摘要": st.column_config.TextColumn("内容预览", width="large"),
                },
                use_container_width=True,
                hide_index=True
            )

        # 商业图表逻辑
        if app_mode == "💼 商业策划案":
            with t2:
                data = [100, 150, 230, 350, 500]
                st.area_chart(pd.DataFrame(data, columns=["营收"]))

    except Exception as e:
        st.error(f"出错啦: {e}")
