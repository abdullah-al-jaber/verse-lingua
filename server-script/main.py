#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK

########################
#     Verse CAPTOR     #
########################

import os
import sys
import json
import typing
import asyncio
import argparse
import warnings
import urllib.parse

import rich.console
import rich.traceback
import rich_argparse
import argcomplete
import soupsieve
import websockets
import bs4

console = rich.console.Console()
rich.traceback.install(console=console, show_locals=True)
warnings.filterwarnings("ignore")
sys.stderr = open(os.devnull, "w")
halt_event = asyncio.Event()

blank_line = "\n"
current_url = "https://example.com/"
current_count = 0


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
    start_url: str
    stop_url: str
    folder_path: str
    text_selector: str
    url_selector: str


def url_validator(url: str) -> str:
    parse_result = urllib.parse.urlparse(url)
    if not (parse_result.scheme in ("http", "https") and parse_result.netloc):
        raise argparse.ArgumentTypeError(f"URL isn't valid! [URL: '{url}']")
    return url


def folder_path_validator(folder_path: str) -> str:
    if os.path.isdir(folder_path) and len(os.listdir(folder_path)) != 0:
        raise argparse.ArgumentTypeError(f"Folder isn't empty ! [FOLDER PATH: '{folder_path}']")
    return folder_path


def selector_validator(selector: str) -> str:
    try:
        soupsieve.compile(selector)
        return selector
    except Exception as error:
        raise argparse.ArgumentTypeError(f"Selector isn't valid ! [SELECTOR: '{selector}']  \n ({error})")


argument_parser = custom_argument_parser(
    prog="verse-lingua",
    formatter_class=rich_argparse.RichHelpFormatter,
    description="Scrap novel from website dynamically",
    epilog="No way Home !",
    add_help=False,
)

argument_parser.add_argument(
    "--start-url",
    type=url_validator,
    metavar="URL",
    help="Start URL for scaping novel chapter",
    required=True,
)

argument_parser.add_argument(
    "--stop-url",
    type=url_validator,
    metavar="URL",
    help="Stop URL for scaping novel chapter",
    required=True,
)

argument_parser.add_argument(
    "--folder-path",
    type=folder_path_validator,
    metavar="FOLDER_PATH",
    help="Folder Path for novel chapter texts",
    required=True,
)

argument_parser.add_argument(
    "--text-selector",
    type=selector_validator,
    metavar="SELECTOR",
    help="Selector for extracting text from html",
    required=True,
)

argument_parser.add_argument(
    "--url-selector",
    type=selector_validator,
    metavar="SELECTOR",
    help="Selector for extracting url from html",
    required=True,
)

argument_parser.add_argument(
    "--help",
    action="help",
    help="Show this help message and exit",
)

argcomplete.autocomplete(argument_parser)
argument = argument_parser.parse_args(namespace=custom_argument_namespace())


def read_file(file_path: str, mode: str) -> str | bytes:
    with open(file_path, mode) as file:
        return file.read()


def write_file(file_path: str, content: str | bytes, mode: str) -> None:
    with open(file_path, mode) as file:
        file.write(content)


async def request_current_url(websocket: websockets.ServerConnection, data: dict) -> None:
    data = {
        "current_url": current_url,
    }
    await websocket.send(json.dumps({"type": "response_current_url", "data": data}))


async def submit_html(websocket: websockets.ServerConnection, data: dict) -> None:
    global current_url, current_count
    text_selector = soupsieve.compile(argument.text_selector)
    url_selector = soupsieve.compile(argument.url_selector)
    soup = bs4.BeautifulSoup(data["html"], "html.parser")
    text_elements = text_selector.select(soup)
    url_elements = url_selector.select(soup)
    assert len(text_elements) > 0, "No text element found !"
    assert len(url_elements) > 0, "No url element found !"
    text = blank_line.join([element.get_text(separator=blank_line, strip=True) for element in text_elements])
    text = blank_line.join([line.strip() for line in text.split(blank_line) if line.strip() != ""])
    url = url_elements[0].get("href")
    url = str(url).strip()
    assert len(text) > 0, "No text found in the text elements !"
    assert len(url) > 0, "No url found in the url element !"
    write_file(os.path.join(argument.folder_path, f"chapter-{current_count}.txt"), text, "w")
    console.print(f"SAVED: chapter-{current_count}.txt ! [{current_url}]")
    if current_url == argument.stop_url:
        await websocket.close()
        halt_event.set()
    current_url, current_count = urllib.parse.urljoin(current_url, str(url)), current_count + 1


async def verse_captor(websocket: websockets.ServerConnection):
    handler_mapping = {
        "request_current_url": request_current_url,
        "submit_html": submit_html,
    }
    async for message in websocket:
        message = json.loads(message)
        assert "type" in message, "Message Type isn't found !"
        assert "data" in message, "Message Data isn't found !"
        assert message["type"] in handler_mapping, "Message Type isn't known !"
        if message["type"] in handler_mapping:
            await handler_mapping[message["type"]](websocket, message["data"])


async def main() -> None:
    global current_url, current_count
    current_url, current_count = argument.start_url, current_count or 1
    os.makedirs(argument.folder_path, exist_ok=True)
    server = await websockets.serve(verse_captor, "127.0.0.1", 6969)
    console.print("SERVER IS RUNNING ! [127.0.0.1:6969]")
    await halt_event.wait()
    server.close()
    await server.wait_closed()
    console.print("SERVER IS STOPPED !")


if __name__ == "__main__":
    asyncio.run(main())

# Final Version [line-length : 120]
