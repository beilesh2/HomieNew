from flask import Flask, request, jsonify, render_template
import openai
import logging
import os
import sys
import base64
import io

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize OpenAI client
openai.api_key = os.getenv('OPENAI_API_KEY')
client = openai.OpenAI()

# Retrieve the assistant
assistant_id = "asst_kgpwc7dVBODphcB487klnaKe"
assistant = client.beta.assistants.retrieve(assistant_id=assistant_id)


class EventHandler(openai.AssistantEventHandler):
    def __init__(self):
        self.output = []
        super().__init__()

    def on_text_created(self, text) -> None:
        self.output.append("\nassistant > ")

    def on_text_delta(self, delta, snapshot):
        self.output.append(delta.value)

    def on_tool_call_created(self, tool_call):
        self.output.append(f"\nassistant > {tool_call.type}\n")

    def on_tool_call_delta(self, delta, snapshot):
        if delta.type == 'code_interpreter':
            self.output.append(delta.code_interpreter.input)
            self.output.append("\n\noutput >")
            for output in delta.code_interpreter.outputs:
                if output.type == "logs":
                    self.output.append(f"\n{output.logs}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():

    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data'}), 400

    # handle request input params
    user_input      = data['message'].strip()

    hasFile         = 'file' in data
    
    file_data       = data['file'] if hasFile else None
    filename        = data['filename'] if hasFile else ''
    

    # handle file
    
    if hasFile:
        # Decode the base64 string
        file_bytes = base64.b64decode(file_data)

        # Convert the bytes to a file-like object
        file_like_object = io.BytesIO(file_bytes)
        file_like_object.name = filename  # Ensure the file-like object has the filename with extension

        # Upload the file to OpenAI for use with an assistant or thread
        file_upload_response = client.files.create(
            file=file_like_object,  # Use the file-like object directly
            purpose="assistants"
        )
        file_id = file_upload_response.id

        # creating a vector store and adding this file
        vector_store = client.beta.vector_stores.create(name="User Vector Store2")

        client.beta.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store.id,
            files=[file_like_object]
        )

   
    try:

        # Create a Thread
        thread = client.beta.threads.create()

        # Add a Message to the Thread
        if hasFile: # with a file attachment
            client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=user_input,
                attachments= [
                    { "file_id": file_id, "tools": [{"type": "file_search"}] }
                ]
            )
        else:       # without a file attachment
            client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=user_input
            )
            

        # Create and Stream a Run
        event_handler = EventHandler()
        with client.beta.threads.runs.stream(
            thread_id=thread.id,
            assistant_id=assistant.id,
            instructions="",
            event_handler=event_handler
        ) as stream:
            stream.until_done()

        reply = ''.join(event_handler.output)[12:] # remove 'assitance >'
        
        return jsonify({'reply': reply})
    
    except Exception as e:
        
        logging.error(f"Error during request processing: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=8080, use_reloader=False)


    
