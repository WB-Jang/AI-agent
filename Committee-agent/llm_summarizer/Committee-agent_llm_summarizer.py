# LLM summarizer using LangChain
# - Summarize chunks produced by pdf_loader
# - Defaults use ChatOpenAI but accepts any LangChain-compatible LLM
# - Two-stage summarization: per-chunk summary -> aggregate summaries

from typing import List, Dict, Optional
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain


# Default prompts (Korean-friendly as requested). You can replace with English or your own.
DEFAULT_CHUNK_PROMPT = """다음 텍스트를 읽고 간결하게 요약해줘. 핵심 포인트만 3~6줄 내외로 정리해줘.

텍스트:
{text}

요약:
"""

DEFAULT_AGGREGATE_PROMPT = """다음은 여러 조각의 요약입니다. 이를 읽고 전체 문서의 통합 요약을 작성하라.
- 통합 요약은 5~10문장 이내로, 문서의 핵심 결론과 중요한 세부사항을 포함해라.
- 중복은 제거하고 논리적으로 연결되어야 한다.

요약들:
{summaries}

통합 요약:
"""


def summarize_chunks(
    chunks: List[Dict],
    llm: Optional[ChatOpenAI] = None,
    chunk_prompt_template: str = DEFAULT_CHUNK_PROMPT,
    aggregate_prompt_template: str = DEFAULT_AGGREGATE_PROMPT,
    verbose: bool = False,
) -> Dict:
    """
    Summarize a list of chunk dicts produced by load_and_chunk_pdfs.
    - chunks: list of {"text": ..., "metadata": {...}}
    - llm: any LangChain LLM object (default: ChatOpenAI with zero temperature)
    Returns:
      {
        "chunk_summaries": [ {"summary": str, "metadata": {...}}, ... ],
        "final_summary": str
      }

    The function performs:
      1. Summarize each chunk individually.
      2. Aggregate all chunk summaries into a final summary.
    """
    if llm is None:
        llm = ChatOpenAI(temperature=0)

    # Prepare per-chunk chain
    chunk_prompt = PromptTemplate(input_variables=["text"], template=chunk_prompt_template)
    chunk_chain = LLMChain(llm=llm, prompt=chunk_prompt)

    chunk_summaries = []
    for i, c in enumerate(chunks):
        input_text = c["text"]
        # call LLM
        chunk_out = chunk_chain.run({"text": input_text})
        if verbose:
            print(f"[chunk {i}] -> {len(chunk_out)} chars")
        chunk_summaries.append({"summary": chunk_out.strip(), "metadata": c.get("metadata", {})})

    # Aggregate
    aggregate_prompt = PromptTemplate(input_variables=["summaries"], template=aggregate_prompt_template)
    aggregate_chain = LLMChain(llm=llm, prompt=aggregate_prompt)

    joined_summaries = "\n\n".join([f"- {s['summary']}" for s in chunk_summaries])
    final_summary = aggregate_chain.run({"summaries": joined_summaries}).strip()

    return {"chunk_summaries": chunk_summaries, "final_summary": final_summary}