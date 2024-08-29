import random  # 导入随机数生成模块
from streamlit_mic_recorder import speech_to_text  # 导入语音转文本模块
import ollama as ol  # 导入Ollama库

import requests  # 导入HTTP请求模块
import streamlit as st  # 导入Streamlit库，用于构建Web应用


# 打印聊天消息
def print_chat_message(message, ChatTTSServer, audio_seed_input, Audio_temp, Top_P, Top_K, Refine_text, is_history):
    text = message["content"]  # 获取消息内容

    if message["role"] == "user":  # 如果消息角色是用户
        with st.chat_message("user", avatar="😊"):  # 显示用户消息
            print_txt(text)
    if message["role"] == "assistant":  # 如果消息角色是助手
        with st.chat_message("assistant", avatar="🤖"):  # 显示助手消息
            print_txt(text)
            cleartext = text

            if not is_history:  # 仅当不是历史记录时，才执行请求
                try:
                    res = requests.post(ChatTTSServer, data={  # 向ChatTTS服务器发送POST请求
                        "text": cleartext,
                        "prompt": "[break_6]",  # 该字段可调整或删除（如果不需要）
                        "voice": audio_seed_input,
                        "temperature": Audio_temp,
                        "top_p": Top_P,
                        "top_k": Top_K,
                        "skip_refine": Refine_text,
                        "custom_voice": audio_seed_input,
                        "speed": 5,  # 这是一个可选参数；根据需要调整
                        "refine_max_new_token": 384,  # 可选参数；根据需要调整
                        "infer_max_new_token": 2048,  # 可选参数；根据需要调整
                        "text_seed": 42  # 可选参数；根据需要调整
                    })

                    response_json = res.json()  # 解析响应的JSON数据

                    if response_json["code"] == 0:  # 检查响应是否成功
                        audioURL = response_json["audio_files"][0]["url"]  # 获取音频文件的URL
                        st.audio(audioURL, format="audio/mpeg", autoplay=True, loop=False)  # 播放音频
                    else:
                        st.error("生成音频时出错: " + response_json.get("msg", "未知错误"))  # 显示错误消息

                except requests.exceptions.RequestException as e:
                    st.error(f"请求失败: {e}")  # 显示请求失败的错误信息


# 打印文本内容
def print_txt(text):
    st.write(text)  # 使用Streamlit显示文本


st.header(':rainbow[:speech_balloon: Ollama V-Chat]')  # 设置页面标题

# 创建多个选项卡
tab_chat, tab_ChatTTS, tab_setup = st.tabs(
    ["Chat", "ChatTTS Setup", "Ollama Setup"]
)


# 录音功能
def record_voice(language="zh"):
    state = st.session_state  # 获取Streamlit会话状态
    if "text_received" not in state:
        state.text_received = []  # 初始化接收到的文本列表

    text = speech_to_text(  # 调用语音转文本函数
        start_prompt="Click to speak",  # 录音开始提示
        stop_prompt="Stop recording",  # 录音停止提示
        language=language,  # 语言选项
        use_container_width=True,
        just_once=True,
    )

    if text:
        state.text_received.append(text)  # 添加接收到的文本

    result = ""
    for text in state.text_received:  # 拼接所有接收到的文本
        result += text

    state.text_received = []  # 清空接收到的文本列表

    return result if result else None  # 返回拼接后的文本，如果没有文本则返回None


# 生成随机种子
def generate_seed():
    new_seed = random.randint(1, 100000000)  # 生成一个随机种子
    st.session_state.Audio_Seed = new_seed  # 保存种子到会话状态


# 生成文本种子
def generate_seed2():
    new_seed = random.randint(1, 100000000)  # 生成一个随机种子
    st.session_state.Text_Seed = new_seed  # 保存种子到会话状态


# 用户语言选择
def language_selector():
    lang_options = ["ar", "de", "en", "es", "fr", "it", "ja", "nl", "pl", "pt", "ru", "zh"]  # 语言选项列表
    with tab_setup:
        return st.selectbox("语言 Language", ["zh"] + lang_options)  # 创建语言选择框


# Ollama模型选择
def OllamaModel():
    ollama_models = [m['name'] for m in ol.list()['models']]  # 获取Ollama模型列表
    with tab_setup:
        return st.selectbox("模型 Ollama Models", ollama_models)  # 创建模型选择框


# Ollama服务器设置
def OllamaServer():
    OllamaServer = st.text_input("Ollama Server URL", "http://127.0.0.1:11434")  # 创建Ollama服务器URL输入框


# ChatTTS服务器设置
def ChatTTSServer():
    # st.subheader("ChatTTS Setup")
    ChatTTSServer = st.text_input("ChatTTS Server URL", "http://127.0.0.1:9966/tts")  # 创建ChatTTS服务器URL输入框
    col1, col2 = st.columns(2)  # 创建两个列布局
    with col1:
        audio_seed_input = st.number_input("音色 Audio Seed", value=42, key='Audio_Seed')  # 创建音色种子输入框
        st.button(":game_die: Audio Seed", on_click=generate_seed, use_container_width=True)  # 创建生成音色种子的按钮
        Audio_temp = st.slider('语调 Audio temperature ', min_value=0.01, max_value=1.0, value=0.3, step=0.05, key="Audiotemperature")  # 创建音调滑块
        # speed_input = st.slider(label="语速 Speed", min_value=1, max_value=10, value=5, step=1)  # 创建语速滑块（已注释）
        oral_input = st.slider(label="口语化 Oral", min_value=0, max_value=9, value=2, step=1)  # 创建口语化滑块
        laugh_input = st.slider(label="笑声 Laugh", min_value=0, max_value=2, value=0, step=1)  # 创建笑声滑块
        Refine_text = st.checkbox("格式化文本 Refine text", value=True, key='Refine_text')  # 创建格式化文本的复选框
    with col2:
        text_seed_input = st.number_input("Text Seed", value=42, key='Text_Seed')  # 创建文本种子输入框
        st.button(":game_die: Text Seed", on_click=generate_seed2, use_container_width=True)  # 创建生成文本种子的按钮
        Top_P = st.slider('top_P', min_value=0.1, max_value=0.9, value=0.3, step=0.1, key="top_P")  # 创建top_P滑块
        Top_K = st.slider('top_K', min_value=1, max_value=20, value=20, step=1, key="top_K")  # 创建top_K滑块
        bk_input = st.slider(label="停顿 Break", min_value=0, max_value=7, value=4, step=1)  # 创建停顿滑块
        TTSServer = ChatTTSServer
    return TTSServer, audio_seed_input, Audio_temp, Top_P, Top_K, Refine_text


# 主函数
def main():
    with tab_setup:
        server = OllamaServer()  # 获取Ollama服务器URL
        model = OllamaModel()  # 获取Ollama模型
        language = language_selector()  # 获取用户选择的语言

    with tab_ChatTTS:
        TTSServer, audio_seed_input, Audio_temp, Top_P, Top_K, Refine_text = ChatTTSServer()  # 获取ChatTTS服务器配置

    with tab_chat:
        col1, col2 = st.columns([4, 1])  # 创建两列布局
        with col1:
            # 用户输入文本
            text_input = st.text_input('', placeholder="Type here and Enter to send", label_visibility='collapsed', key="text_input_key")  # 创建文本输入框

        with col2:
            question = record_voice(language=language)  # 录音并转换为文本

        with st.container(height=500, border=True):  # 创建一个容器来显示聊天记录
            # 初始化聊天历史记录
            if "chat_history" not in st.session_state:
                st.session_state.chat_history = {}
            if model not in st.session_state.chat_history:
                st.session_state.chat_history[model] = []
            chat_history = st.session_state.chat_history[model]
            if len(chat_history) == 0:
                chat_history.append({"role": "system",
                                     "content": "我会用中文简短回答。"})

            # 打印聊天记录
            for message in chat_history:
                print_chat_message(message, TTSServer, st.session_state.Audio_Seed, Audio_temp, Top_P, Top_K, Refine_text, is_history=True)
            # 处理用户的语音或文本输入
            if question or text_input:
                user_message = {
                    "role": "user",
                    "content": question or text_input,
                    "ChatTTSServer": TTSServer,
                    "audio_seed_input": st.session_state.Audio_Seed,
                    "Audio_temp": Audio_temp,
                    "Top_P": Top_P,
                    "Top_K": Top_K,
                    "Refine_text": Refine_text,
                }
                print_chat_message(user_message, TTSServer, st.session_state.Audio_Seed, Audio_temp, Top_P, Top_K, Refine_text, is_history=False)
                chat_history.append(user_message)
                response = ol.chat(model=model, messages=chat_history)  # 调用Ollama模型生成响应
                answer = response['message']['content']  # 获取助手的回答
                ai_message = {
                    "role": "assistant",
                    "content": answer,
                    "ChatTTSServer": TTSServer,
                    "audio_seed_input": st.session_state.Audio_Seed,
                    "Audio_temp": Audio_temp,
                    "Top_P": Top_P,
                    "Top_K": Top_K,
                    "Refine_text": Refine_text,
                }
                print_chat_message(ai_message, TTSServer, st.session_state.Audio_Seed, Audio_temp, Top_P, Top_K, Refine_text, is_history=False)
                chat_history.append(ai_message)

                # 截断聊天记录，保留最多20条消息
                if len(chat_history) > 20:
                    chat_history = chat_history[-20:]

                # 更新聊天历史记录
                st.session_state.chat_history[model] = chat_history


if __name__ == "__main__":
    main()  # 执行主函数
