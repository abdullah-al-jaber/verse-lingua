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
        idle: "magenta",
        ws_error: "red",
        message_format_error: "brown",
        message_type_unknown: "orange",
        message_data_unknown: "yellow",
        cloudflare_challenge: "green",
        waiting: "cyan",
        wrong_site: "gray",
        text_too_long: "teal",
    };
    const INPUT_ELEMENT_SELECTOR = ".er8xn";
    const OUTPUT_ELEMENT_SELECTOR = ".lRu31";
    const MAX_CHAR_LIMIT = 5000;
    const host = document.createElement("div");
    Object.assign(host, { hidden: true });
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
    const container = document.createElement("div");
    Object.assign(container.style, {
        width: "50px",
        height: "50px",
    });
    var ProgressBar = require("progressbar.js");
    const circle = new ProgressBar.Circle(container, {
        strokeWidth: 10,
        trailWidth: 10,
        color: STATUS_COLORS.idle,
        trailColor: "#eeeeee",
        easing: "easeInOut",
        duration: 1400,
        svgStyle: { width: "100%", height: "100%" },
        step: (state, circle) => circle.setText(Math.round(circle.value() * 100) + "%"),
    });
    circle.text.style.fontFamily = "monospace";
    circle.text.style.fontSize = "5em";
    circle.text.style.fontWeight = "700";
    shadow.appendChild(container);
    const wait_for_element = async (selector) => {
        const query = document.querySelector(selector);
        const promise = new Promise((resolve) => {
            const observer = new MutationObserver(() => {
                const element = document.querySelector(selector);
                if (element) (observer.disconnect(), resolve(element));
            });
            observer.observe(document, { childList: true, subtree: true });
        });
        return query || (await promise);
    };
    const progress_update_state = async (percentage) => {
        circle.animate(percentage / 100);
    };
    const progress_update_color = async (color) => {
        circle.path.setAttribute("stroke", color);
    };
    let translate_text = async (text) => {
        const input_element = await wait_for_element(INPUT_ELEMENT_SELECTOR);
        for (const string of ["", text]) {
            input_element.value = string;
            input_element.dispatchEvent(new Event("input", { bubbles: true }));
        }
        console.log(await wait_for_element(OUTPUT_ELEMENT_SELECTOR));
    };
    const translate = async (text) => {
        const lines = text.split("\n");
        const chunks = [];
        let current_chunk = "";
        for (const line of lines) {
            if (line.length > MAX_CHAR_LIMIT) {
                progress_update_color(STATUS_COLORS.text_too_long);
                throw new Error("TEXT TOO LONG !");
            } else if (current_chunk.length + line.length + 1 > MAX_CHAR_LIMIT) {
                if (current_chunk) chunks.push(current_chunk);
                current_chunk = line;
            } else {
                current_chunk += (current_chunk ? "\n" : "") + line;
            }
        }
        if (current_chunk) chunks.push(current_chunk);
        let output = "";
        for (const chunk in chunks) {
            output += (output ? "\n" : "") + (await translate_text(chunk));
        }
        return output;
    };
    const response_progress_info = async (websocket, data) => {
        if (!("percentage" in data)) return progress_update_color(STATUS_COLORS.message_data_unknown);
        await progress_update_state(data.percentage);
    };
    const response_current_job = async (websocket, data) => {
        if (!("current_index" in data && "text" in data)) return progress_update_color(STATUS_COLORS.message_data_unknown);
        if (document.title == "Just a moment...") return progress_update_color(STATUS_COLORS.cloudflare_challenge);
        if (window.location.hostname != "translate.google.com") return progress_update_color(STATUS_COLORS.wrong_site);
        websocket.send(JSON.stringify({ type: "submit_text", data: { current_index: data.current_index, text: await translate(data.text) } }));
        websocket.send(JSON.stringify({ type: "request_current_job", data: {} }));
    };
    const websocket = new WebSocket("ws://127.0.0.1:6969");
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
        setInterval(() => websocket.send(JSON.stringify({ type: "request_progress_info", data: {} })), 2000);
        websocket.send(JSON.stringify({ type: "request_current_job", data: {} }));
    });
})();
