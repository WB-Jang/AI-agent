import pandas as pd
from datetime import datetime
from pandas.api.types import CategoricalDtype

pd.options.display.float_format="{:,.2f}".format

def generate_report():
  dt = str(input('기준일자를 yyyymmdd 형식으로 입력해주세요 : '))
  dt_trans = datetime.striptime(dt, '%Y%m%d')

  path = input('이번 기준년월 파일의 경로를 입력해주세요 : ')
  file = input('이번 기준년월 파일명을 file_name.csv 형식으로 입력해주세요 : ')
  path_file = path + '/' + file

  raw = pd.read_csv(path_file, sep=',', encoding = 'euc-kr')
  raw_copied = raw.copy()
  raw_copied.rename(columns={raw_copied.columns[0], '계좌번호'}, inplace = True)

  bf_file = input('지난 기준년월 rm 파일명을 file_name.csv 형식으로 입력해주세요 : ')
  bf_path_file = path + '/' + bf_file
  bf_raw = pd.read_csv(bf_path_file, sep = ',' , encoding = 'euc-kr')
  bf_raw_copied = bf_raw[['계좌번호','업종','기업규모','용도','담당자']].copy()

  new_file = input('이번 기준년월 신규 외화 여신 회신 받은 파일명을 file_name.csv 형식으로 입력해주세요 : ')
  new_path_file = path + '/' + new_file
  new_raw_response = pd.read_csv(new_path_file, sep=',', encoding='euc-kr')
  new_raw_response_copied = new_raw_response.copy()
  for i in range(len(new_raw_response_copied)):
    if new_raw_response_copied.loc[i,'업종'] is None: #str 타입에는 is None, DataFrame에는 .isnull()로 사용함
      new_raw_response_copied.loc[i,'업종']='비제조업'
      new_raw_response_copied.loc[i,'기업규모']='중소기업'
      new_raw_response_copied.loc[i,'용도']='해외사용운전자금'
      new_raw_response_copied.loc[i,'담당자']='오성진'
  
  raw_merged = raw_copied.merge(bf_raw_copied,how='left',on='계좌번호')

  null_condition = raw_merged['담당자'].isnull()
  rm_info = pd.concat([raw_merged[~null_condition],new_raw_response_copied.drop(['base_dt'],axis=1)], axis=0)

  out_file = input('새롭게 생성할 rm_info 파일명을 file_name.csv 형식으로 입력해주세요 : ')
  out_path_file = path + '/' + out_file
  rm_info.to_csv(out_path_file, index=False, encoding='utf-8-sig')

  file_list = [raw_merged,new_raw_response_copied]
  for file in file_list:
    file['exec_amt'] = file['exec_amt'].astype('string').str.replace(',','').astype('float')
    file['실행금액(US)'] = file['실행금액(US)'].astype('string').str.replace(',','').astype('float')
    file['pybck_amt'] = file['pybck_amt'].astype('string').str.replace(',','').astype('float')
    file['회수금액(US)'] = file['회수금액(US)'].astype('string').str.replace(',','').astype('float')
    file['loan_asst_bs_amt'] = file['loan_asst_bs_amt'].astype('string').str.replace(',','').astype('float')
    file['잔액(US)'] = file['잔액(US)'].astype('string').str.replace(',','').astype('float')

    file['loan_deadln_dt'] = file['loan_deadln_dt'].astype('string').str.replace('-','')
    file['loan_deadln_dt'] = pd.to_datetime(file['loan_deadln_dt'],format='%Y%m%d')
    file['new_start_dt'] = file['new_start_dt'].astype('string').str.replace('-','')
    file['new_start_dt'] = pd.to_datetime(file['new_start_dt'],format='%Y%m%d')

    file['maturity1'] = file['loan_deadln_dt']-file['new_start_dt']
    file['maturity2'] = file['loan_deadln_dt']-dt_trans

    file['maturity1_gb'] = 0
    for i in range(len(file['maturity1'])):
      if file.loc[i,'maturity2'].days<91:
        file.loc[i,'maturity1_gb']=1
      elif file.loc[i,'maturity2'].days<186:
        file.loc[i,'maturity1_gb']=2
      elif file.loc[i,'maturity2'].days<371:
        file.loc[i,'maturity1_gb']=3
      elif file.loc[i,'maturity2'].days<741:
        file.loc[i,'maturity1_gb']=4
      else:
        file.loc[i,'maturity1_gb']=5
  
  new_raw_response_copied_v2=new_raw_response_copied.drop(['base_dt'],axis=1)
  raw_merged_new=pd.concat([raw_merged[~null_condition],new_raw_response_copied_v2],axis=0)

  seg_order = ['대기업','중소기업']
  indu_order = ['제조업','비제조업']

  raw_merged_new_v2 = raw_merged_new[['maturity1_gb','maturity2_gb','crncy_cd','실행금액(US)','기업규모','업종','용도','회수금액(US)','잔액(US)']]

  raw_merged_new_v2['기업규모'] = raw_merged_new_v2['기업규모'].astype(CategoricalDtype(categories=seg_order, ordered=True))
  raw_merged_new_v2['업종'] = raw_merged_new_v2['업종'].astype(CategoricalDtype(categories=indu_order, ordered=True))

  new_condition = raw_merged_new_v2['실행금액(US)']>0
  raw_new = raw_merged_new_v2[new_condition]
  raw_new_pivot_1st = pd.pivot_table(
    raw_new
    ,values='실행금액(US)'
    ,index='crncy_cd'
    ,columns=['기업규모','업종']
    ,aggfunc='sum'
    ,fill_value=0)
  raw_new_pivot_2nd = pd.pivot_table(
    raw_new
    ,values='실행금액(US)'
    ,index='용도'
    ,columns=['기업규모','업종']
    ,aggfunc='sum'
    ,fill_value=0)

  pybck_condition = raw_merged_new_v2['회수금액(US)']>0
  raw_pybck = raw_merged_new_v2[pybck_condition]
  raw_pybck_pivot_1st = pd.pivot_table(
    raw_pybck
    ,values='회수금액(US)'
    ,index='crncy_cd'
    ,columns=['기업규모','업종']
    ,aggfunc='sum'
    ,fill_value=0)
  raw_pybck_pivot_2nd = pd.pivot_table(
    raw_pybck
    ,values='회수금액(US)'
    ,index='용도'
    ,columns=['기업규모','업종']
    ,aggfunc='sum'
    ,fill_value=0)

  raw_merged_pivot_1st = pd.pivot_table(
    raw_merged_new_v2
    ,values='잔액(US)'
    ,index='crncy_cd'
    ,columns=['기업규모','업종']
    ,aggfunc='sum'
    ,fill_value=0)
  raw_merged_pivot_2nd = pd.pivot_table(
    raw_merged_new_v2
    ,values='잔액(US)'
    ,index='용도'
    ,columns=['기업규모','업종']
    ,aggfunc='sum'
    ,fill_value=0)

  raw_mature_pivot_1st = pd.pivot_table(
    raw_merged_new_v2
    ,values='잔액(US)'
    ,index='maturity1_gb'
    ,columns=['기업규모','업종']
    ,aggfunc='sum'
    ,fill_value=0)
  raw_mature_pivot_2nd = pd.pivot_table(
    raw_merged_new_v2
    ,values='잔액(US)'
    ,index='maturity2_gb'
    ,columns=['기업규모','업종']
    ,aggfunc='sum'
    ,fill_value=0)

  print('최종 피벗테이블 결과가 출력됩니다...')
  print('-'*30,'신규통화별','-'*30)
  print(raw_new_pivot_1st)
  print('-'*30,'신규용도별','-'*30)
  print(raw_new_pivot_2nd)
  print('-'*30,'회수통화별','-'*30)
  print(raw_pybck_pivot_1st)
  print('-'*30,'회수용도별','-'*30)
  print(raw_pybck_pivot_2nd)
  print('-'*30,'잔액통화별','-'*30)
  print(raw_merged_pivot_1st)
  print('-'*30,'잔액용도별','-'*30)
  print(raw_merged_pivot_2nd)
  print('-'*30,'잔액최초만기별','-'*30)
  print(raw_maturity_pivot_1st)
  print('-'*30,'잔액잔여만기별','-'*30)
  print(raw_maturity_pivot_2nd)
  print('최종 피벗 테이블을 제출 양식에 복사-붙여넣기 하세요')


    
