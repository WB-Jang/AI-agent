import os
from docx2pdf import convert
from pypdf import PdfWriter
import win32com
from win32com.client import gencache
import shutil

# PPT 변환을 위한 상수 (PowerPoint SaveAs PDF format code)
ppSaveAsPDF = 32

def get_word_files(folder_path):
    """폴더 내의 .docx/.doc/.pptx/.ppt 파일 리스트를 반환"""
    extensions = ('.docx', '.doc', '.pptx', '.ppt')
    files = [f for f in os.listdir(folder_path) if f.lower().endswith(extensions) and not f.startswith('~$')]
    return sorted(files) 

def convert_ppt_to_pdf(input_path, output_path):
    """
    win32com을 사용하여 PPT를 PDF로 변환하는 함수
    """
    powerpoint = None
    presentation = None
    try:
        # PowerPoint 어플리케이션 실행 (백그라운드)
        powerpoint = win32com.client.Dispatch("PowerPoint.Application")
        
        # 파일 열기 (WithWindow=False로 창 숨김 시도)
        presentation = powerpoint.Presentations.Open(input_path, WithWindow=False)
        
        # PDF로 저장
        presentation.SaveAs(output_path, FileFormat=ppSaveAsPDF)
        return True
    except Exception as e:
        print(f"[PPT 변환 에러] {e}")
        return False
    finally:
        # 자원 해제
        if presentation:
            presentation.Close()
        if powerpoint:
            # 주의: 다른 PPT 창이 열려있을 수도 있으므로 Quit은 신중 
            # 배치 작업에서는 깔끔하게 종료하는 것이 메모리 효율 좋음
            # 실행 중인 다른 PPT가 있다면 Quit()을 제외하거나 카운트를 체크.
            try:
                if powerpoint.Presentations.Count == 0:
                    powerpoint.Quit()
            except:
                pass

def convert_to_pdf_wrapper(input_path, output_path):
    """파일 확장자에 따라 적절한 변환 도구를 호출하는 래퍼 함수"""
    ext = os.path.splitext(input_path)[1].lower()
    
    if ext in ['.docx', '.doc']:
        # Word는 기존 docx2pdf 사용
        convert(input_path, output_path)
    elif ext in ['.pptx', '.ppt']:
        # PPT는 win32com 사용
        success = convert_ppt_to_pdf(input_path, output_path)
        if not success:
            raise Exception("PowerPoint conversion failed via win32com")
    else:
        raise Exception(f"지원하지 않는 확장자입니다: {ext}")

def convert_each_to_pdf(folder_path, output_path, output_folder=None):
    """
    기능 1: 여러 Word 파일을 각각의 PDF 파일로 저장
    """
    if output_folder is None:
        output_folder = output_path
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    target_files = get_files(folder_path)
    
    print(f"총 {len(target_files)}개의 파일을 개별 PDF로 변환합니다...")
    
    for file in target_files:
        input_path = os.path.join(folder_path, file)
        # 확장자만 .pdf로 변경
        output_filename = os.path.splitext(file)[0] + ".pdf"
        output_path = os.path.join(output_folder, output_filename)
        
        try:
            convert_to_pdf_wrapper(input_path, output_path)
            print(f"[완료] {file} -> {output_filename}")
        except Exception as e:
            print(f"[에러] {file} 변환 실패: {e}")

def convert_and_merge_to_one_pdf(folder_path, output_path, merged_filename="Merged_Result.pdf"):
    """
    기능 2: 여러 Word 파일을 형식 변형 없이 하나의 PDF 파일로 합쳐서 저장
    (전략: 개별 PDF 변환 -> PDF 병합 -> 임시 파일 삭제 옵션)
    """
    target_files = get_files(folder_path)
    merger = PdfWriter()
    temp_pdf_list = []

    print(f"총 {len(target_files)}개의 파일을 하나로 병합하기 위해 변환을 시작합니다...")

    # 1단계: Word -> 개별 PDF 변환 (임시)
    for file in target_files:
        input_path = os.path.join(folder_path, file)
        temp_pdf_name = os.path.splitext(file)[0] + "_temp.pdf"
        temp_pdf_path = os.path.join(output_path, temp_pdf_name)
        
        try:
            # 변환 수행
            convert(input_path, temp_pdf_path)
            temp_pdf_list.append(temp_pdf_path)
            # 병합 리스트에 추가
            merger.append(temp_pdf_path)
            print(f"[변환됨] {file}")
        except Exception as e:
            print(f"[에러] {file} 처리 중 문제 발생: {e}")

    # 2단계: PDF 병합 저장
    output_path = os.path.join(output_path, merged_filename)
    merger.write(output_path)
    merger.close()
    
    print(f"\n[병합 완료] 파일이 저장되었습니다: {output_path}")

    # 3단계: (선택 사항) 병합을 위해 생성했던 임시 개별 PDF 삭제
    # 임시 파일을 남겨두고 싶다면 아래 반복문을 주석 처리하세요.
    for temp_path in temp_pdf_list:
        if os.path.exists(temp_path):
            os.remove(temp_path)
    print("[정리 완료] 임시 PDF 파일들을 삭제했습니다.")

def cleanup_gen_py():
    """win32com gen_py 캐시 폴더 자동 삭제"""
    paths = set()
    gen_attr =getattr(win32com, "__gen_path__", None)
    if gen_attr:
        paths.add(gen_attr)
        try:
            gen_path = gencache.GetGeneratePath()
            if gen_path:
                paths.add(gen_path)
        except Exception:
            pass
    for p in paths:
        if p and os.path.isdir(p):
            try:
                print(f"[cleanup_gen_py] 삭제 시도: {p}")
                shutil.rmtree(p, ignore_errors=True)
            except Exception as e:
                print(f"[cleanup_gen_py] 삭제 실패: {p} -> {e}")
# --- 사용 예시 ---
if __name__ == "__main__":
    # Word 파일들이 들어있는 폴더 경로 (경로를 본인 환경에 맞게 수정하세요)
    
    target_folder = r"Z:\\" #drm-free 폴더 경로
    out_folder = r"C:\\temp" # drm-free 저장 폴더 경로
  

    # 1. 각각의 PDF로 만들기
    print("--- [1] 개별 PDF 변환 시작 ---")
    convert_each_to_pdf(target_folder,out_folder)

    print("\n" + "="*30 + "\n")

    # 2. 하나의 PDF로 합치기
    print("--- [2] 통합 PDF 생성 시작 ---")
    convert_and_merge_to_one_pdf(target_folder, out_folder, "최종보고서_통합.pdf")
    # 3. cache 삭제
    cleanup_gen_py()
    print('====gen_py cache 삭제 완료====')


