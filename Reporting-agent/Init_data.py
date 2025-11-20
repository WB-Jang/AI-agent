import pandas as pd
from dataclasses import dataclass

@dataclass
class DataBundle:
    LGD : float
    EAD : float
    EAD_conn : float
    EL : float
    EL_conn : float
    LGD_adj : float
    LGD_adj_conn : float
    PD : float
    PD_conn : float
    LI : float
    LI_conn : float
    FXD : float
    FXD_conn : float
    PYBCK : float
    PYBCK_conn : float
    EXPCT : float
    EXPCT_conn : float
    CAPITAL : float
    CAPITAL_conn : float
    CAPITAL_COMP : float
    CAPITAL_COMP_conn : float
    DLNQ : float
    DLNQ_conn : float
    BORROWER : float
    GROUP : float
    INDUSTRY : float
    COLLATERAL : float
    _SUM : float
    CREDIT : float
    CREDIT_conn : float
    MARKET : float
    MARKET_conn : float
    OPERATION : float
    OPERATION_conn : float
    INTEREST : float
    INTEREST_conn : float
    PROFIT_AF_TAX : float
    PROFIT_AF_TAX_conn : float
    RISK_LIMIT : float
    _etc : float

def prepare_data() -> DataBundle:

    path = input('RADARS raw_data 경로를 입력하세요 : ')
    file = input('RADARS raw_data 파일명을 /file_name.csv와 같이 입력하세요 : ')
    
    df=pd.read_csv(path+file,sep=',')
        
    LGD=float(df.iloc[0,2])
    EAD=float(df.iloc[6,2].replace(',','').strip())
    EAD_conn=float(df.iloc[6,3].replace(',','').strip())
    EL=(float(df.iloc[1,2].replace(',','').strip())+float(df.iloc[4,2].replace(',','').strip()))-(float(df.iloc[8,3].replace(',','').strip())-float(df.iloc[8,2].replace(',','').strip()))
    EL_conn=float(df.iloc[1,2].replace(',','').strip())+float(df.iloc[4,2].replace(',','').strip())
    
    PD=round((EL/(EAD*LGD))*100,2)
    PD_conn=round((EL_conn/(EAD*LGD))*100,2)
    LGD_adj=round(EL/(PD/100*EAD),4)
    LGD_adj_conn=round(EL_conn/(PD_conn/100*EAD_conn),4)
    LI=float(df.iloc[8,2].replace(',','').strip())
    LI_conn=float(df.iloc[8,3].replace(',','').strip())

    FXD=float(df.iloc[16,2].replace(',','').strip())
    FXD_conn=float(df.iloc[16,3].replace(',','').strip())
    PYBCK=float(df.iloc[17,2].replace(',','').strip())
    PYBCK_conn=float(df.iloc[17,3].replace(',','').strip())
    EXPCT=float(df.iloc[18,2].replace(',','').strip())
    EXPCT_conn=float(df.iloc[18,3].replace(',','').strip())

    CAPITAL=float(df.iloc[9,2].replace(',','').strip())
    CAPITAL_conn=float(df.iloc[9,3].replace(',','').strip())

    CAPITAL_COMP=float(df.iloc[10,2].replace(',','').strip())
    CAPITAL_COMP_conn=float(df.iloc[10,3].replace(',','').strip())

    DLQN=float(df.iloc[15,2].replace(',','').strip())
    DLQN_conn=float(df.iloc[15,3].replace(',','').strip())

    BORROWER=float(df.iloc[20,2].replace(',','').strip())
    GROUP=float(df.iloc[20,3].replace(',','').strip())
    INDUSTRY=float(df.iloc[20,4].replace(',','').strip())
    COLLATERAL=float(df.iloc[20,5].replace(',','').strip())
    _SUM=float(df.iloc[20,6].replace(',','').strip())

    CREDIT=float(df.iloc[7,2].replace(',','').strip())
    CREDIT_conn=float(df.iloc[7,3].replace(',','').strip())
    MARKET=float(df.iloc[11,2].replace(',','').strip())
    MARKET_conn=float(df.iloc[11,3].replace(',','').strip())
    OPERATION=float(df.iloc[12,2].replace(',','').strip())
    OPERATION_conn=float(df.iloc[12,3].replace(',','').strip())
    INTEREST=float(df.iloc[13,2].replace(',','').strip())
    INTEREST_conn=float(df.iloc[13,3].replace(',','').strip())

    PROFIT_AF_TAX=float(df.iloc[14,2].replace(',','').strip())
    PROFIT_AF_TAX_conn=float(df.iloc[14,3].replace(',','').strip())

    RISK_LIMIT=float(df.iloc[2,2].replace(',','').strip())
    _etc=float(df.iloc[3,2].replace(',','').strip())


    return DataBundle(LGD=LGD, EAD=EAD, EAD_conn=EAD_conn, EL=EL, EL_conn=EL_conn, PD=PD, PD_conn=PD_conn, LI=LI, LI_conn=LI_conn,\
                      FXD=FXD, FXD_conn=FXD_conn, PYBCK=PYBCK, PYBCK_conn=PYBCK_conn, EXPCT=EXPCT, EXPCT_conn=EXPCT_conn, CAPITAL=CAPITAL, CAPITAL_conn=CAPITAL_conn, CAPITAL_COMP=CAPITAL_COMP, CAPITAL_COMP_conn=CAPITAL_COMP_conn,\
                      DLNQ=DLQN, DLNQ_conn=DLQN_conn, BORROWER=BORROWER, GROUP=GROUP, INDUSTRY=INDUSTRY, COLLATERAL=COLLATERAL, _SUM=_SUM,\
                      CREDIT=CREDIT, CREDIT_conn=CREDIT_conn, MARKET=MARKET, MARKET_conn=MARKET_conn, OPERATION=OPERATION, OPERATION_conn=OPERATION_conn,\
                      INTEREST=INTEREST, INTEREST_conn=INTEREST_conn, PROFIT_AF_TAX=PROFIT_AF_TAX, PROFIT_AF_TAX_conn=PROFIT_AF_TAX_conn, RISK_LIMIT=RISK_LIMIT,_etc=_etc,\
                        LGD_adj=LGD_adj, LGD_adj_conn=LGD_adj_conn)