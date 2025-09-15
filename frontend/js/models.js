const loadedModels = new Set()
let loadedModelsCount = 0
let totalModels = 0

function loadInitialModels() {
    // Fetch the models.json file and add each model to the scene
    fetch("../../data/models.json")
        .then(response => response.json())
        .then(models => {
        totalModels = models.length;
        models.forEach(model => {
            // Avoid adding duplicate models
            if (!loadedModels.has(model.id)) {
                addModelToScene(model);
                loadedModelsCount++;
                // Check if all models are loaded
                if (loadedModelsCount === totalModels) {
                    document.querySelector('a-scene').dispatchEvent(new Event('all-models-loaded'));
                }
                loadedModels.add(model.id);
            }
        });
    });
}

// Add 3D model to the A-Frame scene
function addModelToScene(model) {
    const entity = document.createElement("a-entity");
    entity.setAttribute("id", model.id);
    entity.setAttribute("position", model.position);
    entity.setAttribute("rotation", model.rotation);
    entity.setAttribute("gltf-model", model.path);
    entity.setAttribute("mixin", "model");
    entity.setAttribute("semantic-node", `name: ${model.name}; color: ${model.color}`);
    document.querySelector("a-scene").appendChild(entity);
}

// Remove 3D model from the A-Frame scene
function deleteModelInScene(model) {
    // Find and remove the entity from the scene
    const oldEntity = document.getElementById(model.id);
    if (oldEntity) {
        oldEntity.parentNode.removeChild(oldEntity);
        loadedModels.delete(model.id);
    }
}
