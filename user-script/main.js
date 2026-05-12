// ==UserScript==
// @name         Verse Lingua
// @namespace    https://github.com/abdullah-al-jaber
// @version      2.5
// @description  Translate novel with Google Translate
// @author       Retro Boy
// @match        https://translate.google.com/*
// @run-at       document-idle
// @grant        none
// ==/UserScript==

(async () => {
    "use strict";
    if (window.top !== window.self) return void 0;
    const STATUS_COLORS = {
        waiting: "cyan",
        idle: "magenta",
        ws_error: "red",
        message_format_error: "brown",
        message_type_unknown: "orange",
        message_data_unknown: "yellow",
        cloudflare_challenge: "green",
        line_too_long: "teal",
    };
    const INPUT_ELEMENT_SELECTOR = "textarea[aria-label='Source text']";
    const WAIT_ELEMENT_SELECTOR = "div.lRu31";
    const COPY_ELEMENT_SELECTOR = "button[aria-label='Copy translation']";
    const CLEAR_ELEMENT_SELECTOR = "button[aria-label='Clear source text']";
    const MAX_CHAR_LIMIT = 5000;
    const host = document.createElement("div");
    Object.assign(host, {
        hidden: true
    });
    Object.assign(host.style, {
        width: "100vw",
        height: "10px",
        position: "fixed",
        left: "0px",
        top: "0px",
        zIndex: "9999",
        border: `1px solid ${STATUS_COLORS.idle}`,
        backgroundColor: "white",
        boxSizing: "border-box",
        overflow: "hidden",
    });
    document.documentElement.appendChild(host);
    const shadow = host.attachShadow({
        mode: "open"
    });
    const progress_bar = document.createElement("div");
    Object.assign(progress_bar.style, {
        width: "0%",
        height: "10px",
        backgroundColor: STATUS_COLORS.idle,
        transition: "width 0.3s ease-in-out"
    });
    shadow.appendChild(progress_bar);
    const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    const wait_for_element = async (selector) => {
        const query = document.querySelector(selector);
        const promise = new Promise((resolve) => {
            const observer = new MutationObserver(() => {
                const element = document.querySelector(selector);
                if (element)(observer.disconnect(), resolve(element));
            });
            observer.observe(document, {
                childList: true,
                subtree: true
            });
        });
        return query || (await promise);
    };
    const progress_update_state = async (percentage) => {
        progress_bar.style.width = `${percentage}%`;
    };
    const progress_update_color = async (color) => {
        host.style.borderColor = color;
        progress_bar.style.backgroundColor = color;
    };
    const translate_text = async (text) => {
        const input_element = await wait_for_element(INPUT_ELEMENT_SELECTOR);
        input_element.value = text;
        input_element.dispatchEvent(new Event("input", {
            bubbles: true
        }));
        window.bfr_bk = window.clip_board;
        await wait_for_element(WAIT_ELEMENT_SELECTOR);
        (await wait_for_element(COPY_ELEMENT_SELECTOR)).click();
        (await wait_for_element(CLEAR_ELEMENT_SELECTOR)).click();
        if (window.bfr_bk == window.clip_board) await sleep(1000);
        if (document.querySelector(WAIT_ELEMENT_SELECTOR)) await sleep(500);
        return (window.clip_board != window.bfr_bk) ? window.clip_board : translate_text(text);
    };
    const translate = async (text) => {
        const lines = text.split("\n");
        const chunks = [];
        let current_chunk = "";
        for (const line of lines) {
            if (line.length > MAX_CHAR_LIMIT) {
                progress_update_color(STATUS_COLORS.line_too_long);
                throw new Error("LINE TOO LONG !");
            } else if (current_chunk.length + line.length + 1 > MAX_CHAR_LIMIT) {
                if (current_chunk) chunks.push(current_chunk);
                current_chunk = line;
            } else {
                current_chunk += (current_chunk ? "\n" : "") + line;
            }
        }
        if (current_chunk) chunks.push(current_chunk);
        let output = "";
        for (const chunk of chunks) {
            output += (output ? "\n" : "") + (await translate_text(chunk));
        }
        return output
            .split('\n')
            .filter(line => line.trim() !== '')
            .join('\n');;

    };
    const response_progress_info = async (websocket, data) => {
        if (!("percentage" in data)) return progress_update_color(STATUS_COLORS.message_data_unknown);
        await progress_update_state(data.percentage);
    };
    const response_current_job = async (websocket, data) => {
        if (!("current_index" in data && "text" in data)) return progress_update_color(STATUS_COLORS.message_data_unknown);
        if (document.title == "Just a moment...") return progress_update_color(STATUS_COLORS.cloudflare_challenge);
        websocket.send(JSON.stringify({
            type: "submit_text",
            data: {
                current_index: data.current_index,
                text: await translate(data.text),
            },
        }), );
        websocket.send(JSON.stringify({
            type: "request_progress_info",
            data: {}
        }))
        websocket.send(JSON.stringify({
            type: "request_current_job",
            data: {}
        }));
    };
    const websocket = new WebSocket("ws://127.0.0.1:9696");
    websocket.onopen = () => (host.hidden = false);
    websocket.onclose = () => (host.hidden = true);
    websocket.onerror = () => progress_update_color(STATUS_COLORS.ws_error);
    websocket.onmessage = async (event) => {
        const message = JSON.parse(event.data);
        const handler_mapping = {
            response_progress_info: response_progress_info,
            response_current_job: response_current_job,
        };
        if (!("type" in message && "data" in message)) return progress_update_color(STATUS_COLORS.message_format_error);
        if (!(message.type in handler_mapping)) return progress_update_color(STATUS_COLORS.message_type_unknown);
        await handler_mapping[message.type](websocket, message.data);
    };
    websocket.addEventListener("open", () => {
        Object.defineProperty(navigator, "clipboard", {
            value: {
                writeText: text => {
                    window.clip_board = text;
                    return Promise.resolve();
                }
            },
            configurable: true
        });
        Object.assign(document.body.style, {
            position: "relative",
            top: "10px"
        });
        websocket.send(JSON.stringify({
            type: "request_progress_info",
            data: {}
        }))
        websocket.send(JSON.stringify({
            type: "request_current_job",
            data: {}
        }));
    });
})();
