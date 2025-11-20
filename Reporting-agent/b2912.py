from RADARS.Init_data import DataBundle

def generate_report(data : DataBundle) -> dict:
    
    key_list = ['A : 부문별 신용리스크량','B : 기본자본', 'C : 기본자본대비 신용편중리스크량']
    A=[[data.BORROWER,data.GROUP,data.INDUSTRY,data.COLLATERAL,data._SUM],[data.BORROWER,data.GROUP,data.INDUSTRY,data.COLLATERAL,data._SUM]]
    B=[[data.CAPITAL,data.CAPITAL,data.CAPITAL,data.CAPITAL,data.CAPITAL],[data.CAPITAL_conn,data.CAPITAL_conn,data.CAPITAL_conn,data.CAPITAL_conn,data.CAPITAL_conn]]
    C=[[round((data.BORROWER/data.CAPITAL)*100,2),round((data.GROUP/data.CAPITAL)*100,2),round((data.INDUSTRY/data.CAPITAL)*100,2),round((data.COLLATERAL/data.CAPITAL)*100,2),round((data._SUM/data.CAPITAL)*100,2)],\
       [round((data.BORROWER/data.CAPITAL_conn)*100,2),round((data.GROUP/data.CAPITAL_conn)*100,2),round((data.INDUSTRY/data.CAPITAL_conn)*100,2),round((data.COLLATERAL/data.CAPITAL_conn)*100,2),round((data._SUM/data.CAPITAL_conn)*100,2)]]
    return {'A : 부문별 신용리스크량':A,'B : 기본자본':B, 'C : 기본자본대비 신용편중리스크량':C}