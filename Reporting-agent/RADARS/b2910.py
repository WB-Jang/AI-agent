from RADARS.Init_data import DataBundle

def generate_report(data : DataBundle) -> dict:
    
    key_list = ['A : 연체대출채권','B : 대출채권', 'C : 연체대출채권비율']
    A=[data.DLNQ,data.DLNQ_conn]
    B=[data.EAD,data.EAD_conn]
    C=[round((data.DLNQ/data.EAD)*100,2),round((data.DLNQ_conn/data.EAD_conn)*100,2)]
    return {'A : 연체대출채권':A,'B : 대출채권':B, 'C : 연체대출채권비율':C}