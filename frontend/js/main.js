// Initialize
document.addEventListener('DOMContentLoaded', () => {
    const micButton = document.getElementById('mic-button');
    // Set up mic button
    micButton.addEventListener('click', toggleRecording);
    micButton.disabled = true;

    // Connect to WebSocket server
    connectWebSocket();

    // Load models after the scene initializes
    document.querySelector('a-scene').addEventListener('loaded', () => {
        loadInitialModels();
    });
});