from datetime import datetime
from platform import system
import json
import streamlit as st

import os
from openai import OpenAI

system_prompt="你是%s，是我的助手，是我漂泊的终点,性格是%s"


def save_session():
    if st.session_state.current_session:
        # 新的会话对象
        session_data = {
            "current_session": st.session_state.current_session,
            "character": st.session_state.character,
            "nick_name": st.session_state.nick_name,
            "messages": st.session_state.messages,
        }
        if not os.path.exists("sessions"):
            os.mkdir("sessions")
        # 保存会话数据
        with open("sessions/" + st.session_state.current_session + ".json", "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)

def creat_new_session():
    st.session_state.messages = []

    data = datetime.now().strftime("%Y%m%d_%H%M%S")

    st.session_state.current_session = data

    save_session()

    st.rerun()

#加载所有会话
def load_session():
    session_list = []

    if os.path.exists("sessions"):
        flie_list= os.listdir("sessions")
        for filename in flie_list:
            if filename.endswith(".json"):
                session_list.append(filename[0:-5:1])
    session_list.sort(reverse=True)#降序排序
    return session_list

#加载历史会话
def load_HisSession(session_name):
    try:
        if os.path.exists(f"sessions/{session_name}.json"):
            with open("sessions/" + session_name + ".json", "r", encoding="utf-8") as f:
                session_data = json.load(f)
                st.session_state.messages = session_data["messages"]
                st.session_state.nick_name = session_data["nick_name"]
                st.session_state.character = session_data["character"]
                st.session_state.current_session = session_name
    except Exception as e:
            st.error("加载会话失败")

def del_session(session_name):
    try:
        if os.path.exists(f"sessions/{session_name}.json"):
            os.remove(f"sessions/{session_name}.json")
            if session_name==st.session_state.current_session:
                st.session_state.messages = []
                st.session_state.current_session = creat_new_session()
    except Exception as e:
        st.error(e)

st.set_page_config(
    page_title="AI只能聊天伴侣",#上面的标题
    page_icon="😊",#图标
    #网页的图标
    layout="wide",#central居中 ，None
    #控制侧边栏
    initial_sidebar_state="expanded",
    #点击右上角时跳到哪里
    menu_items={
    }
)


st.title("AI智能伴侣")

#初始化聊天信息
if "messages" not in st.session_state:
    st.session_state.messages =[]

if "nick_name" not in st.session_state:
    st.session_state.nick_name = "守岸人"

if "character" not in st.session_state:
    st.session_state.character = "你是守岸人，是我的助手，是我漂泊的终点"

if "current_session" not in st.session_state:
    st.session_state.current_session = datetime.now().strftime("%Y%m%d_%H%M%S")

#侧边栏
# st.sidebar.subheader("AI的性格")
# nick_name=st.sidebar.text_input("昵称")


with st.sidebar:
    st.subheader("AI控制面板")
    if st.button("  新建会话   ",width="stretch",icon="✏"):#stretch铺满整个侧边烂
        # 1保存当前会话
        save_session()

        if st.session_state.messages:
            #2新建新的会话
            creat_new_session()

    st.text("会话历史")
    session_list=load_session()
    for session in session_list:
       col1,col2= st.columns([4,2])
       with col1:
           #三元运算符 让选中的按钮变成高亮

           if st.button(session,width="stretch",key=f"load_{session}",type="primary" if session ==st.session_state.current_session else "secondary"):
                load_HisSession(session)
                st.rerun()
       with col2:
           #删除功能
           if st.button("删",width="stretch",key=f"del_{session}"):
                del_session(session)
                st.rerun()
    st.divider()
    st.subheader("AI信息")

    nick_name=st.text_input("AI昵称")

    if nick_name:
        st.session_state.nick_name=nick_name

    character=st.text_area("自定义性格")

    if character:
        st.session_state.character=character

client = OpenAI(
    api_key='',  # 你的真实密钥
    base_url=""
)




#展示聊天信息
for message in st.session_state.messages:
    if(message["role"] == "user"):
        st.chat_message("user").write(message["content"])
    else:
        st.chat_message("assistant").write(message["content"])

prompt=st.chat_input("说点是什么")

if prompt:#字符串会自动转换为bool 非空字符串都是true
    st.chat_message("user").write(prompt)
    print(f"用户输入的是:{prompt}")

    #保存用户输入的提示词
    st.session_state.messages.append({"role":"user",
                                      "content":prompt})#role用来区分是谁的提示词

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt % (st.session_state.nick_name , st.session_state.character)},
            *st.session_state.messages#先把st.session_state.messages列表里的元素解包成一个个独立的字典，类似于把{"role":"user","content":prompt}这个加到message字典里面,列表里面先是user说的提示词，再是assistant说的，因为列表里会存储用户的对话和AI输出的话（AI的输出在调用模块最下面）解包后就是字典形式，类似滚雪球会话记忆模式，
        ],
        stream=True
    )

#空的容器 占位
    response_message=st.empty()
    full_response =""
    #stream输出

    #遍历response里的数据包
    for chunk in response:
        if chunk.choices[0].delta.content is not None:#dlite里面的content所对应的是AI说出的话，不为空
            content=chunk.choices[0].delta.content
            full_response+=content#拼接数据块
            response_message.chat_message("assistant").write(full_response)

    st.session_state.messages.append({"role":"assistant",
                                      "content":full_response})
    #保存最后一个会话信息
    save_session()
