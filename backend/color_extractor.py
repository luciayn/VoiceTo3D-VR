from PIL import Image
from transformers import pipeline

# Load the pipeline for VQA with the BLIP model
color_extractor_pipe = pipeline("visual-question-answering", model="Salesforce/blip-vqa-base", model_kwargs={"cache_dir": "/mnt/shared_models/huggingface/cache/hub"})

def color_extractor(image_path, object_name):
    """
    Extract the color of the object from the image.
    Args:
        image_path (str): Path to the image file.
        object_name (str): Name of the object whose color is to be extracted.
    Returns:
        str: The color of the object.
    """
    image = Image.open(image_path).convert("RGB")
    question = f"What color is the {object_name} in the image?"    
    color = color_extractor_pipe(image, question)[0]['answer']
    return color