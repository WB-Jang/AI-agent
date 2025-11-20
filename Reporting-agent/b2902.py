from RADARS.Init_data import DataBundle

def generate_report(data : DataBundle) -> dict:
    
    key_list = ['A : 손실위험도가중여신','A1 : 고정 분류자산 x 위험가중치', 'A2 : 회수의문 분류자산 x 위험가중치', 'A3 : 추정손실 분류자산 x 위험가중치',\
                'B : 기본자본', 'C : 대손충당금','D : 손실위험도가중여신비율']
    A=[data.FXD*0.2+data.PYBCK*0.5+data.EXPCT*1.0,data.FXD_conn*0.2+data.PYBCK_conn*0.5+data.EXPCT_conn*1.0]
    A1=[data.FXD*0.2,data.FXD_conn*0.2]
    A2=[data.PYBCK*0.5,data.PYBCK_conn*0.5]
    A3=[data.EXPCT*1.0,data.EXPCT_conn*1.0]
    B=[data.CAPITAL,data.CAPITAL_conn]
    C=[data.LI,data.LI_conn]
    D=[round((data.FXD*0.2+data.PYBCK*0.5+data.EXPCT*1.0)/(data.CAPITAL+data.LI)*100,2),\
       round((data.FXD_conn*0.2+data.PYBCK_conn*0.5+data.EXPCT_conn*1.0)/(data.CAPITAL_conn+data.LI_conn)*100,2)]
    return {'A : 손실위험도가중여신':A,'A1 : 고정 분류자산 x 위험가중치':A1, 'A2 : 회수의문 분류자산 x 위험가중치':A2, 'A3 : 추정손실 분류자산 x 위험가중치':A3,\
            'B : 기본자본':B, 'C : 대손충당금':C,\
            'D : 손실위험도가중여신비율':D}