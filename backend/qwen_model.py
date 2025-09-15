import httpx

async def qwen_model(
    messages,
    server_url="http://10.10.78.11:8080/v1/chat/completions",
):
    """
    Sends a question to the Qwen model server and returns the response.
    Args:
        messages (list): A list of message dictionaries for the chat completion.
        server_url (str): The URL of the Qwen model server.
    Returns:
        str: The response from the Qwen model.
    """
    client = httpx.AsyncClient(timeout=300.0)
    payload = {
        "messages": messages
    }
    response = await client.post(server_url, json=payload)

    if response.status_code == 200:
        return response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
    else:
        print(f"Request failed with status code {response.status_code}: {response.text}")
        return None