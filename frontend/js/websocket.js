// WebSocket connection and event handling for real-time communication with the server
let wsConnection;

const statusElement = document.getElementById('status');
const micButton = document.getElementById('mic-button');
const transcriptionElement = document.getElementById('transcription');

// Connect to WebSocket server
function connectWebSocket() {
    // Server address
    const wsUrl = 'ws://localhost:8000/ws';

    // Create WebSocket connection
    wsConnection = new WebSocket(wsUrl);

    // Event handler for connection open
    wsConnection.onopen = () => {
        statusElement.textContent = 'Connected to server';
        micButton.disabled = false;
        console.log('WebSocket connection established');
    };

    // Event handler for connection close
    wsConnection.onclose = () => {
        statusElement.textContent = 'Disconnected from server';
        micButton.disabled = true;
        micButton.classList.remove('listening');
        if (isRecording) stopRecording();
        console.log('WebSocket connection closed');
        // Auto-reconnect after 3 seconds
        setTimeout(() => {
            console.log('Attempting to reconnect...');
            connectWebSocket();
        }, 3000);
    };

    // Error handling
    wsConnection.onerror = (error) => {
        console.error('WebSocket error:', error);
        statusElement.textContent = 'Connection error';
        micButton.disabled = true;
    };

    // Event handler for incoming messages
    wsConnection.addEventListener("message", event => {
        const data = JSON.parse(event.data);

        // Transcription received from server
        if (data.type === "transcription") {
            const transcription = data.transcription;
            // Update UI with transcription
            transcriptionElement.textContent = transcription;
            console.log('Received transcription:', transcription);
        }

        // Calculate world position based on reference object
        if (data.type === "calculate_position") {
            // Extract parameters from message
            const reference_id = data.reference_id;
            const direction = data.direction;
            const distance = data.distance;
            let referenceEl;
            referenceEl = document.getElementById(reference_id);
            // Calculate world position
            const worldPos = getOffsetPosition(referenceEl, direction, distance);
            console.log('Calculated world position:', worldPos);
            const message = {
                type: 'world_position',
                position: worldPos
        };
        // Send world position back to server
        wsConnection.send(JSON.stringify(message));
        }

        // Add, update, or delete 3D models in the scene
        if (data.type === "new_model") {
            const model = data.model;
            // Check if model with the same ID already exists
            const existingModel = document.getElementById(model.id);
        if (existingModel) {
            console.log("Updating model...");
            deleteModelInScene(existingModel);
            addModelToScene(model);
        } else {
            console.log("Adding new model...")
            addModelToScene(model);
            loadedModels.add(model.id);
        }
        }

        if (data.type === "delete_object") {
            const objectId = data.object_id;
            const existingModel = document.getElementById(objectId);
        if (existingModel) {
            console.log("Deleting model...");
            deleteModelInScene(existingModel);
        }
        }

        // Handle pointing mode initiation for object or location
        if (data.type === "start_pointing_object") {
            // Prompt user to point to the specified object
            text = `Please point to the object you are referring to by ${data.disambiguation_phrase} from the following candidates: ${data.disambiguation_candidates}.`;
            console.log(text);
            pointingType = "object";
            enablePointingMode(text);
        }
        if (data.type === "start_pointing_location") {
            // Prompt user to point to the specified location
            text = `Please point to the location you are referring to by ${data.spatial_phrase}.`;
            console.log(text);
            pointingType = "location";
            enablePointingMode(text);
        }
    });
}