from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

coordinates_storage = {}

#updates the storage with most recent coordinates sent from the llm chain
@app.route('/update_coordinates', methods=['POST'])
def update_coordinates():
    global coordinates_storage
    coordinates = request.json
    coordinates_storage = coordinates
    print(coordinates_storage)
    return jsonify({"status": "success"}), 200

#sends the coordinates to frontend whenever a request is made 
@app.route('/get_coordinates', methods=['GET'])
def get_coordinates():
    global coordinates_storage
    return jsonify(coordinates_storage), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
