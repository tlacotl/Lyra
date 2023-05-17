import json
import openai
import os

os.system("cls")

# Set your API key
openai.api_key = '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'

# Define the conversation history file path
conversation_history_file = "conversation_history.json"

# Define the directory for storing output code files
code_dir = "output_code"

# Create the directory if it doesn't exist
if not os.path.exists(code_dir):
    os.makedirs(code_dir)

# Load conversation history from file if it exists
try:
    with open(conversation_history_file, "r") as file:
        conversation_history = json.load(file)
except FileNotFoundError:
    conversation_history = []

def count_tokens(message):
    return len(openai.api.encoding.encode(message))

# Define a maximum number of tokens for a conversation
max_tokens = 4000

while True:
    # Get user input
    user_input = input("You: ")

    # Break the loop if the user says 'quit'
    if user_input.lower() == "quit":
        break

    # Input validation
    if not user_input.strip():
        print("Please enter a valid input.")
        continue

    # Append the user input to the conversation history
    conversation_history.append({"role": "user", "content": user_input})

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=conversation_history[-max_tokens:]
        )

        response_text = response.choices[0].message.content.strip()

        # If the response is a code block, write it to a file
        if response_text.startswith("```") and response_text.endswith("```"):
            # Remove the backticks and extract the code
            code = response_text[3:-3]

            # Create a unique filename for the code file
            code_file = os.path.join(code_dir, f"code_{len(os.listdir(code_dir)) + 1}.txt")

            # Write the code to the file
            with open(code_file, "w") as file:
                file.write(code)

            # Replace the response text with the file path
            response_text = f"I have written the code to a file: {code_file}"

        print("Lyra: " + response_text)

        # Append the AI's response to the conversation history
        conversation_history.append({"role": "assistant", "content": response_text})

        # Reduce conversation history to the last N tokens, keeping important messages
        important_messages = [msg for msg in conversation_history if 'important' in msg['content']]
        tokens_to_keep = max_tokens - sum(count_tokens(msg['content']) for msg in important_messages)
        new_history = important_messages

        for message in reversed(conversation_history):
            if count_tokens(message['content']) <= tokens_to_keep:
                new_history.append(message)
                tokens_to_keep -= count_tokens(message['content'])
                
        conversation_history = list(reversed(new_history))

    except Exception as e:
        print("Uh oh!:", str(e))

    # Save conversation history to file
    with open(conversation_history_file, "w") as file:
        json.dump(conversation_history, file)
