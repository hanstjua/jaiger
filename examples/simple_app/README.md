# Simple App

## Running

Before running, modify the content of `simple_app.json` to include the necessary details of your AI model of choice.

Then, simply run `simple_app.py` in your terminal (make sure that you have installed `Jaiger` and all its dependencies).

## Explanation

This app is a simple AI chatbot application that runs in your terminal. This app will introduce two tools to the AI: `PythonTool` and `FileTool`. You can tell the chatbot to perform tasks that utilize these tools or you can simply use it like you would a normal AI chatbot.

The `PythonTool` allows the chatbot to execute arbitrary Python code for you.

The `FileTool` allows the chatbot to perform file-related actions (i.e. create, modify and delete).

You can find out more about the capabilities of these tools in `tools.py`.
