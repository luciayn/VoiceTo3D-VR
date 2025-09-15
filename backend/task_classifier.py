import json
from qwen_model import qwen_model

async def classify_task(task, semantic_graph, clarification=""):
    """
    Classify the task to determine if it requires object creation or modification.
    Args:
        task (str): The user's task description.
        semantic_graph (list): List of objects in the scene with their attributes.
        clarification (str): Any additional clarification provided by the user.
    Returns:
        dict: A dictionary containing the classification results and any required disambiguation or pointing information.
    """
    scene_description = "\n".join(f"- {obj}" for obj in semantic_graph)           

    prompt = f"""You are an AI assistant that classifies tasks based on user requests and the current scene.
    You will receive a task and a semantic graph of the scene. Your goal is to classify the task and identify objects to manipulate or create or delete.
    The task may involve creating new objects, manipulating or deleting existing ones, or a combination of many actions. 
    You will also determine if disambiguation or pointing is required:
    - If the object to manipulate or delete is ambiguous, set requires_disambiguation to true, provide disambiguation_candidates and disambiguation_phrases.
    - Do not use the 'requires_disambiguation' flag if the task is related to creating a new object.
    - If 'requires_disambiguation' is set to true, make sure the disambiguation_candidates and disambiguation_phrases are NOT EMPTY.
    - Only set requires_pointing to true if the user uses vague spatial references such as "here" or "there" without any precise spatial relationship or coordinates. Provide spatial_phrases.
    - You MUST NOT set requires_pointing to true for spatial prepositions like "next to", "in front of", "behind", "on top of", "under", or "to the left/right of", nor for egocentric spatial references such as "to my left/right", "in front of me", etc. These are handled by object/user relationships, not spatial ambiguity.

    Scene objects:
    {scene_description}

    Task: "{task}"

    Clarification: {clarification}

    Instructions:
    1. Identify objects to manipulate in the task, do not include the reference object.
    2. Classify the task as one of: [create, manipulate, delete, multitask]. 
    3. If the task involves creating or manipulating more than 1 object, you MUST classify it as "multitask".
    4. If ambiguity remains, set requires_disambiguation or requires_pointing flags.
    5. If clarification is provided, resolve the task completely. ONLY if a location/position with format "x y z" is specified, include it in the response. Replace the ambiguous phrases with the actual object ID or position.
    6. Respond with ONLY the JSON object.

    Output format:
    {{
        "manipulate_objects": [...],
        "delete_objects": [...],
        "classification": "...",
        "requires_disambiguation": true/false,
        "disambiguation_candidates": [...],
        "disambiguation_phrases": [...],
        "requires_pointing": true/false,
        "spatial_phrases": [...],
        "final_action": "...",
        "final_position": "..."
    }}

    Examples:
    semantic_graph = [
        {{
            id: "table1", 
            name: "table",
            color: "brown",
            position: "1 0 0"
        }},
        {{
            id: "chair1", 
            name: "chair",
            color: "red",
            position: "0 0 0"
        }},
        {{
            id: "chair2",
            name: "chair",
            color: "blue",
            position: "0 2 0"
        }}
    ]
    1. question = "Place that over here"
    response = 
        {{
            "manipulate_objects": [],
            "delete_objects": [],
            "classification": "manipulate",
            "requires_disambiguation": true,
            "disambiguation_candidates": ["table1", "chair1"],
            "disambiguation_phrases": ["that"],
            "requires_pointing": true,
            "spatial_phrases": ["here"],
            "final_action": "",
            "final_position": ""
        }}
    2. question = "Place that over here"
    clarification = "User clarified object: table1, User pointed to location: 2 0 0"
    response = 
        {{
            "manipulate_objects": [table1],
            "delete_objects": [],
            "classification": "manipulate",
            "requires_disambiguation": false,
            "disambiguation_candidates": [],
            "disambiguation_phrases": [],
            "requires_pointing": false,
            "spatial_phrases": [],
            "final_action": "Place table1 over 2 0 0"
            "final_position": "2 0 0"
        }}  
    3. question = "Place the chair next to/on top of/under/in front of/behind/to the left/right of the table"
    response = 
        {{
            "manipulate_objects": [],
            "delete_objects": [],
            "classification": "manipulate",
            "requires_disambiguation": true,
            "disambiguation_candidates": [chair1, chair2],
            "disambiguation_phrases": [],
            "requires_pointing": false,
            "spatial_phrases": [],
            "final_action": ""
            "final_position": ""
        }}
    4. question = "Create 2 chairs to my left"
    response = 
        {{
            "manipulate_objects": [],
            "delete_objects": [],
            "classification": "multitask",
            "requires_disambiguation": false,
            "disambiguation_candidates": [],
            "disambiguation_phrases": [],
            "requires_pointing": false,
            "spatial_phrases": [],
            "final_action": "",
            "final_position": ""
        }}
    5. question = "Remove the table in front of me"
    response = 
        {{
            "manipulate_objects": [],
            "delete_objects": [table1],
            "classification": "delete",
            "requires_disambiguation": false,
            "disambiguation_candidates": [],
            "disambiguation_phrases": [],
            "requires_pointing": false,
            "spatial_phrases": [],
            "final_action": "",
            "final_position": ""
        }}
    """
    messages = [
        {"role": "system", "content": "You are an AI assistant designed to classify tasks based on user requests and the current scene."},
        {"role": "user", "content": prompt}
    ]
    response = await qwen_model(messages)
    print("\nResponse: ")
    print(json.loads(response))
    return json.loads(response)