"""
Registers every specialist model as a "tool" the orchestrator can call.
Adding a new model to the system should only ever require:
  1. Writing app/models/your_new_model.py (subclassing BaseSpecialistModel)
  2. Registering it here with the TaskTypes it can serve

The orchestrator never imports model classes directly — it only ever
looks things up through this registry, which is what keeps the
"add new capability without redesigning the controller" promise
from the proposal's future-scope section actually true.
"""

from app.config import settings
from app.models.change_detection import ChangeDetectionModel
from app.models.grounding import GroundingModel
from app.models.land_segmentation import LandSegmentationModel
from app.models.optical_sar_fusion import OpticalSARFusionModel
from app.models.vqa_captioning import VQACaptioningModel
from app.schemas.requests import TaskType

_registry: dict[TaskType, object] = {}


def build_registry() -> dict[TaskType, object]:
    """Instantiates every model once (lazy-loaded weights) and maps tasks to them."""
    global _registry
    if _registry:
        return _registry

    vqa_model = VQACaptioningModel(settings.VQA_CAPTIONING_MODEL_PATH, settings.DEVICE)
    grounding_model = GroundingModel(settings.GROUNDING_MODEL_PATH, settings.DEVICE)
    change_model = ChangeDetectionModel(settings.CHANGE_DETECTION_MODEL_PATH, settings.DEVICE)
    fusion_model = OpticalSARFusionModel(settings.OPTICAL_SAR_FUSION_MODEL_PATH, settings.DEVICE)
    segmentation_model = LandSegmentationModel(settings.LAND_SEGMENTATION_MODEL_PATH, settings.DEVICE)

    _registry = {
        TaskType.VQA: vqa_model,
        TaskType.CAPTIONING: vqa_model,
        TaskType.GROUNDING: grounding_model,
        TaskType.CHANGE_VQA: change_model,
        TaskType.CHANGE_DESCRIPTION: change_model,
        TaskType.OPTICAL_SAR_FUSION: fusion_model,
        TaskType.LAND_SEGMENTATION: segmentation_model,
    }
    return _registry


def get_tool(task: TaskType):
    registry = build_registry()
    if task not in registry:
        raise KeyError(f"No tool registered for task type: {task}")
    return registry[task]

