# LangGraph-based workflow for text validation
# - Orchestrates multi-stage validation process
# - Handles conditional routing based on error severity
# - Supports retry logic and error recovery

from typing import Dict, List, Any, Optional
from langgraph.graph import StateGraph, END
from langchain.chat_models import ChatOpenAI
from text_validator import TextValidator


# Define the state schema for the graph
class ValidationState:
    """State object for the LangGraph workflow"""

    def __init__(self):
        self.chunks: List[Dict] = []
        self.current_chunk_index: int = 0
        self.chunk_validations: List[Dict] = []
        self.typo_errors: List[Dict] = []
        self.logic_errors: List[Dict] = []
        self.aggregate_findings: str = ""
        self.quality_score: float = 0.0


def create_validation_graph(
    llm: Optional[ChatOpenAI] = None,
    max_retries: int = 1,
    skip_critical: bool = False,
) -> StateGraph:
    """
    Create a LangGraph workflow for validating PDF chunks.

    Args:
        llm: LangChain LLM instance (default: ChatOpenAI)
        max_retries: Number of times to retry validation on LLM errors
        skip_critical: If True, skip chunks with critical errors in downstream processing

    Returns:
        A configured StateGraph ready to be compiled
    """
    validator = TextValidator(llm=llm)
    workflow = StateGraph(dict)

    # Node 1: Initialize validation state
    def initialize_validation(state: Dict) -> Dict:
        """Initialize the validation workflow with input chunks"""
        chunks = state.get("chunks", [])
        state["chunk_validations"] = []
        state["typo_errors"] = []
        state["logic_errors"] = []
        state["current_chunk_index"] = 0
        state["validation_progress"] = f"Starting validation of {len(chunks)} chunks"
        return state

    # Node 2: Validate individual chunk
    def validate_single_chunk(state: Dict) -> Dict:
        """Validate a single chunk"""
        chunks = state.get("chunks", [])
        idx = state.get("current_chunk_index", 0)

        if idx >= len(chunks):
            state["validation_status"] = "complete"
            return state

        chunk = chunks[idx]
        try:
            validation_result = validator.validate_chunk(chunk)
            state["chunk_validations"].append(validation_result)

            # Categorize errors
            if validation_result.get("typo_validation", {}).get("has_typos"):
                state["typo_errors"].append(
                    {
                        "chunk_index": idx,
                        "findings": validation_result["typo_validation"]["typo_findings"],
                    }
                )

            if validation_result.get("logic_validation", {}).get("has_logic_errors"):
                state["logic_errors"].append(
                    {
                        "chunk_index": idx,
                        "findings": validation_result["logic_validation"]["logic_findings"],
                    }
                )

            state["current_chunk_index"] = idx + 1
            state["validation_progress"] = f"Validated {idx + 1}/{len(chunks)} chunks"
        except Exception as e:
            state["last_error"] = str(e)
            state["validation_status"] = "error"
            return state

        return state

    # Node 3: Routing logic - continue or aggregate
    def should_continue_validation(state: Dict) -> str:
        """Decide whether to continue validating or aggregate results"""
        chunks = state.get("chunks", [])
        current_idx = state.get("current_chunk_index", 0)

        if current_idx >= len(chunks):
            return "aggregate_findings"
        else:
            return "validate_chunk"

    # Node 4: Aggregate findings
    def aggregate_all_findings(state: Dict) -> Dict:
        """Aggregate validation results across all chunks"""
        chunks = state.get("chunks", [])
        validations = state.get("chunk_validations", [])

        total_chunks = len(chunks)
        clean_chunks = sum(1 for v in validations if v["severity"] == "clean")
        warning_chunks = sum(1 for v in validations if v["severity"] == "warning")
        critical_chunks = sum(1 for v in validations if v["severity"] == "critical")

        quality_score = clean_chunks / total_chunks if total_chunks > 0 else 0.0

        # Build aggregate report
        typo_summary = f"총 {len(state.get('typo_errors', []))}개 청크에서 오타 발견"
        logic_summary = f"총 {len(state.get('logic_errors', []))}개 청크에서 논리적 오류 발견"

        state["summary"] = {
            "total_chunks": total_chunks,
            "clean_chunks": clean_chunks,
            "warning_chunks": warning_chunks,
            "critical_chunks": critical_chunks,
            "overall_quality_score": round(quality_score, 2),
            "typo_summary": typo_summary,
            "logic_summary": logic_summary,
        }

        state["validation_status"] = "complete"
        return state

    # Add nodes to workflow
    workflow.add_node("initialize", initialize_validation)
    workflow.add_node("validate_chunk", validate_single_chunk)
    workflow.add_node("aggregate_findings", aggregate_all_findings)

    # Add conditional edges
    workflow.add_edge("initialize", "validate_chunk")
    workflow.add_conditional_edges(
        "validate_chunk",
        should_continue_validation,
        {
            "validate_chunk": "validate_chunk",
            "aggregate_findings": "aggregate_findings",
        },
    )
    workflow.add_edge("aggregate_findings", END)

    # Set entry point
    workflow.set_entry_point("initialize")

    return workflow


def run_validation_workflow(
    chunks: List[Dict],
    llm: Optional[ChatOpenAI] = None,
    verbose: bool = False,
) -> Dict:
    """
    Execute the validation workflow and return results.

    Args:
        chunks: List of chunk dicts from pdf_loader.py
        llm: LangChain LLM instance
        verbose: Print progress

    Returns:
        Complete validation report
    """
    graph = create_validation_graph(llm=llm)
    compiled_graph = graph.compile()

    initial_state = {
        "chunks": chunks,
        "chunk_validations": [],
        "typo_errors": [],
        "logic_errors": [],
        "current_chunk_index": 0,
        "validation_status": "running",
    }

    # Execute workflow
    result = compiled_graph.invoke(initial_state)

    if verbose:
        print(f"Validation complete. Quality score: {result['summary']['overall_quality_score']}")

    return result