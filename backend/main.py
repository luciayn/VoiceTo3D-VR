import json
import time
import torch
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

from pipelines import handle_task, handle_disambiguation
from task_classifier import classify_task
from whisper import transcribe_audio

# Initialize FastAPI app
app = FastAPI()

device = "cuda" if torch.cuda.is_available() else "cpu"
# Load Whisper model for audio transcription
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
whisper_model = AutoModelForSpeechSeq2Seq.from_pretrained(
    "openai/whisper-small", # or "openai/whisper-large-v3" if you want to upgrade
    torch_dtype=torch_dtype,
    low_cpu_mem_usage=True,
    use_safetensors=True,
    cache_dir="/mnt/shared_models/huggingface/cache/hub"
).to(device)
whisper_processor = AutoProcessor.from_pretrained("openai/whisper-small", cache_dir="/mnt/shared_models/huggingface/cache/hub")
# Create pipeline with chunk processing
whisper_pipe = pipeline(
    "automatic-speech-recognition",
    model=whisper_model,
    tokenizer=whisper_processor.tokenizer,
    feature_extractor=whisper_processor.feature_extractor,
    max_new_tokens=128,
    chunk_length_s=5,  # Process in 5-second chunks
    batch_size=16,
    torch_dtype=torch_dtype,
    device=device,
    model_kwargs={
        "cache_dir": "/mnt/shared_models/huggingface/cache/hub"
    }
)


# Main function - Workflow
async def main(question, semantic_graph, nameCounters, websocket):
    clarification = ""

    # Classify the user's question
    response = await classify_task(question, semantic_graph)

    # Handle disambiguation if needed
    if response['requires_disambiguation'] or response['requires_pointing']:
        clarification = await handle_disambiguation(response, websocket)
        response = await classify_task(question, semantic_graph, clarification)
    
    # If final position is provided from disambiguation, use it
    if clarification != "" and response['final_position'] != "":
        final_position = response['final_position']
    else:
        final_position = None

    # If a final action is specified, use it as the question
    if response['final_action'] != "":
        question = response['final_action']
    
    # Handle the main task
    await handle_task(question, semantic_graph, nameCounters, final_position, websocket)
    return


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    latest_environment_data = {}
    
    while True:
        try:
            message = await websocket.receive()
            if 'text' in message:
                try:
                    data = json.loads(message['text'])
                    # Update latest environment data if received
                    if data.get("type") == "environment_data":
                        latest_environment_data = data
                    else:
                        print("Unknown text message received.")
                except Exception as e:
                    print("Error parsing JSON:", e)

            # Binary audio data
            elif 'bytes' in message:
                start_time = time.time()
                audio_data = message['bytes']

                # Transcribe audio to text
                transcription = transcribe_audio(audio_data, whisper_pipe)
                # Send transcription back
                await websocket.send_text(json.dumps({
                    "type": "transcription",
                    "transcription": transcription
                }))

                # Get semantic graph and name counters from latest environment data
                semantic_graph = latest_environment_data.get("semanticGraph")
                nameCounters = latest_environment_data.get("nameCounters")
                
                # Process the transcription and initiate the main workflow
                await main(transcription, semantic_graph, nameCounters, websocket)
                
                end_time = time.time()
                elapsed = end_time - start_time
                minutes = int(elapsed // 60)
                seconds = int(elapsed % 60)
                print(f"Total time: {minutes} mins {seconds} secs.")
            else: 
                print("Unknown message type received:", message)

        except WebSocketDisconnect:
            print("Client disconnected")
        except Exception as e:
            print(f"Error: {e}")
            break

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, ws_ping_interval=1200, ws_ping_timeout=60)