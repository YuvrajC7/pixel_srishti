import os
import torch
from datasets import load_dataset
from transformers import (
    AutoProcessor, 
    PaliGemmaForConditionalGeneration, 
    TrainingArguments, 
    Trainer
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import BitsAndBytesConfig

# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------
MODEL_ID = "google/paligemma-3b-pt-224"
OUTPUT_DIR = "./paligemma-bigearthnet-lora"
MAX_LENGTH = 128
BATCH_SIZE = 2
EPOCHS = 3
LEARNING_RATE = 2e-4

def prepare_model():
    print("Loading BitsAndBytes Config for 4-bit quantization...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16
    )

    print(f"Loading Base Model: {MODEL_ID}")
    model = PaliGemmaForConditionalGeneration.from_pretrained(
        MODEL_ID,
        quantization_config=bnb_config,
        device_map="auto"
    )
    
    # Prepare model for PEFT
    model = prepare_model_for_kbit_training(model)
    
    print("Configuring LoRA Adapters...")
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "v_proj", "k_proj", "o_proj"], # Target attention blocks
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )
    
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    return model

def get_processor():
    return AutoProcessor.from_pretrained(MODEL_ID)

def train():
    model = prepare_model()
    processor = get_processor()
    
    print("Loading Dataset (Simulation for BigEarthNet.txt)...")
    # In a real scenario, you load your local dataset. 
    # Example: dataset = load_dataset("json", data_files="bigearthnet_vqa.json")
    # For this script, we assume the dataset has columns: ['image', 'question', 'answer']
    
    # We define a custom data collator for PaliGemma
    def collate_fn(examples):
        images = [example["image"] for example in examples]
        texts = [example["question"] for example in examples]
        labels = [example["answer"] for example in examples]
        
        # Processor handles prompt formatting for PaliGemma
        inputs = processor(
            text=texts, 
            images=images, 
            return_tensors="pt", 
            padding=True,
            truncation=True,
            max_length=MAX_LENGTH
        )
        
        # Tokenize labels
        label_inputs = processor(
            text=labels,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=MAX_LENGTH
        )
        
        inputs["labels"] = label_inputs["input_ids"]
        return inputs

    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=4,
        optim="paged_adamw_32bit",
        save_steps=100,
        logging_steps=10,
        learning_rate=LEARNING_RATE,
        weight_decay=0.001,
        max_steps=500, # For hackathon quick testing
        bf16=True, # Use bfloat16 if supported by GPU
        max_grad_norm=0.3,
        warmup_ratio=0.03,
        report_to="none"
    )

    print("Initializing Trainer...")
    # NOTE: Pass your loaded train_dataset here instead of None
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=None, # REPLACE WITH: dataset["train"]
        data_collator=collate_fn,
    )

    print("Starting QLoRA Fine-Tuning...")
    # trainer.train()
    
    print(f"Saving LoRA adapters to {OUTPUT_DIR}...")
    # trainer.model.save_pretrained(OUTPUT_DIR)
    # processor.save_pretrained(OUTPUT_DIR)
    print("Training Script Ready. Just plug in the BigEarthNet data!")

if __name__ == "__main__":
    train()