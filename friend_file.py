import os
import json
import config
import logos
import openai
import shutil
import documents as doc
from math import ceil
from logos import dye
from os import chdir, write, listdir
from pathlib import Path
from base64 import b64decode
from time import sleep, time


# Define global variables
key = ''
commands = ['gpt', 'chat', 'dalle', 'help', 'quit']
break_commands = [commands[-1], 'q', 'goodbye', 'exit']
config_data = config.read_config()['open_ai']

# PATHS
KEY_LOC = f'C:\\Users\\{doc.usr}\\Desktop\\D-Pad LLC\\keys'
AI_FOLDER = f'C:\\Users\\{doc.usr}\\Desktop\\D-Pad LLC\\Art\\AI Generartions'
PROMPT_TEMPLATES = f'C:\\Users\\{doc.usr}\\Desktop\\D-Pad LLC\\GPT\\prompts'
CONV_HIS = f'C:\\Users\\{doc.usr}\\Desktop\\D-Pad LLC\\GPT\\old_conversations'
ROOT = Path.cwd()
DATA_DIR = ROOT / 'responses'
DATA_DIR.mkdir(exist_ok=True)
if not os.path.exists(AI_FOLDER):
    os.mkdir(AI_FOLDER)

# Text strings
GREETING = f'Use "help" for options.'

gpt_help_string = [["red", f"\n{'=' * 60}"],
["magenta", "Enter two dashes followed by one of the commands"],
["magenta", "Ex: --resume web_app"],
["red", "=" * 60],
["cyan", "test   - Generates test responses instead of"],
["cyan", "         submitting actual GPT requests.\n"],
["cyan", "clear  - Clears the conversation and starts over.\n"],
["cyan", "resume - Resumes the last conversation. Add a second argument to"],
["cyan", "         resume a saved conversation if it exists.\n"],
["cyan", "prompt - Use a prewritten prompt to initialize a conversation"],
["cyan", "         if the prompt exists.\n"],
["cyan", "save   - Saves the current conversation."],
["cyan", "         Pass an argument to specify the filename.\n"],
["red", "=" * 60],
["magenta", "TIPS:"],
["magenta", "General information about this chat app"],
["red", "=" * 60],
["cyan",
 "1. Share code blocks by saving the code to a .txt file on\n   the desktop then passing the name of the file between"],
["cyan", "   triple ` such as ```hello_world```"],
["cyan", "\n2. Pass \"help\" as an argument after any command to get\n   more information. Ex: --resume help\n"]]


NE = """A NameError occurred. If running from command line, it may be a problem with the
cursor position, or multiple newline characters in your command."""

help_text = f"""\nENTER ONE OF THE FOLLOWING COMMANDS:\n{logos.make_div('=', logos.logo_width + 5, "")}
\tquit  - Exits the current OpenAI module session\n
\tchat  - Initiates a conversation with Chat GPT.\n
\tdalle - Generates an image from user prompt with Dalle.\n
\tgpt   - Returns a single response from GPT based on a user prompt. Use this
\twhen you don't want to have a full converstaion with GPT\n"""

init_conv = '''
SYSTEM MESSAGE:
Finish the empty "Assitant" response at the bottom of the script using the most recent prompt provided by "User"
as your input. If your response contains any code, please always write it inside of a code block with the filename
one line above the code block such as \n\nhello_world.py\n```\nprint("Hello World!")\n```


CONVERSATION WITH USER:\n'''

first_prompt = ""

# Fetch key
chdir(KEY_LOC)
with open("secrets.json") as file:
    key = json.load(file)['openai']['secret']
chdir(ROOT)
openai.api_key = key


# Module classes
class Dalle:

    def __init__(self):
        self.sizes = Dalle.ImageSizes()

    def create_image(self, prompt: str, num_pics=1, size='large'):
        """Generates an image with Dalle"""

        img_sizes = {'small': self.sizes.small, 'med': self.sizes.medium, 'large': self.sizes.large}

        # Generate an image then save it as a base 64 encoded json object in the AI Images folder on the Desktop
        data = openai.Image.create(prompt=prompt, n=num_pics, size=img_sizes[size], response_format='b64_json')
        file_name = DATA_DIR / f"{prompt[:30].lower().replace(' ', '_')}{str(data['created'])[3:8]}.json"
        with open(file_name, mode="w", encoding="utf-8") as the_file:
            json.dump(data, the_file)

        FILE = os.listdir(DATA_DIR)[0]
        JSON_FILE = DATA_DIR / FILE

        with open(JSON_FILE, mode="r", encoding="utf-8") as the_file:
            response = json.load(the_file)

        # Decode images
        for index, image_dict in enumerate(response["data"]):
            image_data = b64decode(image_dict["b64_json"])
            temp_name = f"{JSON_FILE.stem}-{index + 1}.png"
            image_file = DATA_DIR / temp_name
            with open(image_file, mode="wb") as png:
                png.write(image_data)

            shutil.move(f'{DATA_DIR}\\{temp_name}', f'{AI_FOLDER}\\{temp_name}')

        # Delete json file now that it's been decoded.
        os.remove(DATA_DIR / file_name)

    class ImageSizes:
        def __init__(self):
            self.small = '256x256'
            self.medium = '512x512'
            self.large = '1024x1024'

        def __str__(self):
            return f'small = 256x256\nmedium = 512x512\nlarge = 1024x1024'


class GPT:

    def __init__(self):
        self.responses = []
        self.chat_cycle = 1
        self.conversation = init_conv

    def add_chat_cycle(self):
        """Increments the chat cycle count upwards"""
        self.chat_cycle += 1

    def reset_chat_cycle(self):
        """Resets the chat cycle count"""
        self.chat_cycle = 1

    def set_chat_cycle(self, val: int):
        """Sets the cycle count to a fixed value"""

    def reset_conversation(self):
        """Resets the conversation back to it's default value"""
        self.conversation = init_conv

    def append_conversation(self, msg: str):
        """Adds new lines to the conversation"""
        self.conversation += msg

    def estimate_conversation_size(self):
        """Returns an estimation of the current number of tokens in the conversation"""
        return self.est_token_count(self.conversation)

    def update_conversation(self, new_string):
        self.conversation = new_string

    @staticmethod
    def est_token_count(text: str):
        """Returns an estimation of the number of tokens in the body of text"""
        return ceil(len(text) / 3)

    @staticmethod
    def respond(prompt: str):
        """Gets a response from GPT"""
        completion = openai.ChatCompletion.create(model="gpt-3.5-turbo",
                                                  messages=[{"role": "user", "content": prompt}])
        return completion.choices[0].message.content

    @staticmethod
    def read_file(file_name):
        """Reads a file on the desktop"""
        chdir(doc.DESKTOP)
        with open(file_name) as the_file:
            text = the_file.read()
        return text


class StringDict:

    def __init__(self):
        self.code_prompt = \
"""The code was large, and was split into smaller sections for analyzing in chunks.
Please keep this in mind when responding."""


def run(cmd=None):
    """Main program for this module"""

    artist = Dalle()

    # Get and set API key
    bad_responses = 0
    started = False
    chat_file_name = ''

    # Local function
    def refresh_gpt_connection():
        """Creates and returns another instance of GPT() to refresh the session"""
        return GPT()

    def find_cycle_num(text: str):
        """Looks through a body of text and looks for Response #x, then returns the largest occurance of it."""
        cycle_num = 0
        for line_of_text in text.split('\n'):
            if "Response #" in line:
                temp = line_of_text.replace("Response #", "")
                cycle_num = int(temp[:-1])
        return cycle_num + 1

    def highlight_syntax(text, speed=0.03):

        dialogue = text.split('```')
        wait = speed
        high_speed = speed / 3 if len(text) < 300 else speed / 6
        count = 1
        skip = False if len(text) < 500 else True
        print(logos.dye('\nAssistant: ', "cyan"), end='')

        for line_of_text in dialogue:

            reply = ""

            # It's dialogue
            if count % 2 != 0:
                reply = logos.dye(f'{line_of_text}', "cyan")
                wait = speed

            # It's code
            elif count % 2 == 0:
                reply = logos.dye(f'```{line_of_text}```', "magenta")
                wait = high_speed

            if skip:
                wait = 0.0001

            for character in f"{reply.lstrip()}\n":
                print(character, end='')
                sleep(wait)
            count += 1

    def clear_gpt():
        """Clears terminal and restarts Chat GPT"""
        os.system('cls')
        print(logos.colorize(logos.gpt_logo))
        print(dye("\tYou have initialized a conversation with GPT3.5!", "cyan"))
        print(dye("\tSay something, or type --help for options\n", "cyan"))
        writer.reset_conversation()
        writer.reset_chat_cycle()

    # Get the message dictionary
    msgs = StringDict()

    while True:

        # If this is the first loop iteration and no command was given already.
        if not started and cmd is None:
            print(f'Enter a command then press enter to continue. {GREETING}')
        started = True

        # Get user input if an initial command was not supplied via run(cmd=)
        if cmd is None:
            cmd = input('>>> ').lower().lstrip()

        # If we're writing a single response and moving on
        if cmd == 'gpt':
            writer = GPT()
            prompt = input('\nAsk GPT to write something for you.\n>>> ')
            response = writer.respond(prompt)
            doc.write_file(response, "GPT_Response.txt")
            text_edit = list(response)
            time_to_change = False
            i = 0
            for letter in text_edit.copy():
                if i > 0 and i % 60 == 0:
                    time_to_change = True
                if time_to_change:
                    if letter == ' ':
                        text_edit[i] = '\n'
                        time_to_change = False
                if letter == '\n':
                    i = 0
                    time_to_change = False
            print(dye(''.join(text_edit), "cyan"))
            return response

        # If the user is starting a prolonged conversation with GPT
        elif cmd == 'chat':

            #############################################
            #  ==============  CHAT GPT  =============  #
            #############################################

            writer = GPT()
            clear_gpt()

            # Keep track of time
            launch_time = int(time())

            # Initialize conversation variables
            testing = False

            while True:

                # Get user response
                resp = input('You: ').lstrip()
                current_time = int(time())

                # If it's been more than a minute since the last reply, refresh connection.
                if current_time - launch_time > 60:
                    writer = refresh_gpt_connection()

                # Check to see if the special -- flag was given for unique commands.
                if resp[:2] == '--':
                    cmds = resp[2:].split(' ')

                    # User chose to resume previous conversation
                    if cmds[0] == 'resume':

                        # If a conversation name was not passed
                        if len(cmds) == 1:
                            if 'ChatGPT.txt' in os.listdir(CONV_HIS):
                                writer.update_conversation(doc.read_file('ChatGPT.txt', CONV_HIS).rstrip())
                                chat_file_name = "ChatGPT"
                            else:
                                print(logos.dye('No previous conversation detected', "red"))
                                continue

                        # Otherwise if a conversation name was passed as a command.
                        elif len(cmds) > 1:
                            if cmds[1] == "help":
                                msg1 = "Resumes a previous conversation if one exists. Pass \"list\" as a command "
                                msg2 = "to view names of previous conversations"
                                print(dye(f'{msg1}{msg2}', "yellow"))
                                continue

                            elif cmds[1] == 'list' or cmds[1] == 'ls':
                                print(dye(f"\nPrior conversations:\n{'=' * 50}", "yellow"))
                                conversations = os.listdir(CONV_HIS)
                                for i in range(len(conversations)):
                                    if i == len(conversations) - 1:
                                        file_name = convs[i]
                                    else:
                                        file_name = f'{conversations[i]}, '

                                    if i >= 3 and (i + 1) % 4 == 0 and i != (len(conversations) - 1):
                                        file_name += '\n'
                                    print(dye(file_name, "yellow"), end='')
                                print(dye(f'\n{"=" * 50}\n', "yellow"))
                                continue

                            if f"{cmds[1]}.txt" in os.listdir(CONV_HIS):
                                writer.update_conversation(doc.read_file(f"{cmds[1]}.txt", CONV_HIS).rstrip() + '\n\n')
                                chat_file_name = cmds[1]
                                if chat_file_name == 'test':
                                    testing = True
                            else:
                                print(logos.dye('No conversation by that name detected', "red"))
                                continue

                        writer.set_chat_cycle(find_cycle_num(writer.conversation))
                        os.system('cls')
                        print(logos.colorize(logos.gpt_logo))
                        print('You have initiated a conversation with ChatGPT. Say something.\n')
                        print_text = writer.conversation.split('Assistant:')[-1]
                        highlight_syntax(f'{print_text}\n', speed=0.01)
                        continue

                    # User is beginning with a pre-written prompt
                    elif cmds[0] == 'prompt':

                        if not len(cmds) > 1:
                            print(dye("Which template will you be using?", "cyan"))
                            cmds.append(input(">>> "))

                        else:
                            if cmds[1] == "help":
                                msg1 = "Inserts a previously created prompt as the initial prompt of the conversation. "
                                msg2 = "Enter \"save\" as the first argument to save the first prompt of this "
                                msg3 = "conversation as a template for later use. Otherwise, enter the name of the "
                                msg4 = "prompt template file to select it such as --prompt web_app"
                                print(dye(f"{msg1}{msg2}{msg3}{msg4}", "yellow"))
                                continue

                            elif cmds[1] == 'save':
                                if chat_file_name == '':
                                    fn = input(dye("Enter a file name for the prompt:\n>>>", "cyan"))
                                else:
                                    fn = chat_file_name

                                # Initial variables
                                name = f'{fn}_prompt.txt'
                                prompt = ""
                                record = False
                                overwrite = True

                                # If files exists
                                if name in os.listdir(PROMPT_TEMPLATES):
                                    print(dye(f"\nWARNING: Template {name} already exists. Overwrite it? Y/N", "red"))
                                    rep = input(">>> ").lower()

                                    # If overwriting
                                    if not rep == 'y':
                                        overwrite = False
                                        print(dye("\nPrompt save aborted...", "yellow"))

                                if overwrite:
                                    # Extract prompt
                                    for line in writer.conversation.split("\n"):

                                        if "Response #1" in line:
                                            record = True
                                            continue
                                        elif "Assistant:" in line:
                                            break

                                        if record:
                                            prompt += f"{line}\n"

                                    doc.write_file(prompt[6:].lstrip().rstrip(), name, _dir=PROMPT_TEMPLATES)
                                    print(dye(f"File saved as {name}", "blue"))

                                continue

                        chdir(PROMPT_TEMPLATES)
                        files = os.listdir(PROMPT_TEMPLATES)

                        if f'{cmds[1].lower()}.txt' in files:
                            resp = doc.read_file(f'{cmds[1]}.txt')
                            os.system('cls')
                            print(logos.colorize(logos.gpt_logo))
                            prm = f"{resp[:151]}..." if len(resp) > 150 else resp
                            print(f'You have initiated a conversation with ChatGPT. Say something.\n\nYou: {prm}')
                        else:
                            print(logos.dye("No prompt with that name detected", "red"))
                            print(logos.dye("Options include: ", "cyan"), end='')
                            for num, file in enumerate(files):
                                line_end = "" if (num % 3 == 0 or num == 0) else "\n"
                                name = f'{file.split(".")[0]}\n' if num == len(files) - 1 else f"{file.split('.')[0]}, "
                                print(logos.dye(name, "green"), end=line_end)
                            continue
                        chdir(ROOT)

                    # User wishes to save the conversation for later
                    elif cmds[0] == "save":

                        # If no filename was passed as a command
                        if not len(cmds) > 1:

                            # If no file_name_has previously been established, then establish one.
                            # otherwise just move on with the existing filename.
                            if chat_file_name == '':
                                chat_file_name = input(dye("Enter a file name: ", "yellow"))

                        # Otherwise if a filename was passed as a command
                        if len(cmds) > 1:
                            if cmds[1] == "help":
                                msg1 = "Saves the current conversation. Pass a second argument to specify the "
                                msg2 = "conversation name"
                                print(dye(f"{msg1}{msg2}", "yellow"))
                                continue
                            else:
                                chat_file_name = cmds[1]

                        # Move the directory and save the file
                        doc.write_file(f"{writer.conversation}\n\n", f"{chat_file_name}.txt", _dir=CONV_HISTORY)
                        chdir(ROOT)
                        print(dye(f'\nConversation saved as {chat_file_name}.txt\n', "blue"))
                        continue

                    # If testing
                    elif cmds[0] == 'test':
                        if len(cmds) > 1:
                            if cmds[1] == 'off':
                                testing = False
                            elif cmds[1] == 'on':
                                testing = True
                        else:
                            testing = True
                        chat_file_name = cmds[0]

                    elif cmds[0] == 'clear':
                        clear_gpt()
                        continue

                    elif cmds[0] == "help":
                        for line in gpt_help_string:
                            if '==' in line[1]:
                                print(dye(line[1], line[0]))
                            else:
                                for char in line[1]:
                                    print(dye(char, line[0]), end='')
                                    sleep(0.001)
                                print()
                        continue

                    # NO VALID COMMAND GIVEN
                    else:
                        print(dye('\nInvalid command given...\n', "red"))
                        continue

                # insert code blocks if necessary
                original_resp = resp
                names_of_scripts = []
                if '```' in resp:
                    for i in os.listdir(doc.DESKTOP):
                        j = i.split('.')[0]
                        if f'```{j}```' in resp:
                            names_of_scripts.append(i)
                            user_code = doc.read_file(i, doc.DESKTOP)
                            bot_code = ""
                            for line in user_code.split('\n'):
                                bot_code += f"{line.rstrip()}\n"

                            resp = resp.replace(f'```{j}```',
                                                f'\n\n{i}\n```\n{bot_code}\n```\n\n')

                # If the user typed "quit" or "exit"
                if resp.lower().lstrip().rstrip() in break_commands:
                    print(logos.dye('Chat session closed. Enter another command to continue.\n', "red"))
                    break

                # If the user wants to refresh the session
                elif resp.lower().lstrip().rstrip() == 'clear':
                    clear_gpt()
                    continue
                else:
                    gpt = ""
                    writer.append_conversation(f'\n\nResponse #{writer.chat_cycle}:\n\nUser: {resp}\n\nAssistant: ')
                    if not testing:

                        launch_time = time()

                        try:
                            gpt = writer.respond(writer.conversation)

                        except openai.error.InvalidRequestError:

                            # Remove old responses from conversation to limit context length
                            max_lines_per_submission = 70
                            text_body = writer.conversation.split("Response #")
                            first_half_convo = text_body[0:2]
                            second_half_convo = text_body[-1]
                            gpt = ''

                            # If the first response is equal to the second half of the conversation, then the
                            # initial prompt from the user is too big. Split it.
                            if second_half_convo == text_body[1]:
                                codes = [i for count, i in enumerate(text_body[1].split("```")) if count % 2 != 0]
                                boilerplate = f"USER PROMPT:\n{original_resp}\n\nNOTE:\n{msgs.code_prompt}\n\nCODE:\n"

                                if len(codes) > 0:
                                    # Loop through the codes in the list
                                    end_num = 0
                                    for i, code in enumerate(codes):
                                        init_submission = f"{boilerplate}\n\n{names_of_scripts[i]}"
                                        lines = ""

                                        # Loop through the lines of code that were shared
                                        code_lines = code.split('\n')
                                        code_length = len(code_lines)
                                        for line_num, line_text in enumerate(code_lines):
                                            lines += f"{line_text}\n"

                                            # Share no more than the maximum number of allowed lines of code.
                                            if (line_num + 1) % max_lines_per_submission == 0 and line_num > 1:
                                                start_num = end_num
                                                end_num = line_num
                                                submission = f"{init_submission}"
                                                submission += f" lines {start_num + 1} - {end_num + 1}\n```\n{lines}```"
                                                lines = ""
                                                gpt_request = writer.respond(submission)
                                                tokens = gpt_request.split("```")

                                                if "```" in gpt_request:
                                                    if len(tokens) > 2 and tokens[2] != '':
                                                        print(dye("GPT responded with:", "red"))
                                                        highlight_syntax(gpt_request)
                                                        print(dye("Proceed? Y/N", "yellow"))
                                                        user_input = input(">>>").lower()[0]
                                                        if user_input == 'y':
                                                            pass
                                                        else:
                                                            break

                                                    if line_num + 1 <= max_lines_per_submission:
                                                        gpt += f"{tokens[0]}```{tokens[1]}"
                                                    elif end_num + max_lines_per_submission > code_length:
                                                        temp_string = tokens[1].rstrip("\n")
                                                        gpt += f'{temp_string}\n```'
                                                    else:
                                                        gpt += tokens[1]

                                                else:
                                                    print(dye("GPT responded with no code:\n", "red"))
                                                    highlight_syntax(gpt_request)
                                                    print(dye("\nProceed anyway? Y/N", "yellow"))
                                                    user_input = input(">>>").lower()[0]
                                                    if user_input == 'y':
                                                        gpt += gpt_request
                                                    else:
                                                        break
                                else:
                                    print(dye("Error when importing script(s) to conversation. Bad name(s).", "red"))

                            # Otherwise, the conversation probably just got too long. Clear some old responses
                            else:

                                fstr = "Response #".join(first_half_convo)
                                responses_to_add = []
                                for count in range(len(text_body) - 1, 1, -1):
                                    bod = "Response #x\n".join(text_body[count:])
                                    if writer.est_token_count(fstr + bod) < config_data['max_token_size']:
                                        responses_to_add.insert(0, f"Response #{text_body[count]}")
                                    else:
                                        break
                                writer.update_conversation(fstr + "".join(responses_to_add))

                    elif testing:
                        gpt = "This is a premade reply from GPT for testing purposes.\n```\nprint('Hello')\n```"

                    writer.append_conversation(f'{gpt}\n\n')
                    highlight_syntax(f"{gpt}\n")

                # Save the conversation as a text file.
                doc.write_file(f"{writer.conversation}\n", 'ChatGPT.txt', _dir=CONV_HIS)
                writer.add_chat_cycle()

            break

        elif cmd == 'dalle':
            user = input(dye('Enter a prompt for Dalle to generate an image\n', "cyan") + dye('>>> ', "magenta"))
            copies = int(input(dye('How many images do you want to generate?\n', "cyan") + dye('>>> ', "magenta")))
            image_size = input(dye('What size image(s)? S/M/L\n', "cyan") + dye('>>> ', "magenta")).lower()[0]
            if image_size == "s":
                image_size = "small"
            elif image_size == "m":
                image_size = "med"
            elif image_size == 'l':
                image_size = "large"

            try:
                print(dye('Generating images. Please wait...', "yellow"))
                artist.create_image(user, copies, image_size)
                print(dye('Completed...\n', "red"))

            except:
                print("The server doesn't seem to be responding")

            finally:
                pass

        elif cmd == 'help':
            print(dye(help_text, "red"))

        elif cmd not in commands:
            bad_responses += 1
            if bad_responses == 3:
                os.system('cls')
                print('Too many bad responses. Application terminated...')
                break
            else:
                print(f'Invalid command given. Valid options are {commands}. Try again.')

        elif cmd in break_commands:
            break

        # Reset cmd to None so that the user can choose a new OpenAI option before exiting main loop
        cmd = None


# Run main if not importing
if __name__ == '__main__':
    run()

