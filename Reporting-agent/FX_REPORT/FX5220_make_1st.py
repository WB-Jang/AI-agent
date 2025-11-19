import pandas as pd 
from datetime import datetime

def generate_report():
  dt = str(input('날짜를 yyyymm 형식으로 입력해주세요'))
  dt_trans = datetime.strptime(dt, '%Y%m%d')

  path = input('이번 기준년월 파일의 경로를 입력해주세요 : ')
  file = input('이번 기준년월 파일명을 file_name.csv 형식으로 입력해주세요 : ')
  path_file = path + '/' + file

  raw=pd.read_csv(path_file, sep=',', encoding='euc-kr')
  raw_copied=raw.copy()

  bf_file = input('지난 기준년월 rm 파일명을 file_name.csv 형식으로 입력해주세요 : ')
  bf_path_file = path + '/' + bf_file
  bf_raw=pd.read_csv(bf_path_file, sep=',')
  bf_raw_copied=bf_raw[['계좌번호','업종','기업규모','용도','담당자']].copy()

  raw_copied['base_dt'] = dt_trans
  raw_copied['exec_amt'] = raw_copied['exec_amt'].astype('string').str.replace(',','').astype('float')
  raw_copied['pybck_amt'] = raw_copied['pybck_amt'].astype('string').str.replace(',','').astype('float')
  raw_copied['loan_asst_bs_amt'] = raw_copied['loan_asst_bs_amt'].astype('string').str.replace(',','').astype('float')

  raw_copied.rename(columns={raw_copied.columns[0] : '계좌번호'}, inplcae=True)
  raw_merged=raw_copied.merge(bf_raw_copied, how='left', on='계좌번호')

  new_condition=raw_merged['exec_amt']>0
  raw_new=raw_merge[new_condition]

  out_file = input('신규 외화여신 파일명을 file_name.csv 형식으로 입력해주세요 : ')
  out_path_file = path + '/' + out_file
  raw_new.to_csv(out_path_file,index=False, encoding='utf-8-sig')
  return raw_new
