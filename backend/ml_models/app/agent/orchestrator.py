"""
The agentic controller: reads a natural-language query + validated input
scope, decides which task(s) it maps to, calls the right tool(s) from the
registry, and returns a merged, auditable response.

Design note: research on agentic remote-sensing systems (RS-Agent, and the
2026 "Agentic AI for Remote Sensing" survey) flags two recurring failure
modes this orchestrator is explicitly built to avoid:
  1. Task-inference over-abstraction (picking the wrong tool for a query)
     -> mitigated with a small, explicit keyword/rule layer PLUS an LLM
        fallback, rather than trusting the LLM's tool choice blindly.
  2. Silent error propagation through multi-tool workflows
     -> mitigated by returning a full execution_trace with per-step
        confidence, so a low-confidence step is visible, not hidden.
"""

import time

from app.agent.tool_registry import get_tool
from app.schemas.requests import InputScope, ModelStep, QueryResponse, TaskType
from app.utils.geo_io import LoadedImage

# --- Simple rule-based intent classifier -----------------------------------
# TODO: replace/augment with a real LLM function-calling classifier
# (e.g. via app.config.settings.ORCHESTRATOR_LLM) once you have API access
# or a local instruct model. Keep this rule layer as a fast, free fallback
# and a sanity check against the LLM's choice — don't remove it outright.

_KEYWORD_TASK_MAP: list[tuple[list[str], TaskType]] = [
    (["highlight", "locate", "where is", "point to"], TaskType.GROUNDING),
    (["what changed", "difference between", "compare these", "before and after"], TaskType.CHANGE_VQA),
    (["classify", "land use", "land cover", "map the"], TaskType.LAND_SEGMENTATION),
    (["describe", "what is in", "caption"], TaskType.CAPTIONING),
]


def classify_task(query_text: str, input_scope: InputScope) -> TaskType:
    lowered = query_text.lower()

    for keywords, task in _KEYWORD_TASK_MAP:
        if any(kw in lowered for kw in keywords):
            # Cross-check task against input scope so a change-VQA request
            # on a single image doesn't silently get routed wrong.
            if task == TaskType.CHANGE_VQA and input_scope != InputScope.BI_TEMPORAL_PAIR:
                continue
            return task

    if input_scope == InputScope.BI_TEMPORAL_PAIR:
        return TaskType.CHANGE_VQA
    if input_scope == InputScope.CROSS_MODAL_PAIR:
        return TaskType.OPTICAL_SAR_FUSION

    return TaskType.VQA  # sensible default for a single image + open-ended question


def run_query(
    query_text: str,
    images: list[LoadedImage],
    input_scope: InputScope,
) -> QueryResponse:
    trace: list[ModelStep] = []
    task = classify_task(query_text, input_scope)
    tool = get_tool(task)

    start = time.monotonic()

    if task in (TaskType.VQA, TaskType.CAPTIONING):
        output = tool.predict(images[0].array, query_text)
    elif task == TaskType.GROUNDING:
        output = tool.predict(images[0].array, query_text)
    elif task in (TaskType.CHANGE_VQA, TaskType.CHANGE_DESCRIPTION):
        output = tool.predict(images[0].array, images[1].array, query_text)
    elif task == TaskType.OPTICAL_SAR_FUSION:
        output = tool.predict(images[0].array, images[1].array, query_text)
    elif task == TaskType.LAND_SEGMENTATION:
        output = tool.predict(images[0].array)
    else:
        raise ValueError(f"No execution path defined for task type: {task}")

    duration_ms = int((time.monotonic() - start) * 1000)
    trace.append(
        ModelStep(model_name=tool.name, task=task, confidence=output.confidence, duration_ms=duration_ms)
    )

    return QueryResponse(
        answer=output.text,
        task_type=task,
        confidence=output.confidence,
        bounding_boxes=output.bounding_boxes or None,
        change_mask_url=None,  # TODO: wire up mask -> saved PNG -> URL once storage layer exists
        execution_trace=trace,
        report_download_url=None,  # TODO: generate a downloadable PDF/JSON report here
    )

