import time
import cv2
import numpy as np
from PIL import Image
import tempfile
import os
import streamlit as st
from deepface import DeepFace
import openai
import requests
import random
import streamlit as st
from streamlit_mic_recorder import speech_to_text
import ollama as ol
import mysql.connector
import mysql.connector
from datetime import datetime


def create_table_if_not_exists():
    connection = get_db_connection()
    cursor = connection.cursor()
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS chat_history (
        id INT AUTO_INCREMENT PRIMARY KEY,
        emotion VARCHAR(50),
        question TEXT,
        answer TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    );
    """
    cursor.execute(create_table_sql)
    connection.commit()
    cursor.close()
    connection.close()


def get_db_connection():
    connection = mysql.connector.connect(
        host="localhost",  # MySQL 服务器地址
        port=3306,  # MySQL 端口号
        user="root",  # MySQL 用户名
        password="123456",  # MySQL 密码
        database="ollamaemochat"  # 数据库名称
    )
    return connection


def save_to_database(emotion, question, answer, timestamp=None):
    connection = get_db_connection()
    cursor = connection.cursor()
    if timestamp is None:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sql = "INSERT INTO chat_history (emotion, question, answer, created_at) VALUES (%s, %s, %s, %s)"
    values = (emotion, question, answer, timestamp)
    cursor.execute(sql, values)
    connection.commit()
    cursor.close()
    connection.close()


# 录音功能
def record_voice(language="zh"):
    state = st.session_state
    if "text_received" not in state:
        state.text_received = []

    text = speech_to_text(
        start_prompt="Click to speak",
        stop_prompt="Stop recording",
        language=language,
        use_container_width=True,
        just_once=True,
    )

    if text:
        state.text_received.append(text)

    result = ""
    for text in state.text_received:
        result += text

    state.text_received = []

    return result if result else None


# 打印聊天消息
def print_chat_message(message, ChatTTSServer, audio_seed_input, Audio_temp, Top_P, Top_K, Refine_text, is_history):
    text = message["content"]

    if message["role"] == "user":
        with st.chat_message("user", avatar="👤"):
            print_txt(text)
    if message["role"] == "assistant":
        with st.chat_message("assistant", avatar="🤖"):
            print_txt(text)
            cleartext = text

            if not is_history:
                try:
                    res = requests.post(ChatTTSServer, data={
                        "text": cleartext,
                        "prompt": "",
                        "voice": audio_seed_input,
                        "temperature": Audio_temp,
                        "top_p": Top_P,
                        "top_k": Top_K,
                        "skip_refine": Refine_text,
                        "custom_voice": audio_seed_input,
                        "speed": 5,
                        "refine_max_new_token": 384,
                        "infer_max_new_token": 2048,
                        "text_seed": 42
                    })

                    response_json = res.json()

                    if response_json["code"] == 0:
                        audioURL = response_json["audio_files"][0]["url"]
                        st.audio(audioURL, format="audio/mpeg", autoplay=True, loop=False)
                    else:
                        st.error("生成音频时出错: " + response_json.get("msg", "未知错误"))

                except requests.exceptions.RequestException as e:
                    st.error(f"请求失败: {e}")


# 打印文本内容
def print_txt(text):
    st.write(text)


st.set_page_config(layout="wide")


# 生成随机种子
def generate_seed():
    new_seed = random.randint(1, 100000000)
    st.session_state.Audio_Seed = new_seed


# 生成文本种子
def generate_seed2():
    new_seed = random.randint(1, 100000000)
    st.session_state.Text_Seed = new_seed


# 用户语言选择
def language_selector():
    lang_options = ["ar", "de", "en", "es", "fr", "it", "ja", "nl", "pl", "pt", "ru", "zh"]
    return st.selectbox("语言 Language", ["zh"] + lang_options)


# OpenAI模型选择
def OpenAIModel():
    models = ["llama2-chinese:7b"]
    return st.selectbox("模型 OpenAI Models", models)


# OpenAI服务器设置
def OpenAIServer():
    return st.text_input("OpenAI Server URL", "http://127.0.0.1:11434")


# ChatTTS服务器设置
def ChatTTSServer():
    ChatTTSServer = st.text_input("ChatTTS Server URL", "http://127.0.0.1:9966/tts")
    col1, col2 = st.columns(2)
    with col1:
        audio_seed_input = st.number_input("音色 Audio Seed", value=42, key='Audio_Seed')
        st.button(":game_die: Audio Seed", on_click=generate_seed, use_container_width=True)
        Audio_temp = st.slider('语调 Audio temperature ', min_value=0.01, max_value=1.0, value=0.3, step=0.05, key="Audiotemperature")
        Refine_text = st.checkbox("格式化文本 Refine text", value=True, key='Refine_text')
    with col2:
        text_seed_input = st.number_input("Text Seed", value=42, key='Text_Seed')
        st.button(":game_die: Text Seed", on_click=generate_seed2, use_container_width=True)
        Top_P = st.slider('top_P', min_value=0.1, max_value=0.9, value=0.3, step=0.1, key="top_P")
        Top_K = st.slider('top_K', min_value=1, max_value=20, value=20, step=1, key="top_K")
        TTSServer = ChatTTSServer
    return TTSServer, audio_seed_input, Audio_temp, Top_P, Top_K, Refine_text


def camera_main():
    st.header("Camera Feed")

    # Add custom CSS to make the left column sticky
    st.markdown(
        """
        <style>
        .sticky-col {
            position: -webkit-sticky;
            position: sticky;
            top: 0;
            height: 100vh; /* Full height */
            overflow-y: auto; /* Enable vertical scrolling */
        }
        .scrollable-col {
            overflow-y: auto; /* Enable vertical scrolling */
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Create two columns: left for the camera feed and analysis, right for chat
    col1, col2 = st.columns([1, 3])

    with col1:
        # Apply sticky class
        st.markdown('<div class="sticky-col">', unsafe_allow_html=True)

        # Show camera feed
        video_placeholder = st.empty()
        # Show analysis results
        analysis_placeholder = st.empty()

        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        # Create a scrollable container for the chat section
        st.markdown('<div class="scrollable-col">', unsafe_allow_html=True)

        st.subheader("Chat")

        server = OpenAIServer()
        model = OpenAIModel()
        language = language_selector()

        TTSServer, audio_seed_input, Audio_temp, Top_P, Top_K, Refine_text = ChatTTSServer()

        col1, col2 = st.columns([4, 1])
        with col1:
            text_input = st.text_input('', placeholder="Type here and Enter to send", label_visibility='collapsed', key="text_input_key")
        with col2:
            question = record_voice(language=language)

        with st.container(height=500, border=True):
            if "chat_history" not in st.session_state:
                st.session_state.chat_history = {}
            if model not in st.session_state.chat_history:
                st.session_state.chat_history[model] = []
            chat_history = st.session_state.chat_history[model]
            if len(chat_history) == 0:
                chat_history.append({"role": "system",
                                     "content": "用中文回答，尽量在30字以内。"})

            for message in chat_history:
                print_chat_message(message, TTSServer, st.session_state.Audio_Seed, Audio_temp, Top_P, Top_K, Refine_text, is_history=True)
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

                # Add DeepFace emotion analysis result to user message
                analysis_result = st.session_state.get('last_deepface_analysis', None)
                if analysis_result:
                    emotion = analysis_result['dominant_emotion']
                    user_message["content"] = f"我当前的情绪是{emotion}，请给出对应我情绪的回答。" + user_message["content"]
                else:
                    emotion = "未检测到情绪"

                # 获取当前时间戳
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                print_chat_message(user_message, TTSServer, st.session_state.Audio_Seed, Audio_temp, Top_P, Top_K, Refine_text, is_history=False)
                chat_history.append(user_message)


                response = ol.chat(model=model, messages=chat_history)
                answer = response['message']['content']
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

                # 保存AI回答到数据库，使用与用户问题相同的时间戳
                save_to_database(emotion, user_message["content"], ai_message["content"], timestamp)

                if len(chat_history) > 20:
                    chat_history = chat_history[-20:]

                st.session_state.chat_history[model] = chat_history

        st.markdown('</div>', unsafe_allow_html=True)

    # Initialize camera
    cap = cv2.VideoCapture(0)

    # Initialize DeepFace analysis status
    if "last_analysis" not in st.session_state:
        st.session_state.last_analysis = time.time() - 100  # Ensure first analysis runs immediately

    while cap.isOpened():
        ret, frame = cap.read()

        if not ret:
            st.error("Failed to capture image from camera.")
            break

        # Convert frame from BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(frame_rgb)

        # Show camera feed
        video_placeholder.image(image, channels="RGB", use_column_width=True)

        # Perform DeepFace analysis every 10 seconds
        if time.time() - st.session_state.last_analysis > 2:  # Analyze every 10 seconds
            st.session_state.last_analysis = time.time()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
                temp_file_path = temp_file.name
                image.save(temp_file_path)

                try:
                    analysis_result = DeepFace.analyze(temp_file_path, actions=['age', 'gender', 'race', 'emotion'], enforce_detection=False)
                    if isinstance(analysis_result, list) and len(analysis_result) > 0:
                        # Get the analysis result for the first face
                        analysis_result = analysis_result[0]
                        st.session_state.last_deepface_analysis = analysis_result

                        # Show analysis results
                        age = analysis_result.get('age', 'N/A')
                        gender = analysis_result.get('dominant_gender', 'N/A')
                        race = analysis_result.get('dominant_race', 'N/A')
                        emotion = analysis_result.get('dominant_emotion', 'N/A')

                        analysis_str = (
                            f"年龄: {age}\n"
                            f"性别: {gender}\n"
                            f"种族: {race}\n"
                            f"情绪: {emotion}\n"
                        )
                        analysis_placeholder.text(analysis_str)
                    else:
                        analysis_placeholder.text("没有检测到人脸。")
                except Exception as e:
                    analysis_placeholder.text(f"分析出错: {e}")

    cap.release()
    cv2.destroyAllWindows()



if __name__ == "__main__":
    create_table_if_not_exists()
    camera_main()
