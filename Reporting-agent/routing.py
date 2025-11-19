from typing import Literal, Dict, Any
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parser import StrOutputParser
from pydantic import BaseModel, Field
import json

# C:\Report_agent\llama.cpp>llama-server.exe -m "C:/Report_agent/llm/Qwen2.5-VL-7B-Instruct-Q4_K_M.gguf" -t 8 -tb 8 -c 4096 --top-p 0.9 --repeat-penalty 1.15 --host 127.0.0.1 --port 8080

BASE_URL = 'http://127.0.0.1:8080/v1'
llm = ChatOpenAI(
  model="Qwen2.5-VL-7B-Instruct-Q4_K_M",
  api_key="sk-local-any",
  base_url=BASE_URL,
  temperture=0.0
)

class AgentState(BaseModel):
  user_input: str
  selected_tool: Literal['corp_loan','fx5220-1st','fx5220-2nd','fx5260','bok_10days','fss_10days','b2901','b2902','b2903','b2910','b2912','b2913','b2914','b2915','RADARS']|None=None
  result: list[Any]|None=None

tools = ['corp_loan','fx5220-1st','fx5220-2nd','fx5260','bok_10days','fss_10days','b2901','b2902','b2903','b2910','b2912','b2913','b2914','b2915','RADARS']

prompt = ChatPromptTemplate.from_messages([
  ("system","""
  You are AI assistant to help user select proper tool.
  After understanding user`s request, select one key from [Available tools] and provide output only in form of JSON {tool}:'...'. No explanation. Only JSON output
  Available tools = ['corp_loan','fx5220-1st','fx5220-2nd','fx5260', 'bok_10days',fss_10days','RADARS']
  No content, no description, no extra text, no explanation, no code fences, no line breaks.
  """),
  ("human","[질문]\n{user_input}\n\n반드시 다음의 JSON 형식만 출력하세요\n\n{tool}:'...'")
])

class answer_format(BaseModel):
  tool:str|None=Field(default=None, description='proper tool from available tools') #Description을 넣어주기 위한 Field 사용

chain = promt | llm | StrOutputParser()

def route(state:AgentState)->AgentState:
  print('chain 실행 시작')
  print(f'--- user input : {state.user_input} ---')
  print(f'--- type of user input : {type(state.user_input)} ---')

try:
  raw=chain.invoke({"tool": None, "user_input":state.user_input})
  print('chain 실행 성공')
  print(raw)
  tool=json.loads(raw).get("tool","")
  print(f'[llm chain]에서 {tool} 도구를 선택하였습니다')
  if tool in tools:
    state.selected_tool = tool
    print(f'[llm chain]에서 정상적으로 {state.selected_tool} 도구를 선택하였습니다')
  return state
except Exception:
  print('[llm chain] Failure')
  pass
