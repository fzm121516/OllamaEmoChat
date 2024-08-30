 ## 基于开源模型的实时情感交流

这是一个基于 Streamlit 的应用，集成了摄像头实时人脸分析和语音聊天功能。

## 功能  

- **人脸分析**：实时(固定时间间隔)对摄像头中的图像进行人脸分析，包括年龄、性别、种族和情绪检测等。
- **语音输入**：用户可以通过录音进行语音输入，并应用 [`mozilla/DeepSpeech`](https://github.com/whitphx/streamlit-webrtc)将语音转换为文本。

- **聊天功能**：集成 Ollama API(OpenAI API), 将语言输入的文本和检测到的情绪输入给大模型，并生成聊天回复。
- **文本转语音**：使用 ChatTTS 将大模型回复转换为语音，并自动播放。

##  安装部署 

1. 下载并安装 [Ollama](http://ollama.com) ，并下载你想要的模型

2. 下载并部署 [ChatTTS-ui](https://github.com/jianchang512/ChatTTS-ui/) 

3. 下载本仓库

4. 安装依赖库 

   ```bash
   pip install -r requirements.txt
   ```

## 启动

1. 启动 Ollama 本地服务器，在浏览器里输入 http://127.0.0.1:11434 ，看到有一行运行中的文字，确定已运行成功 

2. 启动 ChatTTS-ui，成功后会自动打开 http://127.0.0.1:9966    

3. 通过命令行启动

      ```bash
       Streamlit run main_ollama.py

   
