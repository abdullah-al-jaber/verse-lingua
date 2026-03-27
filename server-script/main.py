#!/usr/bin/env python3

########################
#     Verse Lingua     #
########################

import re
import os
import sys
import json
import typing
import asyncio
import argparse
import warnings

import rich.console
import rich.progress
import rich.panel
import rich.live
import rich.traceback
import rich_argparse
import websockets

console = rich.console.Console()
rich.traceback.install(console=console, show_locals=True)
warnings.filterwarnings("ignore")
# sys.stderr = open(os.devnull, "w")
halt_event = asyncio.Event()

blank_line = "\n"
current_index = 0
file_names = []


@typing.overload
def read_file(file_path: str, mode: typing.Literal["r"]) -> str: ...
@typing.overload
def read_file(file_path: str, mode: typing.Literal["rb"]) -> bytes: ...


@typing.overload
def write_file(file_path: str, content: str, mode: typing.Literal["w"]) -> None: ...
@typing.overload
def write_file(file_path: str, content: str, mode: typing.Literal["a"]) -> None: ...
@typing.overload
def write_file(file_path: str, content: bytes, mode: typing.Literal["wb"]) -> None: ...
@typing.overload
def write_file(file_path: str, content: bytes, mode: typing.Literal["ab"]) -> None: ...


class custom_argument_parser(argparse.ArgumentParser):
    def error(self, message: str) -> typing.NoReturn:
        self.print_help()
        console.print("\n" + "#======#_#======#" + "\n")
        console.print(message.capitalize())
        sys.exit(2)


class custom_argument_namespace(argparse.Namespace):
    input_folder_path: str
    output_folder_path: str


def input_folder_path_validator(input_folder_path: str) -> str:
    if not os.path.isdir(input_folder_path):
        raise argparse.ArgumentTypeError(f"Input Folder doesn't exists ! [INPUT FOLDER PATH: '{input_folder_path}']")
    if len(os.listdir(input_folder_path)) == 0:
        raise argparse.ArgumentTypeError(f"Input Folder is empty ! [INPUT FOLDER PATH: '{input_folder_path}']")
    return input_folder_path


def output_folder_path_validator(folder_path: str) -> str:
    if os.path.isdir(folder_path) and len(os.listdir(folder_path)) != 0:
        raise argparse.ArgumentTypeError(f"Output Folder isn't empty ! [OUTPUT FOLDER PATH: '{folder_path}']")
    return folder_path


argument_parser = custom_argument_parser(
    prog="verse-lingua",
    formatter_class=rich_argparse.RichHelpFormatter,
    description="Translate novel with Google Translate",
    epilog="No way Home !",
    add_help=False,
)

argument_parser.add_argument(
    "--input-folder-path",
    type=input_folder_path_validator,
    metavar="FOLDER_PATH",
    help="Folder Path for native novel chapter texts",
    required=True,
)

argument_parser.add_argument(
    "--output-folder-path",
    type=output_folder_path_validator,
    metavar="FOLDER_PATH",
    help="Folder Path for foreign novel chapter texts",
    required=True,
)

argument = argument_parser.parse_args(namespace=custom_argument_namespace())


def read_file(file_path: str, mode: str) -> str | bytes:
    with open(file_path, mode) as file:
        return file.read()


def write_file(file_path: str, content: str | bytes, mode: str) -> None:
    with open(file_path, mode) as file:
        file.write(content)


def number_search(string: str):
    match = re.search(r"\d+", string)
    return int(match.group()) if match else 0


async def request_progress_info(websocket: websockets.ServerConnection, data: dict) -> None:
    data = {"percentage": f"{progress.tasks[task_id].percentage:.0f}"}
    await websocket.send(json.dumps({"type": "response_progress_info", "data": data}))


async def request_current_job(websocket: websockets.ServerConnection, data: dict) -> None:
    if current_index >= len(file_names):
        return await websocket.close()
    data = {"current_index": current_index, "text": read_file(os.path.join(argument.input_folder_path, file_names[current_index]), "r")}
    await websocket.send(json.dumps({"type": "response_current_job", "data": data}))


async def submit_text(websocket: websockets.ServerConnection, data: dict) -> None:
    global current_index
    assert "current_index" in data, "Current Index isn't found !"
    assert "text" in data, "Text isn't found !"
    assert current_index == data["current_index"], "Current Index Mismatch !"
    write_file(os.path.join(argument.output_folder_path, file_names[data["current_index"]]), data["text"], "w")
    console.print(f"TRANSLATED: {file_names[current_index]} ! ")
    current_index += 1
    progress.advance(task_id)
    if current_index >= len(file_names):
        await websocket.close()
        halt_event.set()


async def verse_captor(websocket: websockets.ServerConnection):
    handler_mapping = {
        "request_progress_info": request_progress_info,
        "request_current_job": request_current_job,
        "submit_text": submit_text,
    }
    async for message in websocket:
        message = json.loads(message)
        assert "type" in message, "Message Type isn't found !"
        assert "data" in message, "Message Data isn't found !"
        assert message["type"] in handler_mapping, "Message Type isn't known !"
        if message["type"] in handler_mapping:
            await handler_mapping[message["type"]](websocket, message["data"])


async def main() -> None:
    global current_index, file_names, progress, task_id
    os.makedirs(argument.output_folder_path, exist_ok=True)
    current_index, file_names = 0, os.listdir(argument.input_folder_path)
    file_names.sort(key=number_search)
    progress = rich.progress.Progress()
    task_id = progress.add_task("TOTAL", total=len(file_names))
    with rich.live.Live(rich.panel.Panel(progress, width=60), console=console):
        server = await websockets.serve(verse_captor, "127.0.0.1", 9696)
        console.print("SERVER IS RUNNING ! [127.0.0.1:9696]")
        await halt_event.wait()
        server.close()
        await server.wait_closed()
        console.print("SERVER IS STOPPED !")


if __name__ == "__main__":
    asyncio.run(main())

# Final Version [line-length : 150]
