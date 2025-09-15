HTML_BASE = """
<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>3D Model Viewer</title>
        <script src="https://cdn.jsdelivr.net/npm/@google/model-viewer@3.1.1/dist/model-viewer.min.js" type="module"></script>
        <style>
            body {{
                margin: 0;
                overflow: hidden;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                background-color: #ffffff;
            }}

            model-viewer{{
                width: 100vw;
                height: 100vh;
            }}
        </style>
    </head>
<body>
    <!-- 3D Model Viewer -->
    <model-viewer 
        id="modelViewer"
        camera-controls
        auto-rotate
        environment-intensity="1.5"
        exposure="1.2"
        shadow-intensity="1"
        disable-zoom
        ar
        ar-modes="webxr scene-viewer quick-look">
    </model-viewer>
    <script>
        // Convert base64 model to a Blob URL and load it
        const glbData = "data:model/gltf-binary;base64,{MODEL_DATA}";
        document.getElementById('modelViewer').setAttribute('src', glbData);
    </script>
</body>
</html>
"""