# Web UI App

## Running

Before running, modify the content of `web_ui_app.json` to include the necessary details of your AI model of choice, and install the required modules listed in `requirements.txt`.

Then, simply run `web_ui_app.py` in your terminal (make sure that you have installed `Jaiger` and all its dependencies).

Once the server is up and running, you can access the app in your browser by visiting http://127.0.0.1:7613

## Explanation

This app is a simple AI chatbot application with a web UI interface. This app will introduce two tools to the AI: `PythonTool` and `FileTool`. You can tell the chatbot to perform tasks that utilize these tools or you can simply use it like you would a normal AI chatbot.

The `PythonTool` allows the chatbot to execute arbitrary Python code for you.

The `FileTool` allows the chatbot to perform file-related actions (i.e. create, modify and delete).

You can find out more about the capabilities of these tools in `tools.py`.
