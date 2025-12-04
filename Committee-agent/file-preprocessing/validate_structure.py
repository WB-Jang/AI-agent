#!/usr/bin/env python3
"""
코드 구조 검증 스크립트 - 의존성 없이 파일 구조만 확인
"""

import ast
import sys

def analyze_python_file(filepath):
    """Python 파일을 AST로 분석하여 구조를 검증"""
    print(f"\n{'='*60}")
    print(f"분석 중: {filepath}")
    print(f"{'='*60}\n")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
        
        # 클래스 찾기
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        print(f"클래스: {classes}")
        
        # 함수 찾기 (최상위 레벨만)
        functions = [node.name for node in tree.body if isinstance(node, ast.FunctionDef)]
        print(f"함수: {functions}")
        
        # import 확인
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend([alias.name for alias in node.names])
            elif isinstance(node, ast.ImportFrom):
                imports.append(f"from {node.module}")
        
        print(f"\nImport 개수: {len(imports)}")
        
        # 통합 확인
        required_classes = ['LocalEmbeddings']
        required_functions = [
            'get_word_files',
            'initialize_models',
            'load_document',
            'parse_document_structure',
            'summarize_tables',
            'build_retriever',
            'save_retriever',
            'load_retriever',
            'test_retrieval',
            'process_folder',
            'main'
        ]
        
        print("\n" + "="*60)
        print("필수 구성 요소 확인")
        print("="*60)
        
        all_good = True
        for cls in required_classes:
            if cls in classes:
                print(f"✓ 클래스 {cls} 존재")
            else:
                print(f"❌ 클래스 {cls} 없음")
                all_good = False
        
        for func in required_functions:
            if func in functions:
                print(f"✓ 함수 {func} 존재")
            else:
                print(f"❌ 함수 {func} 없음")
                all_good = False
        
        # 키워드 확인 (통합된 기능)
        content_lower = content.lower()
        keywords = {
            'faiss': '_faiss.py에서 가져온 기능',
            'word2pdf': 'word2pdf.py에서 가져온 기능',
            'local': '로컬 임베딩 지원',
            'folder': '폴더 처리 기능',
            'batch': '배치 처리'
        }
        
        print("\n" + "="*60)
        print("통합 기능 키워드 확인")
        print("="*60)
        
        for keyword, desc in keywords.items():
            if keyword in content_lower:
                print(f"✓ '{keyword}' 발견 - {desc}")
            else:
                print(f"⚠️  '{keyword}' 없음 - {desc}")
        
        return all_good
        
    except SyntaxError as e:
        print(f"❌ 구문 오류: {e}")
        return False

def main():
    filepath = "word_parsing_new.py"
    
    print("\n" + "="*60)
    print("word_parsing_new.py 구조 검증")
    print("="*60)
    
    result = analyze_python_file(filepath)
    
    print("\n" + "="*60)
    print("검증 결과")
    print("="*60)
    
    if result:
        print("✅ 모든 필수 구성 요소 확인 완료!")
        print("\n통합 내용:")
        print("1. ✓ LocalEmbeddings 클래스 추가 (_faiss.py)")
        print("2. ✓ get_word_files 함수 추가 (word2pdf.py)")
        print("3. ✓ process_folder 함수 추가 (배치 처리)")
        print("4. ✓ main 함수 확장 (다중 모드 지원)")
        return 0
    else:
        print("❌ 일부 구성 요소 누락")
        return 1

if __name__ == "__main__":
    sys.exit(main())
