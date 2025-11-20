# Text validator using LangChain
# - Detects typos, grammatical errors, logical inconsistencies in text chunks
# - Provides configurable validation prompts
# - Returns structured validation results per chunk and aggregated findings

from typing import List, Dict, Optional
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import json


# Default prompts for validation (Korean)
DEFAULT_TYPO_PROMPT = """다음 텍스트를 꼼꼼히 읽고, 오타와 문법 오류를 모두 찾아줘.

요구사항:
1. 각 오류를 명확하게 지적하고 위치를 표시해줘 (예: "3번째 문장의 '엄청이'는 '엄청'으로 수정해야 함")
2. 오류의 종류를 분류해줘 (예: 오타, 문법 오류, 띄어쓰기 오류 등)
3. 각 오류에 대한 수정안을 제시해줘
4. 만약 오류가 없으면 "오류 없음"이라고 명시해줘

텍스트:
{text}

검증 결과:
"""

DEFAULT_LOGIC_PROMPT = """다음 텍스트를 읽고, 논리적 오류나 일관성 문제가 있는지 판단해줘.

요구사항:
1. 모순되는 표현이나 부자연스러운 논리 흐름을 찾아줘
2. 주어-술어 불일치, 명확하지 않은 지시대상 등을 확인해줘
3. 각 논리적 오류에 대해 "왜" 문제인지 설명해줘
4. 개선 방안을 제시해줘
5. 논리적 오류가 없으면 "논리적 오류 없음"이라고 명시해줘

텍스트:
{text}

논리적 오류 검수 결과:
"""

DEFAULT_AGGREGATE_VALIDATION_PROMPT = """다음은 여러 청크에서 발견된 검증 결과들입니다. 이를 종합하여 전체 문서의 주요 오류와 패턴을 요약해줘.

요구사항:
1. 반복적으로 나타나는 오류 패턴을 식별해줘 (예: 특정 단어의 지속적인 오타)
2. 문서 전체의 논리적 일관성 문제를 정리해줘
3. 우선적으로 수정해야 할 항목을 순서대로 나열해줘
4. 각 섹션별 문제점을 요약해줘

개별 검증 결과들:
{validation_results}

종합 분석:
"""


class TextValidator:
    """
    Validates text chunks for typos and logical errors using LangChain.
    """

    def __init__(
        self,
        llm: Optional[ChatOpenAI] = None,
        typo_prompt_template: str = DEFAULT_TYPO_PROMPT,
        logic_prompt_template: str = DEFAULT_LOGIC_PROMPT,
        aggregate_prompt_template: str = DEFAULT_AGGREGATE_VALIDATION_PROMPT,
    ):
        """
        Initialize the validator with an LLM and prompt templates.

        Args:
            llm: LangChain LLM instance (default: ChatOpenAI with temperature=0)
            typo_prompt_template: Template for typo/grammar validation
            logic_prompt_template: Template for logical error detection
            aggregate_prompt_template: Template for aggregating validation results
        """
        self.llm = llm or ChatOpenAI(temperature=0, model="gpt-4")
        self.typo_prompt_template = typo_prompt_template
        self.logic_prompt_template = logic_prompt_template
        self.aggregate_prompt_template = aggregate_prompt_template

    def validate_typos(self, text: str) -> Dict:
        """
        Detect typos and grammatical errors in the given text.

        Returns:
            {
                "has_typos": bool,
                "typo_findings": str,
                "error_count": int (estimated)
            }
        """
        typo_prompt = PromptTemplate(
            input_variables=["text"], template=self.typo_prompt_template
        )
        typo_chain = LLMChain(llm=self.llm, prompt=typo_prompt)
        result = typo_chain.run({"text": text}).strip()

        has_typos = "오류 없음" not in result
        return {
            "has_typos": has_typos,
            "typo_findings": result,
            "error_count": result.count("\n") if has_typos else 0,
        }

    def validate_logic(self, text: str) -> Dict:
        """
        Detect logical errors and inconsistencies in the given text.

        Returns:
            {
                "has_logic_errors": bool,
                "logic_findings": str,
                "error_count": int (estimated)
            }
        """
        logic_prompt = PromptTemplate(
            input_variables=["text"], template=self.logic_prompt_template
        )
        logic_chain = LLMChain(llm=self.llm, prompt=logic_prompt)
        result = logic_chain.run({"text": text}).strip()

        has_logic_errors = "논리적 오류 없음" not in result
        return {
            "has_logic_errors": has_logic_errors,
            "logic_findings": result,
            "error_count": result.count("\n") if has_logic_errors else 0,
        }

    def validate_chunk(self, chunk: Dict, validate_typos: bool = True, validate_logic: bool = True) -> Dict:
        """
        Fully validate a single chunk (from pdf_loader.py).

        Args:
            chunk: {"text": str, "metadata": {...}}
            validate_typos: Whether to run typo validation
            validate_logic: Whether to run logic validation

        Returns:
            {
                "chunk_index": int,
                "source": str,
                "text": str,
                "typo_validation": {...},
                "logic_validation": {...},
                "is_valid": bool (True if no errors found),
                "severity": "clean" | "warning" | "critical"
            }
        """
        text = chunk.get("text", "")
        metadata = chunk.get("metadata", {})

        typo_result = self.validate_typos(text) if validate_typos else None
        logic_result = self.validate_logic(text) if validate_logic else None

        has_typos = typo_result and typo_result.get("has_typos", False)
        has_logic_errors = logic_result and logic_result.get("has_logic_errors", False)
        is_valid = not (has_typos or has_logic_errors)

        # Determine severity
        if is_valid:
            severity = "clean"
        elif (typo_result and typo_result.get("error_count", 0) > 5) or (
            logic_result and logic_result.get("error_count", 0) > 3
        ):
            severity = "critical"
        else:
            severity = "warning"

        return {
            "chunk_index": metadata.get("chunk_index", -1),
            "source": metadata.get("source", "unknown"),
            "text_preview": text[:100] + "..." if len(text) > 100 else text,
            "typo_validation": typo_result,
            "logic_validation": logic_result,
            "is_valid": is_valid,
            "severity": severity,
            "metadata": metadata,
        }

    def validate_all_chunks(
        self,
        chunks: List[Dict],
        validate_typos: bool = True,
        validate_logic: bool = True,
        verbose: bool = False,
    ) -> Dict:
        """
        Validate all chunks and return aggregated findings.

        Args:
            chunks: List of chunk dicts from pdf_loader.py
            validate_typos: Whether to run typo validation
            validate_logic: Whether to run logic validation
            verbose: Print progress

        Returns:
            {
                "chunk_validations": [...],
                "summary": {
                    "total_chunks": int,
                    "clean_chunks": int,
                    "warning_chunks": int,
                    "critical_chunks": int,
                    "overall_quality_score": float (0.0 to 1.0)
                },
                "aggregate_findings": str
            }
        """
        chunk_validations = []
        for i, chunk in enumerate(chunks):
            if verbose:
                print(f"[Validating chunk {i}/{len(chunks)}]")
            validation = self.validate_chunk(chunk, validate_typos=validate_typos, validate_logic=validate_logic)
            chunk_validations.append(validation)

        # Aggregate findings
        clean_count = sum(1 for v in chunk_validations if v["severity"] == "clean")
        warning_count = sum(1 for v in chunk_validations if v["severity"] == "warning")
        critical_count = sum(1 for v in chunk_validations if v["severity"] == "critical")
        total_count = len(chunk_validations)

        quality_score = clean_count / total_count if total_count > 0 else 0.0

        # Call LLM to aggregate findings
        validation_summaries = "\n\n".join(
            [
                f"청크 {v['chunk_index']} ({v['source']}):\n"
                f"  오타 검수: {v['typo_validation']['typo_findings'] if v['typo_validation'] else 'N/A'}\n"
                f"  논리 검수: {v['logic_validation']['logic_findings'] if v['logic_validation'] else 'N/A'}"
                for v in chunk_validations[:10]  # Limit to first 10 for brevity
            ]
        )

        aggregate_prompt = PromptTemplate(
            input_variables=["validation_results"], template=self.aggregate_prompt_template
        )
        aggregate_chain = LLMChain(llm=self.llm, prompt=aggregate_prompt)
        aggregate_findings = aggregate_chain.run({"validation_results": validation_summaries}).strip()

        return {
            "chunk_validations": chunk_validations,
            "summary": {
                "total_chunks": total_count,
                "clean_chunks": clean_count,
                "warning_chunks": warning_count,
                "critical_chunks": critical_count,
                "overall_quality_score": round(quality_score, 2),
            },
            "aggregate_findings": aggregate_findings,
        }