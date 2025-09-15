let pointingActive = false;
let pointingType = null;
const rightHand = document.querySelector('#rightHand');
const vrInstructions = document.querySelector('#pointing-instructions-text');

// Calculates the offset position from a reference element in a given direction
// Used to determine where to place new objects relative to the user or others
function getOffsetPosition(referenceEl, direction, distance = 1) {
    // Step 1: Get current world position of the reference object (user or other object)
    const refWorldPos = new THREE.Vector3();
    referenceEl.object3D.getWorldPosition(refWorldPos);
    console.log("Reference world position:", refWorldPos);

    // Step 2: Get current world rotation (quaternion) of the reference object
    const refQuat = new THREE.Quaternion();
    referenceEl.object3D.getWorldQuaternion(refQuat);
    console.log("Reference world quaternion:", refQuat);

    // Step 3: Create an offset vector in local space depending on direction
    const offset = new THREE.Vector3();
    switch (direction) {
        case 'front':
            offset.set(0, 0, referenceEl.id === 'user' ? -distance : distance);
            break;
        case 'back':
            offset.set(0, 0, referenceEl.id === 'user' ? distance : -distance);
            break;
        case 'right':
            offset.set(distance, 0, 0);
            break;
        case 'left':
            offset.set(-distance, 0, 0);
            break;
        case 'up':
            offset.set(0, distance, 0);
            break;
        case 'down':
            offset.set(0, -distance, 0);
            break;
    }

    // Step 4: Rotate the offset vector from local to world space
    offset.applyQuaternion(refQuat);

    // Step 5: Add the rotated offset to the world position
    refWorldPos.add(offset);

    // Ensure the new position is above ground level (y >= 0.5)
    if (referenceEl.id === 'user') {
        refWorldPos.y = 0.5;
    }
    else{
        if (refWorldPos.y < 0.5) {
        refWorldPos.y = 0.5; // Ensure objects are above ground
        }
    }

    // Step 6: Return plain x, y, z values
    return `${refWorldPos.x} ${refWorldPos.y} ${refWorldPos.z}`;
}

// Builds a semantic graph representation of all visible scene objects and the user
// This structure is sent to the backend for contextual understanding
function getSemanticGraph(objectEls, cameraEl) {
    const graph = [];

    // Add camera/user node
    const userPos = cameraEl.getAttribute('position');

    graph.push({
        id: 'user',
        name: 'user',
        color: 'none',
        position: userPos
    });

    // Add all objects
    Array.from(objectEls).forEach(el => {
        const semanticNode = el.getAttribute('semantic-node');
        if (!semanticNode) return;
        const [name, color] = semanticNode.split(';').map(s => s.split(':')[1].trim());

        graph.push({
            id: el.id,
            name: name,
            color: color,
            position: el.getAttribute('position'),
            rotation: el.getAttribute('rotation')
        });
    });

    // console.log("Semantic Graph:", JSON.stringify(graph, null, 2));
    return graph;
}

// Determines which objects are visible from the camera's perspective using raycasting
function getVisibleObjects(cameraEl, objectEls) {
    const cameraPos = new THREE.Vector3();
    const cameraDir = new THREE.Vector3();
    const raycaster = new THREE.Raycaster();

    cameraEl.object3D.getWorldPosition(cameraPos);
    cameraEl.object3D.getWorldDirection(cameraDir);

    const visibleObjects = [];

    objectEls.forEach(el => {
        const pos = new THREE.Vector3();
        el.object3D.getWorldPosition(pos);
        const toObj = new THREE.Vector3().subVectors(pos, cameraPos).normalize();

        // Check if the object is in front of the camera
        // If the dot product is positive, the object is behind the camera (skipping it) -> Camera direction is positive (0 0 1)
        if (cameraDir.dot(toObj) > 0) {return};

        // Cast a ray from the camera to the object
        raycaster.set(cameraPos, toObj);
        const intersections = raycaster.intersectObject(el.object3D, true);

        // If the ray intersects the object, add it to the visible objects
        if (intersections.length > 0) {
            visibleObjects.push(el);
        }
    });
    // console.log("Visible Objects:", visibleObjects.map(el => el.id));
    return visibleObjects;
}

// Generates unique IDs to objects based on their semantic name and keeps a count
// This avoids duplicate IDs when multiple objects share the same name
function generatedId(objectEls) {
    const nameCounters = {};
    objectEls.forEach(el => {
        const semanticNode = el.getAttribute('semantic-node');
        if (!semanticNode) return;
        const [name, color] = semanticNode.split(';').map(s => s.split(':')[1].trim());
        
        // Initialize counter for this name if not already done
        if (!nameCounters[name]) {
            nameCounters[name] = 0;
        }
        // Increment the counter and assign a new ID
        nameCounters[name]++;
        el.id = `${name}${nameCounters[name]}`;
    });
    return nameCounters;
    };

// Send environment data to the server
function sendEnvironmentData(semanticGraph, nameCounters) {
    const message = {
        type: 'environment_data',
        semanticGraph: semanticGraph,
        nameCounters: nameCounters
    };

    if (wsConnection.readyState === WebSocket.OPEN) {
        wsConnection.send(JSON.stringify(message));
    } else {
        console.warn("WebSocket is not open.");
    }
}
    
// Backend triggers pointing mode
function enablePointingMode(customText) {
    pointingActive = true;
    // Enable raycaster on right hand
    rightHand.setAttribute('raycaster', 'enabled', true);
    // Show instructions in VR
    vrInstructions.setAttribute('text', 'value', customText);
    vrInstructions.setAttribute('visible', true);
    console.log("Pointing mode enabled - waiting for user click");
}

// Backend stops pointing mode
function disablePointingMode() {
    pointingActive = false;
    // Disable raycaster on right hand
    rightHand.setAttribute('raycaster', 'enabled', false);
    // Hide in VR
    vrInstructions.setAttribute('visible', false);
    console.log("Pointing mode disabled");
}

// User clicks (or presses trigger) to select object or location
document.querySelector('#rightHand').addEventListener('triggerdown', function () {
    if (!pointingActive) return;
    console.log("Right controller clicked!");
    const raycaster = rightHand.components.raycaster;
    const intersects = raycaster.intersections;

    // Check for intersections with objects
    if (intersects.length > 0) {
        // Get the closest intersected object
        const firstHit = intersects[0];
        const hitEl = firstHit.object.el;

        if (hitEl && hitEl.hasAttribute('semantic-node')) {
            // Object hit
            const position = hitEl.object3D.getWorldPosition(new THREE.Vector3());
            // Send message to backend
            const message = {
                type: (pointingType === 'object') ? 'pointing_object' : 'pointing_location',
                position: { x: position.x, y: position.y + 0.4, z: position.z },
                object_id: hitEl.id
            };
            wsConnection.send(JSON.stringify(message));
            console.log("Sent pointing object message");
            console.log("Selected object:", message);
        }
        else if (hitEl && hitEl.id === 'ground') {
        // Location hit
        const point = firstHit.point;
        // Send message to backend
        const message = {
            type: 'pointing_location',
            position: { x: point.x, y: 0, z: point.z }
        };
        wsConnection.send(JSON.stringify(message));
        console.log("Selected location:", message);
        }
    } else {
        console.log("No target hit");
    }
    disablePointingMode();
});

// Continuously updates and sends the environment state to the backend
AFRAME.registerComponent('update-environment', {
    init() {
        this.camera = document.querySelector('#camera');
        this.camera.id = 'user';
        this.camera.name = 'user';
        this.camera.color = 'none';

        this.ready = false;
        document.querySelector('a-scene').addEventListener('all-models-loaded', () => {
        this.ready = true;
        console.log('All models loaded.');
        });
    },

    tick() {
        if (!this.ready) return; // Skip until ready
        const cameraPos = new THREE.Vector3();
        this.camera.object3D.getWorldPosition(cameraPos);
        const scene = document.querySelector('a-scene');
        const objectEls = scene.querySelectorAll('[id][semantic-node]');
        nameCounters = generatedId(objectEls);
        const visibleObjects = getVisibleObjects(this.camera, objectEls);
        semanticGraph = getSemanticGraph(visibleObjects, this.camera);
        sendEnvironmentData(semanticGraph, nameCounters);
    }
});