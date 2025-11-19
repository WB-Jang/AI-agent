from __future__ import annotations
from typing import Literal, Dict, Any
from pydantic import BaseModel
from functools import lru_cache

import json

from langgchain.graph import StateGraph, START, END
from routing import route, AgentState

from RADARS import prepare_data, B2901, B2902, B2903, B2910, B2912, B2913, B2914, B2915
from FX_REPORT import fx5220first, fx5220second, fx5260
from BOK_FSS_10DAYS.BOK_DLNQ_10DAYS import generate_report as bok_10days
from BOK_FSS_10DAYS.FSS_DLNQ_10DAYS import generate_report as fss_10days
from CORP_LOAN.CORP_LOAN import generate_report as corp_loan 

TOOL_REGISTRTY = {
    'fx5220-1st':fx5220first,
    'fx5220-2nd':fx5220second,
    'bok_10days':bok_10days,
    'fss_10days':fss_10days,
    'fx5260':fx5260,
    'corp_loan':corp_loan,
    'b2901':[B2901],
    'b2902':[B2902],
    'b2903':[B2903],
    'b2910':[B2910],
    'b2912':[B2912],
    'b2913':[B2913],
    'b2914':[B2914],
    'b2915':[B2915],
    'RADARS':[B2901,B2902,B2903,B2910,B2911,B2912,B2913,B2914,B2915]
}

def __operating_tools(state:AgentState)->AgentState:
    print(f'---LangGraph AgentState: {state}---')
    print(f'---LangGraph AgentState[selected_tool]: {state.selected_tool}---')

    tool = state.selected_tool
    print(f'---Reporting Agent가 {tool} tool 사용을 시작합니다---')

    if 'fx5220-1st' in tool or 'fx5220-2nd' in tool or 'fx5260' in tool:
        func = TOOL_REGISTRTY[tool]
        result = func()
        print(result)
        return result
    elif 'bok_10days' in tool or 'fss_10days' in tool:
        func = TOOL_REGISTRTY[tool]
        result = func()
        print('보고서 작성 완료')
    elif 'corp' in tool:
        func = TOOL_REGISTRTY[tool]
        result = func()
        print('보고서 작성 완료')
    else:
        data = prepare_data()
        for func in TOOL_REGISTRTY[tool]:
            rpt_nm, result =func(data)
            print(f'---{rpt_nm} 보고서---')
            print(result)
        return result

tool_use_builder = StateGraph(AgentState)
tool_use_builder.add_node('router', route)
tool_use_builder.add_node('operating_tools', __operating_tools)

tool_use_builder.add_edge(START, 'router')
tool_use_builder.add_edge('router', 'operating_tools')
tool_use_builder.add_edge('operating_tools', END)

tool_use_agent = tool_use_builder.compile()

if __name__=='__main__':
    input = input('요청을 입력해주세요 : ')
    req = {'user input': input}
    print(req)
    tool_use_agent.invoke(req)
