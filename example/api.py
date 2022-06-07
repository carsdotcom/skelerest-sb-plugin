import json
import sys
from flask import Flask, jsonify, request

app = Flask(__name__)
app.config["DEBUG"] = True

notes = {
    "1": "Finish Writing Code",
    "2": "Go to the Store",
    "3": "Mow the Lawn"
}

index = 4

@app.route('/notes', methods=['GET'])
def get_notes():
    global notes

    print(f"{request.method}: {request.url}", file=sys.stderr)
    print(f"HEADERS:\n{request.headers}", file=sys.stderr)
    return {'notes': notes}, 200

@app.route('/notes', methods=['POST'])
def create_note():
    global notes
    global index

    print(f"{request.method}: {request.url}", file=sys.stderr)
    print(f"HEADERS:\n{request.headers}", file=sys.stderr)
    print(f"BODY:\n{request.json}", file=sys.stderr)

    print(request.is_json, file=sys.stderr)
    data = request.get_json()
    notes[str(index)] = data["note"]
    index += 1

    return "", 201

@app.route('/notes/<id>', methods=['PUT'])
def update_note(id):
    global notes

    print(f"{request.method}: {request.url}", file=sys.stderr)
    print(f"ID: {id}", file=sys.stderr)
    print(f"HEADERS:\n{request.headers}", file=sys.stderr)
    print(f"BODY:\n{request.json}", file=sys.stderr)

    print(request.is_json, file=sys.stderr)
    data = request.get_json()
    notes[str(id)] = data["note"]

    return "", 201

@app.route('/notes/<id>', methods=['DELETE'])
def delete_note(id):
    global notes

    print(f"{request.method}: {request.url}", file=sys.stderr)
    print(f"ID: {id}", file=sys.stderr)
    print(f"HEADERS:\n{request.headers}")

    del notes[str(id)]

    return "", 200

app.run(host="0.0.0.0")
