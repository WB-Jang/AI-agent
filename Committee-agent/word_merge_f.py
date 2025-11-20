import os
import pythoncom
import pywintypes
import win32com.client as win32
from win32com.client import constants

INPUT_DIR = r"Z:\\"               # 병합할 파일들
OUTPUT_DIR = r"C:\temp\word_merge_D"       # 결과 저장 폴더 (로컬 권장)
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "merged_strategy_D.docx")

VALID_EXT = (".doc", ".docx")


def safe_clone_style(styles, orig_style, prefix, max_name_len=120):
    """COM 오류를 최대한 회피하면서 스타일을 복제."""
    try:
        orig_name = orig_style.NameLocal
    except pywintypes.com_error:
        return None
    except Exception:
        return None

    new_name = f"{prefix}{orig_name}"
    if len(new_name) > max_name_len:
        new_name = new_name[:max_name_len]

    try:
        # 이미 존재하면 그대로 반환
        try:
            return styles(new_name)
        except pywintypes.com_error:
            pass
        except Exception:
            pass

        # 새 스타일 추가 (Type이 이상하면 Paragraph로 대체)
        stype = getattr(orig_style, "Type", constants.wdStyleTypeParagraph)
        if stype not in (
            constants.wdStyleTypeParagraph,
            constants.wdStyleTypeCharacter,
            constants.wdStyleTypeTable,
            constants.wdStyleTypeList,
        ):
            stype = constants.wdStyleTypeParagraph

        new_style = styles.Add(new_name, stype)

        # Font 일부 속성만 안전하게 복사
        try:
            new_style.Font.Name = orig_style.Font.Name
        except Exception:
            pass
        try:
            new_style.Font.Size = orig_style.Font.Size
        except Exception:
            pass
        try:
            new_style.Font.Bold = orig_style.Font.Bold
        except Exception:
            pass
        try:
            new_style.Font.Italic = orig_style.Font.Italic
        except Exception:
            pass
        try:
            new_style.Font.Color = orig_style.Font.Color
        except Exception:
            pass

        # ParagraphFormat 일부 속성만 안전하게 복사 (줄간격/들여쓰기/정렬 위주)
        try:
            pf = new_style.ParagraphFormat
            opf = orig_style.ParagraphFormat

            try:
                pf.LineSpacingRule = opf.LineSpacingRule
            except Exception:
                pass
            try:
                pf.LineSpacing = opf.LineSpacing
            except Exception:
                pass
            try:
                pf.SpaceBefore = opf.SpaceBefore
            except Exception:
                pass
            try:
                pf.SpaceAfter = opf.SpaceAfter
            except Exception:
                pass
            try:
                pf.FirstLineIndent = opf.FirstLineIndent
            except Exception:
                pass
            try:
                pf.LeftIndent = opf.LeftIndent
            except Exception:
                pass
            try:
                pf.RightIndent = opf.RightIndent
            except Exception:
                pass
            try:
                pf.Alignment = opf.Alignment
            except Exception:
                pass
        except Exception:
            pass

        return new_style
    except pywintypes.com_error:
        return None
    except Exception:
        return None


def rewrite_styles_in_doc(sub_doc, prefix="D2_"):
   styles = sub_doc.Styles
   style_map = {}

   # 1) 우선 본문(main story)만 대상으로 시도
   try:
       main_range = sub_doc.StoryRanges(constants.wdMainTextStory)
       paragraphs = main_range.Paragraphs
   except Exception:
       # 혹시 실패하면 전체 문단으로 fallback
       paragraphs = sub_doc.Paragraphs

   # 2) 문단 개수 안전하게 가져오기
   try:
       para_count = paragraphs.Count
   except pywintypes.com_error:
       print("  - 문단 개수 확인 중 COM 오류 발생, 스타일 재작성 생략")
       return
   except Exception:
       print("  - 문단 개수 확인 중 일반 오류 발생, 스타일 재작성 생략")
       return

   print(f"  - 문단 개수(처리 대상): {para_count}")

   # 3) Enumerator(for para in paragraphs)가 아닌 index 기반 순회
   for i in range(1, para_count + 1):
       try:
           # Paragraphs(i) 접근 자체가 COM 오류를 낼 수 있으므로 try 안에 둠
           para = paragraphs(i)
       except pywintypes.com_error:
           # 문제가 되는 문단은 건너뜀
           # 필요하면 여기서 i를 로그로 찍어도 됨
           # print(f"    - 문단 {i} 접근 중 COM 오류, 건너뜀")
           continue
       except Exception:
           # 기타 예외도 건너뜀
           continue

       # 이하 코드는 기존과 동일한 로직
       try:
           orig_style = para.Style
       except pywintypes.com_error:
           continue
       except Exception:
           continue

       try:
           orig_name = orig_style.NameLocal
       except pywintypes.com_error:
           continue
       except Exception:
           continue

       # 이미 prefix가 붙어 있는 스타일은 건너뜀
       if orig_name.startswith(prefix):
           continue

       if orig_name not in style_map:
           new_style = safe_clone_style(styles, orig_style, prefix)
           if new_style is None:
               # 이 스타일은 그냥 원래대로 유지
               style_map[orig_name] = orig_style
           else:
               style_map[orig_name] = new_style

       try:
           para.Style = style_map[orig_name]
       except pywintypes.com_error:
           # 문제가 되는 문단은 그대로 둠
           continue
       except Exception:
           continue

   print(f"  - 스타일 복제/치환 완료 (사용된 스타일 수: {len(style_map)})")

def safe_get_sub_range(sub_doc):
    # 1) 본문(MainTextStory)만 우선 시도
    try:
        main_story = sub_doc.StoryRanges(constants.wdMainTextStory)
        # Duplicate 안 해주면 StoryRanges 열거 중에 Word가 꼬이는 경우가 있어서 복제본 사용
        return main_story.Duplicate
    except pywintypes.com_error:
        pass
    except Exception:
        pass

    # 2) 안 되면 Content만 사용
    try:
        return sub_doc.Content
    except pywintypes.com_error:
        pass
    except Exception:
        pass

    # 3) 그래도 안 되면 이 문서는 스킵
    return None

def merge_with_strategy_D(input_dir, output_file, insert_page_break=True):
    pythoncom.CoInitialize()
    word = None
    master_doc = None

    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        file_list = sorted(
            f for f in os.listdir(input_dir)
            if f.lower().endswith(VALID_EXT)
        )

        if not file_list:
            print("❌ 병합할 Word 파일이 없습니다.")
            return

        print(f"📂 병합 대상 파일 수: {len(file_list)}개")

        word = win32.gencache.EnsureDispatch("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0

        # 1) 첫 번째 파일을 master로 사용
        first_path = os.path.join(input_dir, file_list[0])
        print(f"⭐ 첫 번째 문서를 master로 엶: {first_path}")
        master_doc = word.Documents.Open(first_path)

        # 2) 나머지 파일들 병합
        for idx, filename in enumerate(file_list[1:], start=2):
            file_path = os.path.join(input_dir, filename)
            print(f"\n[{idx}/{len(file_list)}] 병합 준비: {file_path}")

            sub_doc = None
            try:
                sub_doc = word.Documents.Open(file_path)

                prefix = f"D{idx}_"
                print(f"  - 스타일 prefix: {prefix}")

                # 스타일 prefix 부여 (COM 오류는 내부에서 최대한 무시)
                # rewrite_styles_in_doc(sub_doc, prefix=prefix)

                # master 끝 위치에 포맷 포함해서 붙이기
                try:
                    sub_range = safe_get_sub_range(sub_doc)
                    if sub_range is None:
                        print(f"  ⚠ {filename} 범위 추출 실패 (Range 생성 불가) → 이 파일 건너뜀")
                        continue
                    end_pos = master_doc.Content.End
                    end_range = master_doc.Range(end_pos, end_pos) 
                    end_range.FormattedText = sub_range
                except pywintypes.com_error as e:
                    print(f"  ⚠ {filename} 붙여넣기 중 COM 오류, 이 파일은 건너뜀")
                    print("    └ 에러:", e)
                    continue
                except Exception as e:
                    print(f"  ⚠ {filename} 붙여넣기 중 일반 오류, 이 파일은 건너뜀")
                    print("    └ 에러:", e)
                    continue

                # 마지막 파일이 아니라면 페이지 구분
                if insert_page_break and idx < len(file_list):
                    try:
                        br_pos = master_doc.Content.End
                        br_range = master_doc.Range(br_pos, br_pos)
                        br_range.InsertBreak(constants.wdPageBreak)
                    except Exception:
                        pass

            except pywintypes.com_error as e:
                print(f"  ⚠ {filename} 병합 중 COM 오류, 이 파일은 건너뜀")
                print("    └ 에러:", e)
            finally:
                if sub_doc is not None:
                    try:
                        sub_doc.Close(SaveChanges=False)
                    except Exception:
                        pass

        print(f"\n💾 최종 병합 파일 저장 중: {output_file}")
        master_doc.SaveAs(
            output_file,
            FileFormat=constants.wdFormatXMLDocument
        )
        print("✅ 병합 완료!")

    except pywintypes.com_error as e:
        print("❌ Word 작업 중 COM 오류:", e)

    finally:
        if master_doc is not None:
            try:
                master_doc.Close(SaveChanges=False)
            except Exception:
                pass
        if word is not None:
            try:
                word.Quit()
            except Exception:
                pass

        pythoncom.CoUninitialize()
        print("🧹 Word 인스턴스 및 COM 정리 완료")

def merge_with_strategy_insertfile(input_dir, output_file, insert_page_break=True):
    pythoncom.CoInitialize()
    word = None
    master_doc = None

    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        file_list = sorted(
            f for f in os.listdir(input_dir)
            if f.lower().endswith(VALID_EXT)
        )

        if not file_list:
            print("❌ 병합할 Word 파일이 없습니다.")
            return

        print(f"📂 병합 대상 파일 수: {len(file_list)}개")

        word = win32.gencache.EnsureDispatch("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0

        # 1) 첫 번째 파일을 master로 사용
        first_path = os.path.join(input_dir, file_list[0])
        print(f"⭐ 첫 번째 문서를 master로 엶: {first_path}")
        master_doc = word.Documents.Open(first_path)

        # 2) 나머지 파일들을 InsertFile로 병합 (sub_doc을 아예 열지 않음!)
        for idx, filename in enumerate(file_list[1:], start=2):
            file_path = os.path.join(input_dir, filename)
            print(f"\n[{idx}/{len(file_list)}] InsertFile 병합: {file_path}")

            try:
                # 커서를 문서 끝으로 이동
                word.Selection.EndKey(Unit=constants.wdStory)

                # 필요하면 페이지 구분 먼저
                if insert_page_break and idx <= len(file_list):
                    word.Selection.InsertBreak(constants.wdPageBreak)

                # 파일을 통째로 삽입
                word.Selection.InsertFile(
                    FileName=file_path,
                    ConfirmConversions=False,
                    Link=False,
                    Attachment=False
                )

            except pywintypes.com_error as e:
                print(f"  ⚠ {filename} InsertFile 중 COM 오류, 이 파일은 건너뜀")
                print("    └ 에러:", e)
                continue
            except Exception as e:
                print(f"  ⚠ {filename} InsertFile 중 일반 오류, 이 파일은 건너뜀")
                print("    └ 에러:", e)
                continue

        print(f"\n💾 최종 병합 파일 저장 중: {output_file}")
        master_doc.SaveAs(
            output_file,
            FileFormat=constants.wdFormatXMLDocument
        )
        print("✅ InsertFile 병합 완료!")

    except pywintypes.com_error as e:
        print("❌ Word 작업 중 COM 오류:", e)

    finally:
        if master_doc is not None:
            try:
                master_doc.Close(SaveChanges=False)
            except Exception:
                pass
        if word is not None:
            try:
                word.Quit()
            except Exception:
                pass

        pythoncom.CoUninitialize()
        print("🧹 Word 인스턴스 및 COM 정리 완료")

if __name__ == "__main__":
    #merge_with_strategy_D(INPUT_DIR, OUTPUT_FILE)
    merge_with_strategy_insertfile(INPUT_DIR, OUTPUT_FILE)
