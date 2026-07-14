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
import urllib.parse


import rich.console
import rich.progress
import rich.panel
import rich.live
import rich.traceback
import rich_argparse
import googletrans

console = rich.console.Console()
rich.traceback.install(console=console, show_locals=True)
sys.stderr = open(os.devnull, "w")

blank_line = "\n"
blank_string = ""


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
    input_language: str
    output_language: str
    worker_count: int
    show_locals: bool


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


def number_validator(number: str) -> int:
    try:
        number = int(number)
    except ValueError:
        raise argparse.ArgumentTypeError(f"Number must be integer ! [NUMBER: '{number}']")
    if number <= 0:
        raise argparse.ArgumentTypeError(f"Number must be  non-zero positive value ! [NUMBER: '{number}']")
    return number


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

argument_parser.add_argument(
    "--input-language",
    type=str,
    metavar="LANG",
    default="auto",
    help="Language of input novels chapter texts",
)

argument_parser.add_argument(
    "--output-language",
    type=str,
    metavar="LANG",
    default="en",
    help="Language of output novels chapter texts",
)

argument_parser.add_argument(
    "--worker-count",
    type=number_validator,
    metavar="NUMBER",
    default=5,
    help="Number of workers for verse lingua",
)

argument_parser.add_argument(
    "--show-locals",
    action="store_true",
    help="Show local variables for rich.traceback",
)

argument_parser.add_argument(
    "--help",
    action="help",
    help="Show this help message and exit",
)

argument = argument_parser.parse_args(namespace=custom_argument_namespace())

rich.traceback.install(console=console, show_locals=argument.show_locals)


def read_file(file_path: str, mode: str) -> str | bytes:
    with open(file_path, mode) as file:
        return file.read()


def write_file(file_path: str, content: str | bytes, mode: str) -> None:
    with open(file_path, mode) as file:
        file.write(content)


def number_search(string: str) -> int:
    match = re.search(r"\d+", string)
    return int(match.group()) if match else 0


def split_text(text: str, limit: int) -> list[str]:
    chunks, chunk = [], ""
    for line in text.splitlines(keepends=True):
        if len(line) > limit:
            raise Exception("Line can't be broken !")
        if len(chunk) + len(line) > limit:
            chunks.append(chunk)
            chunk = ""
        chunk += line
    if chunk:
        chunks.append(chunk)
    return chunks


async def translate_text(text: str) -> str:
    async with googletrans.Translator() as translator:
         return (await translator.translate(text, src=argument.input_language, dest=argument.output_language)).text


async def translate(file_name: str, semaphore: asyncio.Semaphore) -> None:
    async with semaphore:
        input_file_path = os.path.join(argument.input_folder_path, file_name)
        output_file_path = os.path.join(argument.output_folder_path, file_name)
        native_text = read_file(input_file_path, "r")
        tasks = [translate_text(chunk.strip()) for chunk in split_text(native_text, 5000)]
        foreign_text = blank_line.join(await asyncio.gather(*tasks))
        write_file(output_file_path, foreign_text, "w")
        console.print(f"SUCCESS: {file_name}")
        progress.advance(task_id)


async def verse_lingua(file_names: list[str]) -> None:
    tasks = []
    semaphore = asyncio.Semaphore(argument.worker_count)
    for file_name in file_names:
        tasks.append(translate(file_name, semaphore))
    await asyncio.gather(*tasks)


async def main() -> None:
    global progress, task_id
    os.makedirs(argument.output_folder_path, exist_ok=True)
    file_names = os.listdir(argument.input_folder_path)
    file_names.sort(key=number_search)
    progress = rich.progress.Progress()
    task_id = progress.add_task("TOTAL", total=len(file_names))
    with rich.live.Live(rich.panel.Panel(progress, width=60), console=console):
        await verse_lingua(file_names)


if __name__ == "__main__":
    asyncio.run(main())
