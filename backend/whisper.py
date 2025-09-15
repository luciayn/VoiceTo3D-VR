import numpy as np

def transcribe_audio(audio_data, pipe):
    """
    Transcribe audio data using the Whisper model.
    
    Args:
        audio_data (list or bytes): Audio data in float32 format.
        
    Returns:
        str: Transcription of the audio.
    """
    audio_buffer = np.array([], dtype=np.float32)

    # Convert to numpy array based on input type
    if isinstance(audio_data, list):
        # If it's a list, convert directly to numpy array
        audio_chunk = np.array(audio_data, dtype=np.float32)
    else:
        # If it's bytes, use frombuffer
        audio_chunk = np.frombuffer(audio_data, dtype=np.float32)

    audio_buffer = np.concatenate([audio_buffer, audio_chunk])

    # Process with pipeline
    result = pipe(audio_buffer, return_timestamps=False)
    transcription = result["text"]
    print("Transcription:", transcription)    
    return transcription