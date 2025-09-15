import torch
from io import BytesIO
from diffusers import StableDiffusionPipeline

device = "cuda" if torch.cuda.is_available() else "cpu"
# Load the Stable Diffusion pipeline
sd_pipe = StableDiffusionPipeline.from_pretrained("stabilityai/stable-diffusion-2", torch_dtype=torch.float16, cache_dir="/mnt/shared_models/huggingface/cache/hub")
sd_pipe = sd_pipe.to(device)


def generate_image(object_name, object_id):
    """
    Generate a stylized 3D render of the specified object using Stable Diffusion.
    Args:
        object_name (str): The name of the object to generate.
        object_id (str): The unique identifier for the object, used for saving the image.
    Returns:
        list: List of bytes of the image.
        str: File path where the image is saved.
    """
    # Define prompt for image generation
    prompt = f"A stylized 3D render of a single entire {object_name}, centered, non-cropped, isolated on a plain background, realistic, high contrast game asset style, VR-ready, front 3/4 view."
    
    # Generate image
    image = sd_pipe(prompt).images[0]
    # Save image to file
    image.save(f"../images/{object_id}.png".replace(" ", "_"))

    # Convert image to bytes
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    image_bytes = buffered.getvalue()

    return list(image_bytes), f"../images/{object_id}.png".replace(" ", "_")