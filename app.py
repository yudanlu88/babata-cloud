导入 streamlit 为 st
从 openai 导入 OpenAI
从 docx 导入 文档
导入 pandas 为 pd
导入 numpy 为 np
导入 plotly.graph_objects 为 go
导入 输入输出
导入 asyncio
导入 edge_tts
从 日期时间 导入 日期时间

# --- 1. 基础配置 ---
st.设置页面配置(页面标题="巴巴塔万能助手", 页面图标="⚡", 布局="宽屏")

如果 "DEEPSEEK_KEY" 在 st.秘密:
    api_key = st.secrets["DEEPSEEK_KEY"]
否则:
    st.错误("⚠️ 请先配置 Secrets！")
    街。停止()

client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

如果 "历史" 不在  st.会话状态中: st.会话状态.历史 = []

# --- 2. 视觉系统 ---
st.markdown('''
<style>
    .stApp { 背景颜色: #F5F7FA; }
    按钮 .stButton>button {
        背景颜色: #0052D9; 颜色: 白色; 边框半径: 6px;
        高度：48px；字体粗细：600；宽度：100%；
    }
    .stButton>button:hover { background-color: #003CAB; }

""", unsafe_allow_html=真)

# --- 3. 异步语音函数 ---
异步 定义 生成音频文件(文本, 文件名="输出.mp3"):
    communicate = edge_tts.沟通(文本, "zh-CN-XiaoxiaoNeural")
    等待 通讯。保存(文件名)

# --- 4. 侧边栏 (控制台) ---
与 st.侧边栏:
    st.title("⚡ 巴巴塔控制台")
    
    # 🔥 核心升级：模式选择
    app_mode = st.selectbox("切换功能模式", 
        ["💼 商业策划案", "📕 小红书爆款", "📊 职场周报大师", "❤️ 情感/哄人专家"]
    )
    
    st.分隔符()
    
    # 根据模式不同，显示不同的选项
    if app_mode == "💼 商业策划案":
        industry = st.selectbox("行业赛道", ["🚀 AI/科技", "🛒 消费/零售", "🏥 医疗", "⚙️ 制造"])
    
    style_mode = st.radio("AI 语气风格", ["专业理性", "毒舌巴巴塔", "温柔贴心", "热情激昂"])
    word_count = st.slider("生成字数", 200, 2000, 800)
    enable_voice = st.toggle("🔊 开启语音朗读", value=True)

# --- 5. 智能 Prompt (核心大脑) ---

def get_prompt(mode):
    if mode == "💼 商业策划案":
        return """

        return """你是小红书爆款博主。要求：1.标题带emoji极其抓眼球。2.正文多emoji，语气像闺蜜安利。3.包含：🌟亮点、📝感受、💡避雷。4.结尾带#标签。"""
    elif mode == "📊 职场周报大师":
        return """你是互联网大厂P8。请把用户输入的简单内容扩写成高大上的周报。多用黑话：赋能、闭环、抓手、沉淀、复盘。结构：✅产出、🚧卡点、📅规划。"""
    elif mode == "❤️ 情感/哄人专家":
        return """你是顶级情感专家。如果是哄人，要温柔体贴，提供情绪价值；如果是分析感情，要一针见血但充满关怀。请给出具体的行动建议。"""

# --- 6. 主界面 ---


with st.form("universal_form"):
    # 根据模式改变输入框的提示语
    if app_mode == "💼 商业策划案":



    else:

        
    user_input = st.text_input("💡 请输入内容", placeholder=placeholder)
    submitted = st.form_submit_button("🚀 立即生成")

# --- 7. 执行逻辑 ---
if submitted and user_input:
        placeholder = 

    
        placeholder = 
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
        
        # (2) 语音朗读
        if enable_voice:
            with st.spinner("正在生成语音..."):
                # 截取前100字朗读，避免读太久
                # 去掉了 [:150]，它就会老老实实读完每一个字
                read_text = full_text.replace("#", "").replace("*", "")
                asyncio.run(generate_audio_file(read_text, "voice.mp3"))
                st.audio("voice.mp3", autoplay=True)
        
        # (3) 商业模式专属福利：显示图表
        # 只有在选"商业策划"时，才显示那些复杂的图表，写情书时不需要！
        if app_mode == "💼 商业策划案":
            st.divider()
            st.subheader("📊 商业数据模型")
            
            # 简单的模拟数据
            data = [100, 150, 230, 350, 500]
            df = pd.DataFrame(data, columns=["预估营收(万)"])
            st.area_chart(df)
            
            # 雷达图
            fig = go.Figure(go.Scatterpolar(
                r=[4, 5, 3, 4, 2], theta=['技术','市场','资金','团队','竞争'], fill='toself'[4, 5, 3, 4, 2], theta=['技术','市场','资金','团队','竞争'], fill='toself'
            输入：             ))))
            fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])), showlegend=False)update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)plotly_chart(fig, use_container_width=True)

    except Exception as e:except Exception as e:
        st.error(f"出错啦: {e}")error(f"出错啦: {e}")

