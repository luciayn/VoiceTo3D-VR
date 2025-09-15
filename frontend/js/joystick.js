// Joystick movement component: moves the rig based on thumbstick input on the left controller.
AFRAME.registerComponent("joystick-movement", {
    schema: { speed: { type: "number", default: 1.5 } },
    init() {
        this.joystick = { x: 0, y: 0 };
        document.querySelector("#leftHand").addEventListener("thumbstickmoved", evt => {
            this.joystick = { x: evt.detail.x, y: evt.detail.y };
        });
    },

    tick(time, deltaTime) {
        const dt = deltaTime / 1000;
        const rigEl = this.el;
        // Get the current y-axis rotation (yaw) of the rig in degrees
        const rigRotation = rigEl.getAttribute("rotation").y;
        // Input vector representing joystick input in XZ plane (horizontal movement)
        const inputVector = new THREE.Vector3(this.joystick.x, 0, this.joystick.y);
        // Quaternion to rotate inputVector by the rig’s current yaw rotation
        const quat = new THREE.Quaternion().setFromAxisAngle(
            new THREE.Vector3(0, 1, 0),
            THREE.MathUtils.degToRad(rigRotation)
        );
        // Apply rotation to inputVector and scale by speed and delta time
        inputVector.applyQuaternion(quat).multiplyScalar(this.data.speed * dt);
        // Add the resulting vector to the rig's current position (move the rig)
        rigEl.object3D.position.add(inputVector);
    }
});

// Joystick rotation component: rotates the rig based on thumbstick input on the right controller.
AFRAME.registerComponent("joystick-rotation", {
    schema: { speed: { type: "number", default: 45 } },
    init() {
        this.rotationInput = 0;
        document.querySelector("#rightHand").addEventListener("thumbstickmoved", evt => {
            this.rotationInput = evt.detail.x;
        });
    },
    tick(time, deltaTime) {
        const dt = deltaTime / 1000;
        const rigEl = document.querySelector("#rig");
        // Get current rotation of rig as an object with x, y, z properties
        let currentRotation = rigEl.getAttribute("rotation");
        // Adjust rig’s y rotation based on joystick input, speed, and delta time
        currentRotation.y -= this.rotationInput * this.data.speed * dt;
        // Apply the updated rotation back to the rig element
        rigEl.setAttribute("rotation", currentRotation);
    }
});