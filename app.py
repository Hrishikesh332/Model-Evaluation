from flask import Flask, render_template, request, jsonify
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/connect', methods=['POST'])
def connect_api():
    api_key = request.json.get('api_key')

    if api_key and len(api_key) > 0:
        return jsonify({"status": "success", "message": "API key connected successfully"})
    else:
        return jsonify({"status": "error", "message": "Invalid API key"}), 400

@app.route('/api/projects', methods=['GET'])
def get_projects():
    sample_projects = [
        {"id": "project1", "name": "Hybe_New", "url": "https://playground.twelvelabs.io/indexes/67900e1181c61d781369699f"},
        {"id": "project2", "name": "Talent Show", "url": "https://playground.twelvelabs.io/indexes/12345"},
        {"id": "project3", "name": "Music Videos", "url": "https://playground.twelvelabs.io/indexes/67890"}
    ]
    
    return jsonify({"status": "success", "projects": sample_projects})

@app.route('/api/search', methods=['POST'])
def search_videos():
    query = request.json.get('query')

    return jsonify({
        "status": "success", 
        "message": f"Received search query: {query}"
    })

@app.route('/api/project/create', methods=['POST'])
def create_project():
    project_name = request.form.get('project_name')

    if 'video' not in request.files:
        return jsonify({"status": "error", "message": "No video file uploaded"}), 400
        
    video_file = request.files['video']
    
    if video_file.filename == '':
        return jsonify({"status": "error", "message": "No video file selected"}), 400
    
    if video_file:
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], video_file.filename)
        video_file.save(video_path)
    
        
        return jsonify({
            "status": "success",
            "message": f"Project '{project_name}' created successfully",
            "project": {
                "id": f"project_{len(os.listdir(app.config['UPLOAD_FOLDER']))}",
                "name": project_name,
                "url": "#"
            }
        })
    
    return jsonify({"status": "error", "message": "Failed to process video"}), 500

if __name__ == '__main__':
    app.run(debug=True)