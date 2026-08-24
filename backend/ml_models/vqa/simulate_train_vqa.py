import time
import sys
import codecs

# Force utf-8 for stdout if possible, or just use ascii chars
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach()) if hasattr(sys.stdout, 'detach') else sys.stdout

def print_slow(text, delay=0.03):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def simulate():
    print_slow("Loading BitsAndBytes Config for 4-bit quantization...", 0.01)
    time.sleep(0.5)
    print("bnb_4bit_compute_dtype: torch.bfloat16")
    print("load_in_4bit: True")
    print("bnb_4bit_use_double_quant: True")
    
    print_slow("\nLoading Base Model: google/paligemma-3b-pt-224...", 0.01)
    time.sleep(1)
    print("Fetching shards...")
    for i in range(1, 4):
        print(f"Downloading model-0000{i}-of-00003.safetensors: 100%|[##########]| 4.8G/4.8G [00:0{i}<00:00, 1.2GB/s]")
        time.sleep(0.3)
        
    print_slow("Model loaded successfully. Preparing for K-Bit training...", 0.01)
    time.sleep(0.5)
    
    print_slow("\nConfiguring LoRA Adapters...", 0.01)
    time.sleep(0.3)
    print("target_modules: ['q_proj', 'v_proj', 'k_proj', 'o_proj']")
    print("trainable params: 11,534,336 || all params: 2,934,816,768 || trainable%: 0.3930")
    
    print_slow("\nLoading Dataset (BigEarthNet_VQA_Sample)...", 0.01)
    time.sleep(0.5)
    print("DatasetDict({")
    print("    train: Dataset({")
    print("        features: ['image', 'question', 'answer'],")
    print("        num_rows: 5000")
    print("    })")
    print("})")
    
    print_slow("\nInitializing SFT Trainer...", 0.01)
    time.sleep(0.5)
    print("Detected kernel version 5.15.0, which is below the recommended minimum of 5.15.0 for bitsandbytes.")
    print("Using paged_adamw_32bit optimizer")
    
    print_slow("\nStarting QLoRA Fine-Tuning...", 0.02)
    print("  Num examples = 5,000")
    print("  Num Epochs = 3")
    print("  Instantaneous batch size per device = 2")
    print("  Gradient Accumulation steps = 4")
    print("  Total optimization steps = 1,875")
    
    print("\n[Training Progress]")
    steps = [10, 20, 30, 40, 50, 100]
    loss = [2.451, 2.103, 1.842, 1.521, 1.294, 0.941]
    
    for i in range(len(steps)):
        bar_length = int(40 * (steps[i]/100))
        bar = '#' * bar_length + '-' * (40 - bar_length)
        sys.stdout.write(f"\r  {steps[i]}/1875 [{bar}] - loss: {loss[i]:.4f} - lr: 1.9e-4")
        sys.stdout.flush()
        time.sleep(0.8)
        if i == len(steps)-1:
            print()
            
    print_slow("\nSaving LoRA adapters to ./paligemma-bigearthnet-lora...", 0.02)
    time.sleep(0.5)
    print("Model weights saved in ./paligemma-bigearthnet-lora/adapter_model.safetensors")
    print("Training Simulation Complete! VLM successfully fine-tuned for Remote Sensing.")

if __name__ == '__main__':
    simulate()