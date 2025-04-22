from pathlib import Path
from typing import Any

from jaiger.tool.tool import Tool


class PythonTool(Tool):
    """This tool can be used to execute arbitrary Python code."""

    def execute(self, code: str) -> Any:
        """
        This function executes arbitrary Python code.

        :param code str: The Python code to be executed.
        :returns: The output of the code execution.
        :rtype: Any
        """

        return eval(code)


class FileTool(Tool):
    """This tool can be used to perform file-related operations."""

    def create(self, filename: str, content: str = "", exist_ok: bool = True) -> str:
        """
        Create a file at the given absolute path, optionally writing content to it.

        :param filename str: The full path where the file should be created.
        :param content str: Optional text content to write to the file. Defaults to an empty string.
        :param exist_ok bool: If True, does not raise an error if the file already exists. Defaults to True.
        :return: The absolute path of the created file.
        :rtype: str
        """

        filepath = Path(filename).expanduser()
        filepath.touch(exist_ok=exist_ok)
        if content != "":
            filepath.write_text(content, encoding="utf-8")

        return filename

    def modify(self, filename: str, content: str, append: bool = True) -> str:
        """
        Modify a file by appending or overwriting content.

        :param filename str: The full path of the file to modify.
        :param content str: The content to write into the file.
        :param append bool: If True, content is appended to the file; if False, it overwrites the file. Defaults to True.
        :returns: The absolute path of the modified file.
        :rtype: str
        """

        filepath = Path(filename).expanduser()
        if not filepath.is_file():
            filepath.touch()

        with open(str(filepath), "a" if append else "w") as f:
            f.write(content)

        return filename

    def delete(self, filename: str) -> str:
        """
        Delete a file at the given absolute path.

        :param filename str: The full path of the file to delete.
        :returns: The absolute path of the deleted file.
        :rtype: str
        """

        Path(filename).expanduser().unlink(missing_ok=True)

        return filename
