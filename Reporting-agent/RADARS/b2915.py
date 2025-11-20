from RADARS.Init_data import DataBundle

def generate_report(data : DataBundle) -> dict:
    
    key_list = ['A1 : 신용리스크','A2 : 시장리스크', 'A3 : 금리리스크', 'A4 : 운영리스크', 'D : 기본자본']
    A1=[data.CREDIT,data.CREDIT_conn]
    A2=[data.MARKET,data.MARKET_conn]
    A3=[data.INTEREST,data.INTEREST_conn]
    A4=[data.OPERATION,data.OPERATION_conn]
    D=[data.CAPITAL,data.CAPITAL_conn]
    return {'A1 : 신용리스크':A1,'A2 : 시장리스크':A2, 'A3 : 금리리스크':A3, 'A4 : 운영리스크':A4, 'D : 기본자본':D}