
# Local AI Chat Server

![example1](/data/examples/ui1.png)
![example1](/data/examples/caecea.png)

## Features

- **Character Management:** Create, update, and delete character profiles with names, descriptions, and avatar URLs.
- **Chat Sessions:** Engage in conversations with characters and save the chat history.
- **Streaming Responses:** Receive AI responses in real-time as they are generated (using streaming).
- **Cross-Platform:** Designed to run on Windows and mobile devices.
- **Themes**: Change the color of the UI however you like!

## ⚠️ Important Notice for Users

> **THIS IS ONLY FOR LOCAL LLM USERS. IT PROBABLY DOES NOT SUPPORT ANY OUTSIDE API LIKE CHATGPT, CLAUDE, GWEN, ETC**

This project is specifically designed to work with locally hosted language models (e.g., LM Studio, Koboldcpp, TextGenWebUI). It does **not** support external APIs such as OpenAI's ChatGPT, Anthropic's Claude, or other cloud-based AI services.

## Prerequisites

1. A working LLM on your PC: You must have an LLM running locally (e.g., LM Studio, Koboldcpp, TextGenWebUI) on port 1234 (default for LM Studio). You can change this port in `main.py`.
2. **Python:** Python 3.10 worked on my machine; it should work with higher versions as well.

## Installation & Setup

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/Sapphirana/LocalAIChat.git
   ```

2. **Run `Install.bat`**  
   This will install dependencies and start the server automatically.

3. **Configuration (Important):**  
   Make sure that the `LM_STUDIO_API_URL` variable in `main.py` is correctly set to your running LM Studio instance's URL. The default value is:
   ```
   http://localhost:1234/v1/chat/completions
   ```
   Double-check this setting before proceeding.

## Running the Server

1. **Start Your Preferred LLM Engine** (e.g., LM Studio, Koboldcpp, etc.)

2. **Access the Web UI:**  
   Open your web browser and navigate to:  
   ```
   http://127.0.0.1:5500
   ```

> **Note:**  
> If you want your Flask app to only listen on `localhost`, change the host parameter from `'0.0.0.0'` to `'127.0.0.1'` in `main.py`.  
> It uses ***ONLY*** Chat Completions-style JSON template (similar to OpenAI's). From my testing, ChatML and Gemma3 work fine.  
> This project was created with the help of an AI assistant and this will be my *first and last* project I ever make. Although I tried to make it as user-friendly as possible, you might encounter some bugs.

## License Information

This project uses the following third-party libraries:

- **Tailwind CSS** - [MIT License](https://github.com/tailwindlabs/tailwindcss/blob/master/LICENSE)
  ```html
  <link href="data/tailwind.min.css" rel="stylesheet">
  ```

- **Marked.js** - [MIT License](https://github.com/markedjs/marked/blob/master/LICENSE.md)
  ```html
  <script src="data/marked.min.js"></script>
  ```

- **DOMPurify** - [Apache-2.0 License](https://github.com/cure53/DOMPurify/blob/HEAD/LICENSE.txt)
  ```html
  <script src="data/purify.min.js"></script>
  ```

> ⚠️ **Disclaimer**: This project only uses local LLMs exclusively. It does not connect to or use any online AI APIs such as ChatGPT, Claude, or Gwen.
