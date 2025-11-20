from RADARS.Init_data import DataBundle

def generate_report(data : DataBundle) -> dict:
    
    key_list = ['A11 : 신용리스크','A12 : 시장리스크', 'A13 : 운영리스크', 'A21 : 신용편중리스크', 'A22 : 금리리스크', 'A24 : 전략/평판/잔여/기타리스크',\
                'B11 : 기본자본계', 'B12 : 보완자본계', 'B13 : 공제항목 및 기타', 'C1 : 세후 당기순이익','C2 : 대손충당금', 'C3 : 예상손실',\
                'D : 리스크한도']
    A11=[data.CREDIT,data.CREDIT_conn]
    A12=[data.MARKET,data.MARKET_conn]
    A13=[data.OPERATION,data.OPERATION_conn]
    A21=[data._SUM,data._SUM]
    A22=[data.INTEREST,data.INTEREST_conn]
    A24=[data._etc*1000,data._etc*1000]
    B11=[data.CAPITAL,data.CAPITAL_conn]
    B12=[data.CAPITAL_COMP,data.CAPITAL_COMP_conn]
    B13=[0,0]
    C1=[data.PROFIT_AF_TAX,data.PROFIT_AF_TAX_conn]
    C2=[data.LI,data.LI_conn]
    C3=[data.EAD*(data.PD/100)*data.LGD_adj,data.EAD_conn*(data.PD_conn/100)*data.LGD_adj_conn]
    D =[data.RISK_LIMIT*1000, data.RISK_LIMIT*1000]
    return {'A11 : 신용리스크':A11,'A12 : 시장리스크':A12, 'A13 : 운영리스크':A13,\
            'A21 : 신용편중리스크':A21, 'A22 : 금리리스크':A22, 'A24 : 전략/평판/잔여/기타리스크':A24,\
            'B11 : 기본자본계':B11, 'B12 : 보완자본계':B12, 'B13 : 공제항목 및 기타':B13,\
            'C1 : 세후 당기순이익':C1, 'C2 : 대손충당금':C2, 'C3 : 예상손실': C3, 'D : 리스크한도': D}