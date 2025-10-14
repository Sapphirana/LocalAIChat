import os
import json
import requests
import re
import time
import uuid
import shutil
from flask import Flask, request, jsonify, send_from_directory, Response, stream_with_context
from flask_cors import CORS

# --- Basic Setup ---
app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# --- Configuration ---
LM_STUDIO_API_URL = "http://localhost:1234/v1/chat/completions"

# --- Data Storage Setup ---
DATA_DIR = "data"
CHARACTERS_DIR = os.path.join(DATA_DIR, "characters")
CHATS_DIR = os.path.join(DATA_DIR, "chats")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CHARACTERS_DIR, exist_ok=True)
os.makedirs(CHATS_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

# --- Helper Functions ---
def sanitize_filename(name):
    """Removes special characters to create a valid filename."""
    return re.sub(r'[^a-zA-Z0-9_-]', '', name.replace(' ', '_')).lower()

# --- API Routes ---

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

# --- Character Management ---

@app.route('/api/characters', methods=['GET'])
def get_characters():
    characters = []
    for filename in sorted(os.listdir(CHARACTERS_DIR)):
        if filename.endswith(".json"):
            try:
                with open(os.path.join(CHARACTERS_DIR, filename), 'r', encoding='utf-8') as f:
                    characters.append(json.load(f))
            except (IOError, json.JSONDecodeError) as e:
                print(f"Error reading character file {filename}: {e}")
    return jsonify(characters)

@app.route('/api/characters', methods=['POST'])
def create_character():
    data = request.json
    name = data.get('name')
    description = data.get('description')
    avatar_url = data.get('avatar_url', '')

    if not name or not description:
        return jsonify({"error": "Name and description are required"}), 400

    character_id = sanitize_filename(name)
    character_filepath = os.path.join(CHARACTERS_DIR, f"{character_id}.json")
    
    if os.path.exists(character_filepath):
        return jsonify({"error": "A character with this name already exists"}), 409

    character_data = {
        "id": character_id,
        "name": name,
        "description": description,
        "avatar_url": avatar_url
    }

    try:
        with open(character_filepath, 'w', encoding='utf-8') as f:
            json.dump(character_data, f, indent=4)
        os.makedirs(os.path.join(CHATS_DIR, character_id), exist_ok=True)
    except IOError as e:
        return jsonify({"error": f"Failed to save character data: {e}"}), 500

    return jsonify(character_data), 201

@app.route('/api/characters/<character_id>', methods=['PUT'])
def update_character(character_id):
    data = request.json
    name = data.get('name')
    description = data.get('description')
    avatar_url = data.get('avatar_url', '')

    if not name or not description:
        return jsonify({"error": "Name and description are required"}), 400

    character_filepath = os.path.join(CHARACTERS_DIR, f"{character_id}.json")
    
    if not os.path.exists(character_filepath):
        return jsonify({"error": "Character not found"}), 404

    try:
        with open(character_filepath, 'r', encoding='utf-8') as f:
            character_data = json.load(f)
        
        character_data['name'] = name
        character_data['description'] = description
        character_data['avatar_url'] = avatar_url
        
        with open(character_filepath, 'w', encoding='utf-8') as f:
            json.dump(character_data, f, indent=4)
            
    except (IOError, json.JSONDecodeError) as e:
        return jsonify({"error": f"Failed to update character data: {e}"}), 500

    return jsonify(character_data), 200

@app.route('/api/characters/<character_id>', methods=['DELETE'])
def delete_character(character_id):
    try:
        character_filepath = os.path.join(CHARACTERS_DIR, f"{character_id}.json")
        if os.path.exists(character_filepath):
            os.remove(character_filepath)
        
        char_chat_dir = os.path.join(CHATS_DIR, character_id)
        if os.path.isdir(char_chat_dir):
            shutil.rmtree(char_chat_dir)
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": f"Failed to delete character: {e}"}), 500

# --- Chat Session Management ---

@app.route('/api/characters/<character_id>/chats', methods=['GET'])
def get_character_chats(character_id):
    """Lists all chat sessions for a character, sorted by newest first."""
    char_chat_dir = os.path.join(CHATS_DIR, character_id)
    if not os.path.isdir(char_chat_dir):
        return jsonify([])
    
    chat_files = [f for f in os.listdir(char_chat_dir) if f.endswith('.json')]
    chat_files.sort(key=lambda x: int(os.path.splitext(x)[0]), reverse=True)
    
    return jsonify([os.path.splitext(f)[0] for f in chat_files])

@app.route('/api/characters/<character_id>/chats', methods=['POST'])
def create_new_chat(character_id):
    """Creates a new, empty chat file for a character."""
    char_chat_dir = os.path.join(CHATS_DIR, character_id)
    os.makedirs(char_chat_dir, exist_ok=True)
    
    chat_id = str(int(time.time()))
    chat_filepath = os.path.join(char_chat_dir, f"{chat_id}.json")

    try:
        with open(chat_filepath, 'w', encoding='utf-8') as f:
            json.dump([], f)
    except IOError as e:
        return jsonify({"error": f"Could not create new chat file: {e}"}), 500
        
    return jsonify({"chat_id": chat_id}), 201

@app.route('/api/chats/<character_id>/<chat_id>', methods=['GET'])
def get_chat_history(character_id, chat_id):
    """Gets the history for a specific chat session."""
    chat_filepath = os.path.join(CHATS_DIR, character_id, f"{chat_id}.json")
    if not os.path.exists(chat_filepath):
        return jsonify({"error": "Chat history not found"}), 404
    try:
        with open(chat_filepath, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    except (IOError, json.JSONDecodeError) as e:
        return jsonify({"error": f"Failed to read chat history: {e}"}), 500

@app.route('/api/characters/<character_id>/chats/<chat_id>', methods=['DELETE'])
def delete_chat(character_id, chat_id):
    try:
        chat_filepath = os.path.join(CHATS_DIR, character_id, f"{chat_id}.json")
        if os.path.exists(chat_filepath):
            os.remove(chat_filepath)
            return jsonify({"success": True})
        return jsonify({"error": "Chat not found"}), 404
    except Exception as e:
        return jsonify({"error": f"Failed to delete chat: {e}"}), 500
    
    
@app.route('/api/chats/<character_id>/<chat_id>/delete_message', methods=['POST'])
def delete_message(character_id, chat_id):
    data = request.json
    message_index = data.get('index')

    if message_index is None:
        return jsonify({"error": "Message index is required"}), 400

    chat_filepath = os.path.join(CHATS_DIR, character_id, f"{chat_id}.json")
    if not os.path.exists(chat_filepath):
        return jsonify({"error": "Chat not found"}), 404

    try:
        with open(chat_filepath, 'r', encoding='utf-8') as f:
            history = json.load(f)

        if 0 <= message_index < len(history):
            # Simply delete the specific message without any additional logic
            del history[message_index]
        else:
            return jsonify({"error": "Invalid message index"}), 400

        with open(chat_filepath, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=4)
        
        return jsonify({"success": True, "new_history": history})

    except (IOError, json.JSONDecodeError) as e:
        return jsonify({"error": f"Failed to update chat history: {e}"}), 500


@app.route('/api/chats/<character_id>/<chat_id>/update_message', methods=['POST'])
def update_message(character_id, chat_id):
    data = request.json
    message_index = data.get('index')
    content = data.get('content')

    if message_index is None or content is None:
        return jsonify({"error": "Message index and content are required"}), 400

    chat_filepath = os.path.join(CHATS_DIR, character_id, f"{chat_id}.json")
    if not os.path.exists(chat_filepath):
        return jsonify({"error": "Chat not found"}), 404

    try:
        with open(chat_filepath, 'r', encoding='utf-8') as f:
            history = json.load(f)

        if 0 <= message_index < len(history):
            history[message_index]['content'] = content
        else:
            return jsonify({"error": "Invalid message index"}), 400

        with open(chat_filepath, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=4)
        
        return jsonify({"success": True, "new_history": history})

    except (IOError, json.JSONDecodeError) as e:
        return jsonify({"error": f"Failed to update chat history: {e}"}), 500

@app.route('/api/chats/<character_id>/<chat_id>/add_message', methods=['POST'])
def add_message(character_id, chat_id):
    data = request.json
    role = data.get('role')
    content = data.get('content')

    if not role or not content:
        return jsonify({"error": "Role and content are required"}), 400

    chat_filepath = os.path.join(CHATS_DIR, character_id, f"{chat_id}.json")
    if not os.path.exists(chat_filepath):
        return jsonify({"error": "Chat not found"}), 404

    try:
        with open(chat_filepath, 'r', encoding='utf-8') as f:
            history = json.load(f)

        history.append({"role": role, "content": content})

        with open(chat_filepath, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=4)
        
        return jsonify({"success": True, "new_history": history})

    except (IOError, json.JSONDecodeError) as e:
        return jsonify({"error": f"Failed to update chat history: {e}"}), 500

# --- Streaming Chat Endpoint ---
# --- Streaming Chat Endpoint ---

@app.route('/api/chat/stream', methods=['POST'])
def handle_streaming_chat():
    data = request.json
    character_id = data.get('character_id')
    chat_id = data.get('chat_id')
    user_message = data.get('message')
    history_override = data.get('history_override') # Get history_override from frontend
    mode = data.get('mode', 'chat')
    user_persona = data.get('user_persona', 'The user you are talking to.')
    llm_settings = data.get('llm_settings', {})
    system_prompt = data.get('system_prompt', '') # Get system prompt from frontend if sent, otherwise build it

    if not all([character_id, chat_id, user_message]):
        return jsonify({"error": "Character ID, Chat ID, and message are required"}), 400

    try:
        with open(os.path.join(CHARACTERS_DIR, f"{character_id}.json"), 'r', encoding='utf-8') as f:
            character = json.load(f)
    except FileNotFoundError:
        return jsonify({"error": "Character data not found."}), 404

    # Determine history source
    if history_override is not None:
        # Use the history provided by the frontend (for regeneration)
        history = history_override
        regenerate_index = len(history_override) # The index where the new AI response will go
        print(f"Regenerating: Using history_override. New message index will be {regenerate_index}")
    else:
        # Load history from file (normal chat)
        chat_filepath = os.path.join(CHATS_DIR, character_id, f"{chat_id}.json")
        try:
            with open(chat_filepath, 'r', encoding='utf-8') as f:
                history = json.load(f)
            regenerate_index = None # Not regenerating
            print(f"Normal chat: Loaded history from {chat_filepath}")
        except FileNotFoundError:
            return jsonify({"error": "Chat history not found."}), 404

    # Build the system prompt if not provided explicitly (e.g., for regeneration where it's context-dependent)
    if not system_prompt:
        system_prompt = (
            f"This is a conversation between you, {character['name']}, and a user. "
            f"Your persona: {character['description']}. "
            f"The user's persona: {user_persona}. "
        )
        if mode == 'chat':
            system_prompt += "Respond naturally and conversationally as your character. Stay in character at all times."
        else:
            system_prompt += "You are in instruct mode. Follow the user's instructions precisely while embodying your character's personality."

    messages_for_api = [{"role": "system", "content": system_prompt}]
    messages_for_api.extend(history)
    messages_for_api.append({"role": "user", "content": user_message})

    api_payload = {
        "model": "local-model",
        "messages": messages_for_api,
        "temperature": llm_settings.get('temperature', 0.7),
        "repeat_penalty": llm_settings.get('repetition_penalty', 1.1),
        "top_p": llm_settings.get('min_p', 0.95),
        "stream": True
    }

    def generate():
        try:
            response = requests.post(
                LM_STUDIO_API_URL,
                json=api_payload,
                stream=True,
                timeout=300
            )

            if response.status_code != 200:
                yield f"data: {json.dumps({'type': 'error', 'content': f'API Error: {response.status_code}'})}\n\n"
                return

            full_content = ""
            for line in response.iter_lines():
                if line:
                    try:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith("data: "):
                            data_json = decoded_line[6:]

                            if data_json == '[DONE]':
                                break

                            chunk_data = json.loads(data_json)
                            content = chunk_data.get('choices', [{}])[0].get('delta', {}).get('content', '')

                            if content:
                                full_content += content
                                yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"

                    except Exception as e:
                        print(f"Error processing streaming data: {e}")

            # --- POST-STREAMING LOGIC ---
            chat_filepath = os.path.join(CHATS_DIR, character_id, f"{chat_id}.json")

            if regenerate_index is not None:
                # We are regenerating, so load the CURRENT file history to update it
                try:
                    with open(chat_filepath, 'r', encoding='utf-8') as f:
                        current_file_history = json.load(f)
                    print(f"Regenerating: Loaded current file history, length: {len(current_file_history)}")
                    print(f"Regenerating: Attempting to replace message at index {regenerate_index}")
                    # Replace the message at the specific index with the new content
                    # Ensure the index is valid within the current file history
                    if 0 <= regenerate_index < len(current_file_history):
                        # Assuming the regenerated message should be an assistant message
                        current_file_history[regenerate_index] = {"role": "assistant", "content": full_content}
                        print(f"Regenerating: Successfully replaced message at index {regenerate_index}")
                    else:
                        print(f"Regenerating: Index {regenerate_index} is out of bounds for current file history.")
                        # Potentially log an error or handle this case differently if needed
                        # For now, just append if index is invalid
                        current_file_history.append({"role": "assistant", "content": full_content})

                    # Save the updated history back to the file
                    with open(chat_filepath, 'w', encoding='utf-8') as f:
                        json.dump(current_file_history, f, indent=4)
                    print(f"Regenerating: Saved updated history to {chat_filepath}")

                except FileNotFoundError:
                    print(f"Regenerating: Chat file {chat_filepath} not found during save.")
                    # This shouldn't happen if we got this far, but handle it gracefully
                    return
                except Exception as e:
                    print(f"Regenerating: Error saving final message to file: {e}")
                    # Yield an error to the frontend?
                    # yield f"data: {json.dumps({'type': 'error', 'content': f'Error saving: {e}'})}\n\n"
                    return # Stop execution on save error

            else:
                # Normal chat, append user and assistant messages to the loaded history
                try:
                    history.append({"role": "user", "content": user_message})
                    history.append({"role": "assistant", "content": full_content})

                    with open(chat_filepath, 'w', encoding='utf-8') as f:
                        json.dump(history, f, indent=4)
                    print(f"Normal chat: Saved updated history to {chat_filepath}")
                except Exception as e:
                    print(f"Normal chat: Error saving final message: {e}")
                    # Yield an error to the frontend?
                    # yield f"data: {json.dumps({'type': 'error', 'content': f'Error saving: {e}'})}\n\n"
                    return # Stop execution on save error

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            error_msg = str(e)
            print(f"Streaming Error: {error_msg}")
            yield f"data: {json.dumps({'type': 'error', 'content': f'Streaming Error: {error_msg}'})}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')


# --- Regular Chat Endpoint (non-streaming) ---

@app.route('/api/chat', methods=['POST'])
def handle_chat():
    data = request.json
    character_id = data.get('character_id')
    chat_id = data.get('chat_id')
    user_message = data.get('message')
    history_override = data.get('history_override')
    mode = data.get('mode', 'chat')
    user_persona = data.get('user_persona', 'The user you are talking to.')
    llm_settings = data.get('llm_settings', {})
    
    if not all([character_id, chat_id, user_message]):
        return jsonify({"error": "Character ID, Chat ID, and message are required"}), 400

    try:
        with open(os.path.join(CHARACTERS_DIR, f"{character_id}.json"), 'r', encoding='utf-8') as f:
            character = json.load(f)
    except FileNotFoundError:
        return jsonify({"error": "Character data not found."}), 404

    chat_filepath = os.path.join(CHATS_DIR, character_id, f"{chat_id}.json")
    if history_override is not None:
        history = history_override
    else:
        try:
            with open(chat_filepath, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except FileNotFoundError:
            return jsonify({"error": "Chat history not found."}), 404

    system_prompt = (
        f"This is a conversation between you, {character['name']}, and a user. "
        f"Your persona: {character['description']}. "
        f"The user's persona: {user_persona}. "
    )
    if mode == 'chat':
        system_prompt += "Respond naturally and conversationally as your character. Stay in character at all times."
    else:
        system_prompt += "You are in instruct mode. Follow the user's instructions precisely while embodying your character's personality."

    messages_for_api = [{"role": "system", "content": system_prompt}]
    messages_for_api.extend(history)
    messages_for_api.append({"role": "user", "content": user_message})

    api_payload = {
        "model": "local-model",
        "messages": messages_for_api,
        "temperature": llm_settings.get('temperature', 0.7),
        "repeat_penalty": llm_settings.get('repetition_penalty', 1.1),
        "top_p": llm_settings.get('min_p', 0.95),
        "stream": False
    }

    try:
        response = requests.post(LM_STUDIO_API_URL, json=api_payload, timeout=300)
        response.raise_for_status()
        ai_message = response.json()['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Could not connect to LM Studio API: {e}"}), 500
    except (KeyError, IndexError) as e:
        return jsonify({"error": f"Unexpected API response format: {e}"}), 500

    if history_override is None:
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": ai_message})
        try:
            with open(chat_filepath, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=4)
        except IOError as e:
            print(f"Error saving chat history for {character_id}/{chat_id}: {e}")

    return jsonify({"reply": ai_message})

# --- Image Upload ---

@app.route('/api/upload-image', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No image selected"}), 400
    
    if file:
        _, ext = os.path.splitext(file.filename)
        filename = f"{uuid.uuid4()}{ext}"
        file_path = os.path.join(UPLOADS_DIR, filename)
        file.save(file_path)
        return jsonify({"url": f"/data/uploads/{filename}"})
    
    return jsonify({"error": "Failed to upload image"}), 500

@app.route('/data/uploads/<path:filename>')
def serve_uploaded_file(filename):
    try:
        return send_from_directory(UPLOADS_DIR, filename)
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404

# --- Main Execution ---
if __name__ == '__main__':
    print("--- Local AI Chat Server ---")
    print("Access the web UI at: http://127.0.0.1:5500")
    print("Make sure LM Studio is running on port 1234")
    print("---------------------------------")
    app.run(host='0.0.0.0', port=5500, debug=False)
