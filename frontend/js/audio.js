// Audio context for capturing microphone input
let audioContext;
let recordedChunks = [];
let mediaStream;
let isRecording = false;
const SAMPLE_RATE = 16000; // 16kHz sample rate

// Start recording audio
async function startRecording() {
    try {
        // Update UI
        statusElement.textContent = 'Listening... (click to stop)';
        micButton.classList.add('listening');
        micButton.textContent = 'Stop Listening';
        isRecording = true;
        
        // Get microphone access
        mediaStream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
                sampleRate: SAMPLE_RATE,
                echoCancellation: true,
                noiseSuppression: true
            }
        });
        
        // Set up audio context
        audioContext = new (window.AudioContext || window.webkitAudioContext)({
        sampleRate: SAMPLE_RATE
        });
        
        // Load and add the audio processor module
        try {
            await audioContext.audioWorklet.addModule('js/audio-processor.js');
            console.log('AudioWorklet processor loaded');
        } catch (error) {
            console.error('Error loading AudioWorklet:', error);
            statusElement.textContent = 'Error initializing audio';
            stopRecording();
            return;
        }
        
        // Create a source node from the microphone stream
        const source = audioContext.createMediaStreamSource(mediaStream);
        const processor = new AudioWorkletNode(audioContext, 'audio-processor');
        
        // Handle audio data from the processor
        processor.port.onmessage = (event) => {
        if (isRecording) {
            const audioData = new Float32Array(event.data);
            recordedChunks.push(audioData);
        }
        };
        
        // Connect source node to processor
        source.connect(processor);
        console.log('Recording started');
    } catch (error) {
        console.error('Error starting recording:', error);
        statusElement.textContent = 'Error: ' + error.message;
        micButton.classList.remove('listening');
        micButton.textContent = 'Start Listening';
        isRecording = false;
    }
    }

    // Stop recording
    function stopRecording() {
    if (mediaStream) {
        mediaStream.getTracks().forEach(track => track.stop());
        mediaStream = null;
    }
    if (audioContext) {
        audioContext.close().then(() => {
        audioContext = null;
        console.log('Audio context closed');

        // Combine all chunks into one Float32Array
        if (recordedChunks.length > 0 && wsConnection.readyState === WebSocket.OPEN) {
            const length = recordedChunks.reduce((sum, chunk) => sum + chunk.length, 0);
            const merged = new Float32Array(length);
            let offset = 0;
            for (const chunk of recordedChunks) {
            merged.set(chunk, offset);
            offset += chunk.length;
            }

            // Send merged audio to server
            wsConnection.send(merged.buffer);
            console.log('Sent complete recording to server');
        }
        // Clear buffer for next recording
        recordedChunks = [];
        });
    }

    // Update UI
    isRecording = false;
    statusElement.textContent = 'Connected to server';
    micButton.classList.remove('listening');
    micButton.textContent = 'Start Listening';
    console.log('Recording stopped');
    }

// Toggle recording
function toggleRecording() {
    // Check WebSocket connection before recording
    if (wsConnection.readyState !== WebSocket.OPEN) {
        statusElement.textContent = 'Reconnecting...';
        connectWebSocket();
        return;
    }

    // Start or stop recording based on current state
    if (isRecording) {
        stopRecording();
    } else {
        startRecording();
    }
}