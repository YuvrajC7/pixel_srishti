import os
import json
from groq import Groq
from groq import APIConnectionError, RateLimitError, APIStatusError, GroqError

# Import our PyTorch Agent Tools
from tools.agent_tools import (
    tool_detect_change,
    tool_answer_vqa,
    tool_segment_image,
    tool_detect_objects
)

class GroqOrchestratorError(Exception):
    """Custom exception raised when the Groq primary path fails (triggers fallback)."""
    pass

GROQ_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "segment_image",
            "description": "Run semantic segmentation to map buildings, woodlands, water bodies, and roads. Use when asked about urban spread, land cover, or mapping an area.",
            "parameters": {
                "type": "object",
                "properties": {
                    "image_path": {"type": "string", "description": "The exact file path of the image to segment."}
                },
                "required": ["image_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "detect_change",
            "description": "Detect structural changes, new construction, or water body alterations between two dates/images.",
            "parameters": {
                "type": "object",
                "properties": {
                    "image_a_path": {"type": "string", "description": "The file path of the older/first image."},
                    "image_b_path": {"type": "string", "description": "The file path of the newer/second image."}
                },
                "required": ["image_a_path", "image_b_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "detect_objects",
            "description": "Zero-shot object detection. Use this when the user asks to count specific items or locate objects like 'houses', 'tractors', or 'water pumps'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "image_path": {"type": "string", "description": "The exact file path of the image."},
                    "query": {"type": "string", "description": "The object to search for (e.g., 'houses')."}
                },
                "required": ["image_path", "query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "answer_vqa",
            "description": "Visual Question Answering. Use this to answer general, descriptive, or open-ended questions about what is happening in the image.",
            "parameters": {
                "type": "object",
                "properties": {
                    "image_path": {"type": "string", "description": "The exact file path of the image."},
                    "question": {"type": "string", "description": "The question to ask the visual language model."}
                },
                "required": ["image_path", "question"]
            }
        }
    }
]

def execute_tool_call(tool_name, args):
    """Executes the corresponding local PyTorch tool."""
    try:
        if tool_name == "segment_image":
            res_text, mask_path = tool_segment_image(args["image_path"])
            return f"Segmentation Results: {res_text} | Mask generated at: {mask_path}"
        
        elif tool_name == "detect_change":
            res_text, mask_path = tool_detect_change(args["image_a_path"], args["image_b_path"])
            return f"Change Detection Results: {res_text} | Mask generated at: {mask_path}"
        
        elif tool_name == "detect_objects":
            result = tool_detect_objects(args["image_path"], args["query"])
            return f"Object Detection Results: {result['description']} (Found {result['count']} items)"
            
        elif tool_name == "answer_vqa":
            answer = tool_answer_vqa(args["image_path"], args["question"])
            return f"VLM Answer: {answer}"
            
        else:
            return f"Error: Tool {tool_name} not recognized."
    except Exception as e:
        return f"Error executing {tool_name}: {str(e)}"

def run_groq_orchestrator(user_query: str, uploaded_images: list[str]) -> str:
    """
    Primary orchestrator path using Groq (Llama-3-70B).
    Handles multi-tool sequencing, parameter extraction, and natural language synthesis.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise GroqOrchestratorError("GROQ_API_KEY environment variable is not set.")
    
    try:
        client = Groq(api_key=api_key, timeout=20.0) # 20 second timeout
    except Exception as e:
        raise GroqOrchestratorError(f"Failed to initialize Groq client: {str(e)}")

    images_context = ", ".join(uploaded_images)
    
    messages = [
        {
            "role": "system",
            "content": (
                "You are the PIXEL-Srishti AI Orchestrator. Your job is to answer the user's queries regarding satellite imagery. "
                "You have access to specialist ML tools. You must call them to gather information before answering. "
                f"The user has uploaded the following image files: [{images_context}]. "
                "Always pass these exact file paths to your tools. If the user asks a multi-part question, you can call multiple tools simultaneously. "
                "Synthesize the outputs of the tools into a cohesive, professional natural language response."
            )
        },
        {
            "role": "user",
            "content": user_query
        }
    ]

    try:
        # Step 1: Initial call to Groq
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=messages,
            tools=GROQ_TOOLS,
            tool_choice="auto",
            max_tokens=1024
        )
        
        response_message = response.choices[0].message
        messages.append(response_message)
        
        # Step 2: Handle function calls if Groq decided to use tools
        if response_message.tool_calls:
            for tool_call in response_message.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)
                
                # Execute our local PyTorch functions
                tool_result = execute_tool_call(func_name, func_args)
                
                # Append tool results to conversation
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": func_name,
                    "content": tool_result
                })
            
            # Step 3: Call Groq again to synthesize the final answer
            final_response = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=messages,
                max_tokens=1024
            )
            return final_response.choices[0].message.content
        else:
            # If no tools were called, return standard text
            return response_message.content

    # Catching all specific Groq exceptions to reliably trigger the fallback
    except (APIConnectionError, RateLimitError, APIStatusError, GroqError, TimeoutError) as e:
        print(f"[Orchestrator] Groq API Error: {str(e)}")
        raise GroqOrchestratorError(f"Groq network or limit failure: {str(e)}")
    except Exception as e:
        print(f"[Orchestrator] Unexpected Error in Groq Path: {str(e)}")
        raise GroqOrchestratorError(f"Unexpected Groq failure: {str(e)}")
