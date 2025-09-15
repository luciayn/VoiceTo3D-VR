import json
import os

from color_extractor import color_extractor
from image_to_3D import generate_3D_model
from task_classifier import classify_task
from task_divider import divide_tasks, reviewer_tasks
from text_to_image import generate_image
from object_definition import define_object, define_position, extract_name, generateId, describe_object


async def create_object_pipeline(question, semantic_graph, nameCounters, final_position, websocket):
    """
    Create a new 3D object based on the user's question and place it in the environment.
    Args:
        question (str): The user's question or command.
        semantic_graph (dict): The current semantic graph of the environment.
        nameCounters (dict): A dictionary to keep track of object name counts for unique ID generation.
        final_position (dict or None): The final position for the object if already determined.
        websocket (WebSocket): The WebSocket connection to communicate with the client.
    Returns:
        dict: The properties of the created object.
    """
    # Describe the object based on the question
    object_description = await describe_object(question)
    # print(f"Object Description: {object_description}")
    
    # Extract the object's name and generate its object_id
    name = await extract_name(question)
    object_id, nameCounters = generateId(name, nameCounters)

    # Generate a stylized 3D render image of the object
    image_bytes, image_path = generate_image(object_description, object_id)

    # Generate a 3D model of the object from the image
    model_path = await generate_3D_model(image_path, object_id)
    
    # Extract the color of the object from the image
    color = color_extractor(image_path, object_description)
    properties = {"color": color}
    # print(f"Object Color: {color}")
    
    # Determine the position of the object
    if final_position == None:
        position_result = await define_position(question, semantic_graph)
        print("Position result: ", position_result)

        # Request the client to calculate the world position
        position_data = json.loads(position_result)
        reference_id = position_data['reference_id']
        direction = position_data['direction']
        distance = position_data['distance']
        await websocket.send_text(json.dumps({
            "type": "calculate_position",
            "reference_id": reference_id,
            "direction": direction,
            "distance": distance
        }))
        while True:
            message = await websocket.receive()
            if 'text' in message:
                data = json.loads(message['text'])
                if data.get("type") == "world_position":
                    final_position = data.get("position")
                    print(f"Calculated Position: {final_position}")
                    break

    # Define the object with all its properties
    object_properties = await define_object(object_id, name, properties, model_path, final_position)
    
    # Save the new model to the models.json file
    await save_model(object_properties)
    # Send the new model data to the client
    await websocket.send_text(json.dumps({
        "type": "new_model",
        "model": object_properties
    }))
    return object_properties


async def manipulate_object_pipeline(question, semantic_graph, object_id, final_position, websocket):
    """
    Determine the 3D position of an existing object in the scene based on user instructions.
    Args:
        question (str): The user's question or command.
        semantic_graph (dict): The current semantic graph of the environment.
        object_id (str): The ID of the object to manipulate.
        final_position (dict or None): The final position for the object if already determined.
        websocket (WebSocket): The WebSocket connection to communicate with the client.
    Returns:
        dict: The updated properties of the manipulated object.
    """
    # Load existing models
    with open("../data/models.json", "r") as f:
        models = json.load(f)

    # Find the object in the models
    object = next((model for model in models if model['id'] == object_id), None)
    if not object:
        return (f"Object with ID {object_id} not found in models.")
    
    # If a final position is provided, use it directly
    if final_position:
        object['position'] = final_position
    else:
        # Otherwise, define the position based on the task
        position_result = await define_position(question, semantic_graph)

        # Request the client to calculate the world position
        position_data = json.loads(position_result)
        reference_id = position_data['reference_id']
        direction = position_data['direction']
        distance = position_data['distance']
        await websocket.send_text(json.dumps({
            "type": "calculate_position",
            "reference_id": reference_id,
            "direction": direction,
            "distance": distance
        }))
        while True:
            message = await websocket.receive()
            if 'text' in message:
                data = json.loads(message['text'])
                if data.get("type") == "world_position":
                    object['position'] = data.get("position")
                    print(f"Calculated Position: {object['position']}")
                    break
    # Save the updated model to the models.json file
    await save_model(object)
    # Send the new model data to the client
    await websocket.send_text(json.dumps({
        "type": "new_model",
        "model": object
    }))
    print(f"Object: {object['id']} moved to position: {object['position']}")
    return object


async def handle_task(task, semantic_graph, nameCounters, final_position, websocket, context=""):
    """
    Handle a user's task by classifying it and executing the appropriate pipeline.
    Args:
        task (str): The user's task or command.
        semantic_graph (dict): The current semantic graph of the environment.
        nameCounters (dict): A dictionary to keep track of object name counts for unique ID generation.
        final_position (dict or None): The final position for the object if already determined.
        websocket (WebSocket): The WebSocket connection to communicate with the client.
        context (str): Contextual information from previous tasks.
    Returns:
        str: Updated context after handling the task.
    """
    response = await classify_task(task, semantic_graph, context)

    # If a final action is specified, use it as the question/task 
    if response['final_action'] != "":
        task = response['final_action']

    # If task is classified as multitask, divide and conquer
    if response['classification'] == "multitask":
        # Recursively handle subtasks until review feedback is positive
        feedback = "negative"
        while "negative" in feedback.lower():
            subtasks = await divide_tasks(task)
            feedback = await reviewer_tasks(task, subtasks)

        # Handle each subtask sequentially
        for subtask in subtasks:
            print("Subtask: ", subtask)
            # Use context from previous tasks
            context = await handle_task(
                subtask, semantic_graph, nameCounters, final_position, websocket, context
            )
        return context

    # Handle single tasks
    elif response['classification'] == "create":
        obj = await create_object_pipeline(task, semantic_graph, nameCounters, final_position, websocket)
        context += f"Created object in previous task: {{'id': {obj['id']}, 'position': {obj['position']}}}\n"
        return context

    elif response['classification'] == "manipulate":
        for object_id in response['manipulate_objects']:
            result = await manipulate_object_pipeline(task, semantic_graph, object_id, final_position, websocket)
            context += f"Manipulated object in previous task: {{'id': {result['id']}, 'position': {result['position']}}}\n"
        return context

    # Handle delete tasks
    elif response['classification'] == "delete":
        for object_id in response['delete_objects']:
            # Load existing models
            with open("../data/models.json", "r") as f:
                        models = json.load(f)
            # Remove the object from the models list
            remaining_models = [m for m in models if m["id"] != object_id]
            with open("../data/models.json", "w", encoding="utf-8") as f:
                json.dump(remaining_models, f, indent=2)
            # Notify the client to delete the object
            await websocket.send_text(json.dumps({
                "type": "delete_object",
                "object_id": object_id
            }))
            context += f"Deleted object {object_id} in previous task.\n"
        return context

    else:
        print(f"Unhandled classification: {response['classification']}")
        return context
    

async def handle_disambiguation(response, websocket):
    clarification = ""
    
    # Handle cases where object is ambiguous
    if response['requires_disambiguation']:
            # If only one candidate, no need to ask user
            if len(response['disambiguation_candidates']) == 1:
                pointed_object = response['disambiguation_candidates'][0]
            else: # Otherwise, ask user to point to the object
                # Handle each disambiguation phrase
                for disambiguation_phrase in response["disambiguation_phrases"]:
                    # Extract pointed object from user
                    pointed_object = await vr_pointed_object(disambiguation_phrase, response["disambiguation_candidates"], websocket)
                    clarification += f"For the disambiguation phrase {disambiguation_phrase}, the user clarified object: {pointed_object}\n"
    
    # Handle cases where spatial phrases are ambiguous
    if response['requires_pointing']:
        # Handle each spatial phrase
        for spatial_phrase in response["spatial_phrases"]:
            # Ask user to point to the location
            await websocket.send_text(json.dumps({
                "type": "start_pointing_location",
                "spatial_phrase": spatial_phrase
            }))
            # Extract pointed location from user
            pointed_location = await vr_pointed_location(spatial_phrase, websocket)
            clarification += f"For the spatial phrase {spatial_phrase}, the user pointed to location: {pointed_location}\n"
    
    print("Clarification: ", clarification)
    return clarification


async def vr_pointed_object(disambiguation_phrase, disambiguation_candidates, websocket):
    # print(f"[VR Prompt] Please point to the object referred to.")
    while True:
        # Ask user to point to the object
        await websocket.send_text(json.dumps({
            "type": "start_pointing_object",
            "disambiguation_phrase": disambiguation_phrase,
            "disambiguation_candidates": disambiguation_candidates
        }))
        message = await websocket.receive()
        if 'text' in message:
            data = json.loads(message['text'])
            if data.get("type") == "pointing_object":
                pointed_object = data.get("object_id")
                # Validate the pointed object
                if pointed_object not in disambiguation_candidates:
                    print(f"User pointed to an unexpected object: '{pointed_object}'. Expected: {disambiguation_candidates}")
                else:
                    # print(f"[VR Response] User pointed to object: {pointed_object}")
                    return pointed_object 

async def vr_pointed_location(spatial_phrase, websocket):
    # print(f"[VR Prompt] Please point to the location referred to by '{spatial_phrase}'.")
    while True:
        message = await websocket.receive()
        if 'text' in message:
            data = json.loads(message['text'])
            if data.get("type") == "pointing_location":
                pointed_location = data.get("position")
                # print(f"[VR Response] User pointed to location: {pointed_location}")
                # Avoid placing objects below the ground
                if pointed_location['y'] < 0.5:
                    pointed_location['y'] = 0.5
                return pointed_location
            
async def save_model(model_data):
    # Load existing models
    if os.path.exists("../data/models.json"):
        with open("../data/models.json", "r") as f:
            models = json.load(f)
    else: # If file doesn't exist, start with empty list
        models = []
    
    # Check if the model already exists and update it
    updated = False
    for i, model in enumerate(models):
        if model['id'] == model_data['id']:
            models[i] = model_data
            updated = True
            break
    # If the model is not found, append it
    if not updated:
        models.append(model_data)
    with open("../data/models.json", "w") as f:
        json.dump(models, f, indent=2)
    print(f"Model {model_data['id']} saved successfully.") 