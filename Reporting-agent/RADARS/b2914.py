from RADARS.Init_data import DataBundle

def generate_report(data : DataBundle) -> dict:
    
    key_list = ['A : Credit VaR','B : 예상손실', 'C : 총여신', 'D : 기본자본', 'E : 자기자본']
    A=[data.CREDIT,data.CREDIT_conn]
    B=[data.EAD*(data.PD/100)*data.LGD_adj,data.EAD_conn*(data.PD_conn/100)*data.LGD_adj_conn]
    C=[data.EAD,data.EAD_conn]
    D=[data.CAPITAL,data.CAPITAL_conn]
    E=[data.CAPITAL+data.CAPITAL_COMP,data.CAPITAL_conn+data.CAPITAL_COMP_conn]
    return {'A : Credit VaR':A,'B : 예상손실':B, 'C : 총여신':C,'D : 기본자본':D, 'E : 자기자본':E}