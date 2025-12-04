#!/usr/bin/env python3
"""
간단한 테스트 스크립트 - word_parsing_new.py의 주요 기능 검증

이 스크립트는 실제 문서나 API 키 없이 기본 import와 함수 시그니처를 확인합니다.
"""

import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """필요한 모든 모듈이 import 되는지 확인"""
    print("=" * 60)
    print("테스트 1: Import 확인")
    print("=" * 60)
    
    try:
        import word_parsing_new
        print("✓ word_parsing_new 모듈 import 성공")
        
        # 주요 클래스 확인
        assert hasattr(word_parsing_new, 'LocalEmbeddings'), "LocalEmbeddings 클래스가 없습니다"
        print("✓ LocalEmbeddings 클래스 존재")
        
        # 주요 함수 확인
        functions = [
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
        
        for func_name in functions:
            assert hasattr(word_parsing_new, func_name), f"{func_name} 함수가 없습니다"
            print(f"✓ {func_name} 함수 존재")
        
        print("\n✅ 모든 import 테스트 통과!\n")
        return True
        
    except ImportError as e:
        print(f"❌ Import 실패: {e}")
        return False
    except AssertionError as e:
        print(f"❌ 검증 실패: {e}")
        return False

def test_configuration():
    """설정값 확인"""
    print("=" * 60)
    print("테스트 2: 설정값 확인")
    print("=" * 60)
    
    try:
        import word_parsing_new as wpn
        
        configs = [
            'DEFAULT_DOC_PATH',
            'DEFAULT_FOLDER_PATH',
            'DB_PATH',
            'DOCSTORE_PATH',
            'EMBEDDING_MODEL_NAME',
            'LLM_MODEL_NAME',
            'USE_LOCAL_EMBEDDING',
            'LOCAL_EMBEDDING_SERVER'
        ]
        
        for config in configs:
            assert hasattr(wpn, config), f"{config} 설정이 없습니다"
            value = getattr(wpn, config)
            print(f"✓ {config} = {value}")
        
        print("\n✅ 모든 설정값 확인 완료!\n")
        return True
        
    except AssertionError as e:
        print(f"❌ 검증 실패: {e}")
        return False

def test_local_embeddings_class():
    """LocalEmbeddings 클래스 구조 확인"""
    print("=" * 60)
    print("테스트 3: LocalEmbeddings 클래스 구조")
    print("=" * 60)
    
    try:
        import word_parsing_new as wpn
        
        # 클래스 메서드 확인
        methods = ['_embed_text', 'embed_documents', 'embed_query']
        
        for method in methods:
            assert hasattr(wpn.LocalEmbeddings, method), f"{method} 메서드가 없습니다"
            print(f"✓ LocalEmbeddings.{method} 메서드 존재")
        
        print("\n✅ LocalEmbeddings 클래스 구조 확인 완료!\n")
        return True
        
    except AssertionError as e:
        print(f"❌ 검증 실패: {e}")
        return False

def test_get_word_files():
    """get_word_files 함수 기본 동작 확인 (빈 폴더)"""
    print("=" * 60)
    print("테스트 4: get_word_files 함수")
    print("=" * 60)
    
    try:
        import word_parsing_new as wpn
        import tempfile
        
        # 임시 디렉토리 생성
        with tempfile.TemporaryDirectory() as tmpdir:
            # 빈 폴더에서 실행
            files = wpn.get_word_files(tmpdir)
            assert files == [], "빈 폴더에서 빈 리스트를 반환해야 합니다"
            print(f"✓ 빈 폴더: {files}")
            
            # 테스트 파일 생성
            test_files = ['test1.docx', 'test2.doc', 'test3.txt', '~$temp.docx']
            for filename in test_files:
                open(os.path.join(tmpdir, filename), 'w').close()
            
            files = wpn.get_word_files(tmpdir)
            expected = ['test1.docx', 'test2.doc']  # txt와 임시 파일 제외
            assert sorted(files) == sorted(expected), f"예상: {expected}, 실제: {files}"
            print(f"✓ 필터링된 파일 목록: {files}")
        
        print("\n✅ get_word_files 함수 테스트 통과!\n")
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """모든 테스트 실행"""
    print("\n" + "=" * 60)
    print("word_parsing_new.py 기능 검증 시작")
    print("=" * 60 + "\n")
    
    tests = [
        test_imports,
        test_configuration,
        test_local_embeddings_class,
        test_get_word_files
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ 예외 발생: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"통과: {passed}/{total}")
    
    if all(results):
        print("\n✅ 모든 테스트 통과!")
        return 0
    else:
        print("\n❌ 일부 테스트 실패")
        return 1

if __name__ == "__main__":
    sys.exit(main())
