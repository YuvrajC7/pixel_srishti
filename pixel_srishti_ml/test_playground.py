import os
from tools.agent_tools import (
    tool_segment_image,
    tool_detect_change,
    tool_detect_objects,
    tool_answer_vqa
)

def run_tests():
    print("=========================================================")
    print("    PIXEL-SRISHTI MODEL PLAYGROUND & TEST SCRIPT         ")
    print("=========================================================")
    print("Use this tool to independently test every model we built.")
    print("Please make sure you have 1 or 2 test satellite images saved locally.\n")
    
    img_path = input("Enter the path to a test image (e.g., test1.jpg): ").strip()
    if not os.path.exists(img_path):
        print(f"\n[Error] Could not find '{img_path}'. Please make sure the image exists and try again.")
        return

    # --- 1. Grounding DINO ---
    print("\n---------------------------------------------------------")
    print("[1] Testing Object Detection (Grounding DINO)")
    print("---------------------------------------------------------")
    query = input("What object should I look for? (e.g., 'houses', 'water', 'road'): ").strip()
    print("Loading Grounding DINO (this may take a few seconds)...")
    res_obj = tool_detect_objects(img_path, query)
    print(f">>> Result: {res_obj['description']}")
    print(f">>> Bounding Boxes Found: {len(res_obj['boxes'])}")
    
    # --- 2. BLIP-2 VQA ---
    print("\n---------------------------------------------------------")
    print("[2] Testing Visual Question Answering (BLIP-2)")
    print("---------------------------------------------------------")
    question = input("Ask a natural language question about the image: ").strip()
    print("Loading BLIP-2 (this may take a few seconds)...")
    res_vqa = tool_answer_vqa(img_path, question)
    print(f">>> Answer: {res_vqa}")

    # --- 3. DeepLabV3+ ---
    print("\n---------------------------------------------------------")
    print("[3] Testing Semantic Segmentation (DeepLabV3+)")
    print("---------------------------------------------------------")
    print("Loading your trained DeepLabV3+ weights...")
    res_seg, mask_seg = tool_segment_image(img_path)
    print(">>> Analysis Output:")
    print(res_seg)
    print(f">>> 🎨 A colored visual mask has been saved to your folder at: {mask_seg}")
    print("    (You can open this file to see the land cover map!)")
    
    # --- 4. Siamese U-Net ---
    print("\n---------------------------------------------------------")
    print("[4] Testing Change Detection (Siamese U-Net)")
    print("---------------------------------------------------------")
    img_b_path = input("To test change detection, enter the path to a SECOND image (the 'after' image): ").strip()
    if not os.path.exists(img_b_path):
         print(f"[Error] Could not find '{img_b_path}'. Skipping change detection.")
    else:
        print("Loading your trained Siamese U-Net weights...")
        res_cd, mask_cd = tool_detect_change(img_path, img_b_path)
        print(f">>> Analysis Output: {res_cd}")
        print(f">>> 🎨 A binary change mask has been saved to your folder at: {mask_cd}")
        print("    (You can open this file to see the highlighted changes!)")

    print("\n=========================================================")
    print(" All individual model tests complete! ")
    print("=========================================================")

if __name__ == "__main__":
    # Prevent PyTorch from throwing warnings during our clean CLI script
    import warnings
    warnings.filterwarnings("ignore")
    run_tests()
