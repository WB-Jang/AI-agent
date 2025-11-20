from RADARS.Init_data import DataBundle

def generate_report(data : DataBundle) -> dict:
    
    key_list = ['A : 예상손실','A1 : 부도시익스포져', 'A2 : 부도율', 'A3 : 부도시손실율','B : 익스포져대비 예상손실비율', 'C : 대손충당금','D : 예상손실대비 대손충당금 적립비율']
    A=[data.EAD*(data.PD/100)*data.LGD_adj,data.EAD_conn*(data.PD_conn/100)*data.LGD_adj_conn]
    A1=[data.EAD,data.EAD_conn]
    A2=[data.PD,data.PD_conn]
    A3=[round(data.LGD_adj*100,2),round(data.LGD_adj_conn*100,2)]
    B=[round((data.EAD*data.PD*data.LGD)/data.EAD,2),round((data.EAD_conn*data.PD_conn*data.LGD)/data.EAD_conn,2)]
    C=[data.LI,data.LI_conn]
    D=[round((data.LI/(data.EAD*(data.PD/100)*data.LGD_adj))*100,2),round((data.LI_conn/(data.EAD_conn*(data.PD_conn/100)*data.LGD_adj_conn))*100,2)]
    return {'A : 예상손실':A,'A1 : 부도시익스포져':A1, 'A2 : 부도율':A2, 'A3 : 부도시손실율':A3,'B : 익스포져대비 예상손실비율':B, 'C : 대손충당금':C,\
            'D : 예상손실대비 대손충당금 적립비율':D}
