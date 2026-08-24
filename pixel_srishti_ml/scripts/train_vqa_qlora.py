import torch
from transformers import AutoProcessor, AutoModelForCausalLM, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

def setup_qlora_model(model_id="Salesforce/blip2-opt-2.7b"):
    """
    Initializes a lightweight VLM for QLoRA fine-tuning.
    We target a ~2.7B to 7B parameter model to ensure it fits on a single T4 GPU.
    """
    print(f"Loading {model_id} in 4-bit...")
    
    # 1. 4-bit Quantization Config (Requires bitsandbytes, CUDA only)
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16
    )

    processor = AutoProcessor.from_pretrained(model_id)
    
    # 2. Load Base Model
    model = AutoModelForCausalLM.from_pretrained(
        model_id, 
        quantization_config=bnb_config, 
        device_map="auto"
    )

    # 3. Prepare for PEFT
    model = prepare_model_for_kbit_training(model)

    # 4. LoRA Config (Targeting attention blocks)
    config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "v_proj"], # Varies slightly by model architecture
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )

    model = get_peft_model(model, config)
    model.print_trainable_parameters()
    
    return model, processor

# NOTE: Training loop script will use HuggingFace Trainer/SFTTrainer 
# connected to the datasets/rsvqa.py loader.
