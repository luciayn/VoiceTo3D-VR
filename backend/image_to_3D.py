import base64
import httpx
import io
import time
from html_template import HTML_BASE
from PIL import Image

# Convert PIL image to base64 string
def pil_image_to_base64_str(img):
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# Send POST request with base64 image and get response
async def send_3d_request(
    image_b64_str,
    server_url="http://aicube_hunyuan:8081/generate",
    generate_texture=True,
):
    """
    Sends a POST request with a base64-encoded image and saves the response as a file.

    Args:
        image (PIL.Image): The image to send.
        server_url (str): The URL of the server.
        generate_texture (bool): Whether to generate a texture for the 3D model.
    Returns:
        bytes: The content of the response if successful, None otherwise.
    """
    client = httpx.AsyncClient(timeout=900)  # Set a timeout of 900 seconds
    payload = {"image": image_b64_str, "texture": generate_texture}
    headers = {"Content-Type": "application/json"}

    response = await client.post(server_url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.content
    else:
        print(f"Request failed with status code {response.status_code}: {response.text}")
        return None

async def generate_3D_model(image_path, object_id):
    """
    Generate a 3D model of the specified object using Stable Diffusion.
    Args:
        image_path (str): Path to the input image.
        object_id (str): Name of the object to be generated.
    Returns:
        str: Path to the saved 3D model file.
    """
    output_path = f"../models/{object_id}.glb".replace(" ", "_")

    # Load and convert image to base64 string
    image = Image.open(image_path)
    image_b64_str = pil_image_to_base64_str(image)

    print(f"Generating {object_id} 3D model...")
    try:
        start_time = time.time()
        result = await send_3d_request(
            image_b64_str,
            server_url="http://localhost:8081/generate",
            generate_texture=True,
        )
        end_time = time.time()
        elapsed = end_time - start_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        print(f"{object_id} took {minutes} mins {seconds} secs to be generated.\n")
    except Exception as e:
        print(f"Error occurred while generating 3D model: {e}")
        return

    # Save the result to a .glb file
    if result:
        with open(output_path, "wb") as f:
            f.write(result)
        print(f"3D model saved to {output_path}")

        # Generate HTML content with embedded 3D model
        glb_b64 = base64.b64encode(result).decode("utf-8")
        html_content = HTML_BASE.format(MODEL_DATA=glb_b64)

        # Save the HTML content to a file
        html_file_path = f"../html/{object_id}.html"
        with open(html_file_path, "w") as html_file:
            html_file.write(html_content)

        return f"../../models/{object_id}.glb".replace(" ", "_")
    else:
        print("Failed to generate 3D model.")