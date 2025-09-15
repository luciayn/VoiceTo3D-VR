class AudioProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        this.buffer = [];
        this.bufferSize = 16000 * 5; // 5 seconds buffer (16000 samples/sec * 5 sec)
    }
    process(inputs) {
        const input = inputs[0];
        if (input && input.length > 0) {
            const audioData = input[0];
            
            // Add new samples to buffer
            this.buffer.push(...audioData);

            // If buffer exceeds the defined size, send a chunk to the main thread
            const chunk = this.buffer.slice(0, this.bufferSize);
            this.buffer = this.buffer.slice(this.bufferSize);
            this.port.postMessage(chunk);
        }
        return true;
    }
}
registerProcessor('audio-processor', AudioProcessor);