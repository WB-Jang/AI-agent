from RADARS.Init_data import DataBundle

def generate_report(data : DataBundle) -> dict:
    
    key_list = ['A : 고정이하 분류여신','A1 : 고정', 'A2 : 회수의문', 'A3 : 추정손실',\
                'B : 총여신', 'C : 고정이하 여신 비율','D : 대손충당금', 'E : 고정이하여신대비 대손충당금 적립 비율']
    A=[data.FXD+data.PYBCK+data.EXPCT,data.FXD_conn+data.PYBCK_conn+data.EXPCT_conn]
    A1=[data.FXD,data.FXD_conn]
    A2=[data.PYBCK,data.PYBCK_conn]
    A3=[data.EXPCT,data.EXPCT_conn]
    B=[data.EAD,data.EAD_conn]
    C=[round(((data.FXD+data.PYBCK+data.EXPCT)/data.EAD)*100,2),round(((data.FXD_conn+data.PYBCK_conn+data.EXPCT_conn)/data.EAD_conn)*100,2)]
    D=[data.LI,data.LI_conn]
    E=[round((data.LI/(data.FXD+data.PYBCK+data.EXPCT))*100,2),round((data.LI_conn/(data.FXD_conn+data.PYBCK_conn+data.EXPCT_conn))*100,2)]
    return {'A : 고정이하 분류여신':A,'A1 : 고정':A1, 'A2 : 회수의문':A2, 'A3 : 추정손실':A3,\
            'B : 총여신':B, 'C : 고정이하 여신 비율':C,\
            'D : 대손충당금':D, 'E : 고정이하여신대비 대손충당금 적립 비율': E}