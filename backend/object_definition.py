from qwen_model import qwen_model

async def describe_object(task):
    """
    Describe the desired object based on the provided task.
    Args:
        task (str): The task or query involving the object to be created.
    Returns:
        str: A small description of the object to be created.
    """
    prompt = f"""
    You are an expert in selecting the object that needs to be created, given a query.
    Query: {task}

    Return ONLY the name of the object that needs to be created.
    If defined in the text, include its properties like color, size, material, etc.
    Otherwise, only return the name.

    Here's an example:
    Task: "Create a red table model."
    
    Response format: "red table"
    """
    messages = [
        {"role": "system", "content": "You are an AI assistant designed to help users extract the object they need to create in a VR environment."},
        {"role": "user", "content": prompt}
    ]
    object = await qwen_model(messages)
    if not object:
        return "unknown object"
    return object.strip()


def generateId(name, nameCounters):
    """
    Generate a unique ID for an object based on its name and a counter.
    Args:
        name (str): The base name of the object.
        nameCounters (dict): A dictionary tracking the count of each object name.
    Returns:
        str: A unique ID for the object.
        dict: Updated nameCounters dictionary.
    """
    # If the name is not in the counters, initialize it
    if name not in nameCounters:
        nameCounters[name] = 1
    else: # Otherwise, increment the counter
        nameCounters[name] += 1
    return f"{name}{nameCounters[name]}", nameCounters


async def extract_name(task):
    """
    Extract the main object's name from the user's task.
    Args:
        task (str): The user's task or query.
    Returns:
        str: The extracted name of the main object.
    """
    prompt = f"""
    You are an expert in extracting the name of the main object the user wants to create based on their request.
    Your task is to extract ONLY the name of the main object.

    Do not include any descriptions, attributes, or properties, such as color, height, or size.
    Do not include words like "model".
    Do not include numbers.

    Return only the single name of the object, and nothing else.
    The name MUST be a NOUN.
    
    User's request: {task}
    """
    messages = [
        {"role": "system", "content": "You are an AI assistant designed to help users extract the name of the main object based on their request."},
        {"role": "user", "content": prompt}
    ]
    name = await qwen_model(messages)
    return name.strip().replace(" ", "_").lower()


async def define_position(question, semantic_graph):
    """
    Define the direction and distance to place an object relative to a reference object or the user.
    Args:
        question (str): The user's question or instruction.
        semantic_graph (list): A list of objects in the environment with their properties.
    Returns:
        str: A JSON string containing the reference ID, direction, and distance.
    """
    prompt = f"""
    You are an expert at interpreting spatial instructions from a user.

    Your job:
    1. Identify the reference object within the semantic graph in the question (could be 'me' for the user).
    2. Identify the relative direction (one of: front, back, left, right, up, down).
        - If the user says "next to", map it to "right".
        - If the user says "on"/"on top of" or "under", map them to "up" and "down" respectively.
    3. Identify the distance in meters (default = 0.5 if not specified for "up/down", 1 for others).
    4. Return the reference ID, direction, and distance in JSON format.
    5. If no direction is specified, assume the object should be placed in front of the user.

    You MUST ONLY return the result directly in JSON format:
    {{
        "reference_id": "<id from semantic_graph or 'user'>",
        "direction": "<front|back|left|right|up|down>",
        "distance": <number>
    }}

    Semantic Graph: {semantic_graph}
    Question: {question}

    Examples:
    Question: "Place the chair in front of me."
    Response: 
    {{ 
        "reference_id": "user", 
        "direction": "front", 
        "distance": 1
    }}

    Question: "Put the table 2 meters to the left of the sofa."
    Response: 
    {{ 
        "reference_id": "sofa1", 
        "direction": "left", 
        "distance": 2 
    }}

    Question: "Create a table to the right of the chair."
    Response: 
    {{ 
        "reference_id": "chair1", 
        "direction": "right", 
        "distance": 1 
    }}

    Question: "Place a lamp on the table."
    Response:
    {{ 
        "reference_id": "table1", 
        "direction": "up", 
        "distance": 0.5 
    }}
    """
    messages = [
        {"role": "system", "content": "You determine spatial directions from natural language instructions."},
        {"role": "user", "content": prompt}
    ]
    result = await qwen_model(messages)
    return result.strip()


async def define_object(object_id, name, properties, path, position):
    """
    Define the properties of an object to be created in the VR environment.
    Args:
        object_id (str): The unique ID of the object.
        name (str): The name of the object.
        properties (dict): A dictionary of properties containing the object's color.
        path (str): The file path to the object's 3D model.
        position (dict): A dictionary containing position details like reference_id, direction, and distance.
    Returns:
        dict: A dictionary containing all the object's properties.
    """
    object_properties = {
        "id": object_id,
        "name": name,
        "color": properties.get("color", "unknown"),
        "path": path,
        "position": position
    }
    return object_properties