import pyaudio
import wave
import requests
import json
import base64
import os
import edge_tts
import asyncio
import pygame
import openai
import uuid  # 用于生成唯一的文件名

#1.录音
#用Pyaudio录制音频(生成wav文件)
def audio_record(rec_time,filename):
    """
    :param rec_time : 音频录制时间
    :param filename : 输出音频文件
    :返回值：在当前目录输出一个音频文件
    """

    CHUNK=1024 #定义数据流块
    FORMAT = pyaudio.paInt16 #16bit编码格式
    CHANNELS = 1 #单声道
    RATE = 16000 #16000采样频率

    #创建一个音频对象
    p = pyaudio.PyAudio()

    #创建音频数据流
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    print('Start recording...')
    frames=list() #空列表用于保存录制的音频流
    #录制音频数据
    for i in range(0,int(RATE/CHUNK*rec_time)):
        data=stream.read(CHUNK)
        frames.append(data)
    #录制完成
    # print(frames)
    #停止数据流
    stream.stop_stream()
    stream.close()
    #关闭pyaudio
    p.terminate()
    print('recording done...')

    #保存音频文件
    with wave.open(filename,'wb') as f:
        f.setnchannels(CHANNELS) #设置音频声道数
        f.setsampwidth(p.get_sample_size(FORMAT)) #以字节为样本返回样本宽度
        f.setframerate(RATE) #设置采样频率
        f.writeframes(b''.join(frames))
        f.close()

#2 获取token

API_KEY = "HfXqZQDtatZttTzRHw08ZYzk"    # 这里请替换为你的API_KEY
SECRET_KEY = "eDmELRfwosUvQgEoIG8G7pIccSApTGmU" # 这里请替换为你的SECRET_KEY
def get_access_token():
    """
    使用 AK，SK 生成鉴权签名（Access Token）
    :return: access_token，或是None(如果错误)
    """
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {"grant_type": "client_credentials", "client_id": API_KEY, "client_secret": SECRET_KEY}
    return str(requests.post(url, params=params).json().get("access_token"))



# 3.上传录音文件
def BaiduYuYin(file_url,token):
    """
    :param file_url: 录音文件路径
    :param token: 获取的access token
    :return: 录音识别出来的文本
    """
    
    
    try:
        RATE='16000'
        FORMAT='wav'
        CUID='rvs7K414cquxm4f62jtasIRi6iNRNXR6'
        DEV_PID='1536' # 普通话，支持简单的英文识别
        
        file_url=file_url
        token=token
        #以字节格式读取文件之后进行编码
        with open(file_url,'rb') as f:
            speech=base64.b64encode(f.read()).decode('utf-8')
        size = os.path.getsize(file_url)# 语音文件的字节数
        headers={'Content-Type':'application/json',
                'Accept':'application/json'} # json格式post上传本地文件
        url='https://vop.baidu.com/server_api'
        data={
            "format":FORMAT,#格式
            "rate":RATE,#取样频率,固定值16000
            "dev_pid":DEV_PID,#语音识别类型
            "speech":speech,#本地语音文件的二进制数据,需要进行base64编码
            "cuid":CUID,#用户唯一标识,用来区分用户 建议填写能区分用户的机器MAC地址或IMEI码,长度为60字符以内。
            "len":size,#语音文件的字节数
            "channel":1,#声道数,仅支持单声道,固定值为1
            "token":token,
        }
        req=requests.request("POST",url,data=json.dumps(data),headers=headers) #request.post 改为requests.request("POST"……)
        data_dict=json.loads(req.text)
        # print(data_dict['result'][0])
        return data_dict['result'][0] # 返回文本
    except:
        return '识别不清楚'



# 4.接入大语言模型
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv()) # read local .env file
os.environ['OPENAI_API_KEY'] = 'EMPTY'
os.environ['OPENAI_API_BASE'] = 'http://localhost:8000/v1'
openai.api_key = 'none'
openai.api_base = 'http://localhost:8000/v1'

def get_completion(prompt, model="gpt-3.5-turbo"):
    """
    :param prompt:输入提示词
    :param model:模型名称(使用默认参数即可)
    :return: 大模型的回复文本
    """
    messages = [{"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=0,
    )
    return response.choices[0].message["content"]


# 5.文本转语音TTS：edge-tts

async def generate_audio_from_text(text,file_url):
    """
    :param text:需要进行转换的文本
    :file_url:转换后输出的音频文件地址
    :return:无
    """
    voice = 'zh-CN-YunxiNeural'
    output = file_url
    rate='-4%'
    volume = '+0%'
    tts = edge_tts.Communicate(text=text,voice=voice,rate=rate,volume=volume)
    await tts.save(output)



# 6.播放音频文件：pygame
def play_mp3(mp3_file): 
    """
    :param mp3_file:需要播放的录音文件地址
    :return:无
    """
    pygame.init()  # 初始化pygame
    pygame.mixer.init() # 初始化音频混合器
    pygame.mixer.music.load(mp3_file) # 加载指定MP3文件
    pygame.mixer.music.play() # 播放
    clock = pygame.time.Clock()
    while pygame.mixer.music.get_busy(): # 使用一个循环来等待音频播放完毕，保证程序不会在播放结束前退出
        clock.tick(3)
        

def main():
    while True:
        # 1. 提示用户发言
        print('请发言，谢谢！')
        # 2. 录制音频
        audio_record(5, 'user_audio.wav')
        print('Audio recording complete.')

        # 3. 获取百度语音识别的access token
        baidu_token = get_access_token()
        print('Baidu access token obtained.')

        # 4. 上传录音文件并进行语音识别
        baidu_result = BaiduYuYin('user_audio.wav', baidu_token)
        print('Baidu speech recognition result:', baidu_result)

        
        # 5. 调用大语言模型进行文本生成
        model_response = get_completion(baidu_result)
        print('Model response:', model_response)

        # 6. 将文本转换为语音,保存到唯一的文件名
        unique_audio_filename = str(uuid.uuid4()) + '.mp3' # 保存为不同的文件名以避免访问冲突
        asyncio.run(generate_audio_from_text(model_response,unique_audio_filename))

        # 7. 播放生成的语音
        play_mp3(unique_audio_filename)

        # 8. 提示用户继续对话或退出
        user_input = input('继续对话或输入"退出"退出: ')
        if user_input == '退出':
            break

if __name__ == "__main__":
    main()




