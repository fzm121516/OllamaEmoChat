import random
import openai
import requests
import streamlit as st
import random
from streamlit_mic_recorder import speech_to_text
import ollama as ol
import requests
import streamlit as st


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
        with st.chat_message("user", avatar="😊"):
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
    models = ["gpt-4", "gpt-3.5-turbo"]
    return st.selectbox("模型 OpenAI Models", models)


# OpenAI服务器设置
def OpenAIServer():
    return st.text_input("OpenAI Server URL", "")


openai.api_key = ""
openai.api_base = ""

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


# 主函数
def main():
    st.header(':rainbow[:speech_balloon: OpenAI V-Chat]')

    with st.container():
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
                                     "content": "我会用中文简短回答。"})

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
                print_chat_message(user_message, TTSServer, st.session_state.Audio_Seed, Audio_temp, Top_P, Top_K, Refine_text, is_history=False)
                chat_history.append(user_message)
                response = openai.ChatCompletion.create(
                    model=model,
                    messages=chat_history,
                    temperature=Audio_temp,
                    top_p=Top_P
                )
                answer = response['choices'][0]['message']['content']
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

                if len(chat_history) > 20:
                    chat_history = chat_history[-20:]

                st.session_state.chat_history[model] = chat_history


if __name__ == "__main__":
    main()
