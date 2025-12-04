import requests
import faiss
import numpy as np
import json, os

# on-premise model을 local host server에 띄워둔 상태에서 진행
# C:\Users\1598505\OneDrive - Standard Chartered Bank\5.Python\jupyter_notebook\2.Script\3.Automation\Report_agent\llama.cpp>llama-server.exe -m "C:/Users/1598505/OneDrive - Standard Chartered Bank/5.Python/AI/0.models/bge-m3-FP16.gguf" --embedding -t 8 -c 4092 -b 2048 -ub 2048 -np 1 -v --host 0.0.0.0 --port 8081
# -b 옵션의 크기를 크게 해야지, 긴 문장도 임베딩이 된다(-ub는 -b와 같은 숫자 사용하면 안전)
# 다른 서버와의 충돌을 위하여 port 8080이 아닌 port 8081을 사용


class faiss_vector_db:
    def __init__(self, save_dir, save_idx ,save_nm):
        self.save_dir = save_dir
        self.save_idx = save_idx
        self.save_nm = save_nm
        self.SERVER = "HTTP://127.0.0.1:8081"
        
    def _embed_text(self, texts):
        """
        llama-server의 /v1/embeddings 엔드포인트를 사용해 bge-m3.gguf 임베딩 진행
        반환 결과 : (N, D) float32 numpy array
        N = chunk나 sentence의 개수
        D = 각 chunk나 sentence를 vector space로 넘길 때에, vector의 차원
        """
        out=[]
        for t in texts:
            vecs = None 
            try:
                r= requests.post(f"{self.SERVER}/v1/embeddings", json={"model": "bge-m3", "input": t}, timeout=45)
                if r.ok and "data" in r.json():
                    vecs= r.json()["data"][0]["embedding"]
                    v = np.array(vecs, dtype=np.float32)
                    v /= (np.linalg.norm(v)+1e-12) # cosine similarity를 사용하기 위해서 정규화 실시
                    out.append(v)
            except Exception:
                pass
        if vecs is None:
            raise RuntimeError(f"embedding API 실패: {t}")
            
        return np.vstack(out).astype("float32")
    
    def _make_index(self, texts): # idx는 "faiss_ip.index"와 같은 형식
        text_embedded = self._embed_text(texts)
        text_ids = np.arange(len(texts),dtype=np.int64)

        dim = text_embedded.shape[1]
        base_index = faiss.IndexFlatIP(dim)
        print("base_index 완성")
        index = faiss.IndexIDMap2(base_index)
        print("index map 완성")
        index.add_with_ids(text_embedded, text_ids)
        print("index_size : ", index.ntotal)


        faiss.write_index(index, os.path.join(self.save_dir, self.save_idx))
        with open(os.path.join(self.save_dir, self.save_nm), "w", encoding="utf-8") as f:
            json.dump({int(i):texts[i] for i in range(len(texts))}, f, ensure_ascii=False, indent=2)

        print("Saved : ", index.ntotal, " vectors")
    
    def _search_db(self, q, k):
        index = faiss.read_index(os.path.join(self.save_dir, self.save_idx))
        with open(os.path.join(self.save_dir,self.save_nm),"r", encoding="utf-8") as f:
            DOCS = {int(k): v for k, v in json.load(f).items()}

            print("loaded_index size : ", index.ntotal)

            # Test
            query = q
            q_emb = self._embed_text([query])
            print("임베딩 된 쿼리 : ",q_emb)
            D, I = index.search(q_emb.astype("float32"), k)
            print(f'--- search results : [선택된 {k}개의 Distance[유사도] : {D}"], [선택된 n개의 Index[문장번호] : {I}"] ---' )

            search_result = []
            for idx, score in zip(I[0], D[0]):
                if idx == -1:
                    continue
                search_result.append((DOCS[idx], float(score)))
            print(search_result)
        return search_result
   




# # 문장 임베딩

# sentences = ['나는 은행의 리스크관리부에서 근무 중이다','내가 좋아하는 음식은 김치찌개다','리스크관리는 은행의 비즈니스 과정에서 발생하는 리스크를 통제하는 업무이다','은행의 리스크업무에는 신용리스크, 시장리스크, 운영리스크, 금리리스크 등이 있다']
# print("문장 수 : ", len(sentences))
# #sentences_ids = np.arange(2,dtype=np.int64)
# sentences_ids = np.arange(len(sentences),dtype=np.int64)
# print("ID map : ", sentences_ids)
# sentences_embedded = _embed_text(sentences)
# print("임베딩 완료된 문장들 : ",sentences_embedded)
# print("임베딩 완료된 문장들 모양 0 : ",sentences_embedded.shape[0])
# print("임베딩 완료된 문장들 모양 1 : ",sentences_embedded.shape[1])

# # faiss index 
# dim = sentences_embedded.shape[1]
# base_index = faiss.IndexFlatIP(dim)
# print("base_index 완성")
# index = faiss.IndexIDMap2(base_index)
# print("index map 완성")
# index.add_with_ids(sentences_embedded, sentences_ids)

# print("index_size : ", index.ntotal)

# # Test
# query = '은행의 리스크 관리에 대해서 궁금해'
# q_emb = _embed_text([query])
# print("임베딩 된 쿼리 : ",q_emb)
# D, I = index.search(q_emb.astype("float32"), k=4)
# print(f'--- search results : [f"선택된 n개의 Distance[유사도] : {D}"], [f"선택된 n개의 Index[문장번호] : {I}"] ---' )

# search_result = []
# for idx, score in zip(I[0], D[0]):
#     if idx == -1:
#         continue
#     search_result.append((sentences[idx], float(score)))
# print(search_result)