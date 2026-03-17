// ==UserScript==
// @name         Verse Lingua
// @namespace    https://github.com/abdullah-al-jaber
// @version      2.0
// @description  Translate novel with Google Translate
// @author       Retro Boy
// @match        https://translate.google.com/*
// @run-at       document-idle
// @grant        none
// @require      https://cdn.jsdelivr.net/npm/progressbar.js@0.8.0/dist/progressbar.min.js'
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
    };
    const CHAR_LIMIT = 5000;
    const host = document.createElement("div");
    Object.assign(host.style, {
        position: "fixed",
        right: "20px",
        bottom: "20px",
        zIndex: "9999",
        border: "2px solid black",
        borderRadius: "50px",
    });
    document.documentElement.appendChild(host);
    const shadow = host.attachShadow({ mode: "open" });
    const progress = document.createElement("div");
    progress.hidden = true;
    shadow.appendChild(progress);
    const wait_for_element = async (selector) => {
        return (
            document.querySelector(selector) ||
            new Promise((resolve) => {
                const observer = new MutationObserver(() => {
                    const element = document.querySelector(selector);
                    if (element) (observer.disconnect(), resolve(element));
                });
                observer.observe(document, { childList: true, subtree: true });
            })
        );
    };
    const translate = async (text) => {};
    const response_progress_info = async (websocket, data) => {
        if (!("percentage" in data)) return (progress.style.backgroundColor = STATUS_COLORS.message_data_unknown);
        
    };
    const response_current_job = async (websocket, data) => {
        if (!("current_index" in data && "text" in data)) return (progress.style.backgroundColor = STATUS_COLORS.message_data_unknown);
        if (document.title == "Just a moment...") return (progress.style.backgroundColor = STATUS_COLORS.cloudflare_challenge);
        websocket.send(JSON.stringify({ type: "submit_text", data: { current_index: data.current_index, text: await translate(data.text) } }));
        websocket.send(JSON.stringify({ type: "request_current_job", data: {} }));
    };
    const websocket = new WebSocket("ws://127.0.0.1:6969");
    websocket.onopen = () => (progress.hidden = false);
    websocket.onclose = () => (progress.hidden = true);
    websocket.onerror = () => (progress.style.backgroundColor = STATUS_COLORS.ws_error);
    websocket.onmessage = async (event) => {
        const message = JSON.parse(event.data);
        const handler_mapping = {
            response_progress_info: response_progress_info,
            response_current_job: response_current_job,
        };
        if (!("type" in message && "data" in message)) return (progress.style.backgroundColor = STATUS_COLORS.message_format_error);
        if (!(message.type in handler_mapping)) return (progress.style.backgroundColor = STATUS_COLORS.message_type_unknown);
        await handler_mapping[message.type](websocket, message.data);
    };
    websocket.addEventListener("open", () => {
        setInterval(() => websocket.send(JSON.stringify({ type: "request_progress_info", data: {} })), 2000);
        websocket.send(JSON.stringify({ type: "request_current_job", data: {} }));
    });
})();
