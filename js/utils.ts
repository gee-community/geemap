// TODO(sufyanAbbasi): Write tests for this file.

import type { AnyModel } from "@anywidget/types";
import { IWidgetManager, WidgetModel } from "@jupyter-widgets/base";
import { html, TemplateResult } from "lit";

async function unpackModels(
    modelIds: Array<string>,
    manager: IWidgetManager
): Promise<Array<WidgetModel>> {
    return Promise.all(
        modelIds.map((id) => manager.get_model(id.slice("IPY_MODEL_".length)))
    );
}

export function loadFonts() {
    if (!document.querySelector(".custom-fonts")) {
        const styleElement = document.createElement("style");
        styleElement.classList.add("custom-fonts");
        styleElement.textContent =
            '@import "https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined";';
        document.body.appendChild(styleElement);
    }
}

export async function updateChildren(
    container: HTMLElement,
    model: AnyModel<any>,
    property = "children"
) {
    let children = model.get(property);
    if (!Array.isArray(children)) {
        children = [children];
    }
    const child_models = await unpackModels(children, model.widget_manager);
    const child_views = await Promise.all(
        child_models.map((model) => model.widget_manager.create_view(model))
    );
    container.innerHTML = ``;
    for (const child_view of child_views) {
        container.appendChild(child_view.el);
    }
}

export function reverseMap<K, V>(map: Map<K, V>): Map<V, K> {
    const reversedMap = new Map<V, K>();
    for (const [key, value] of map.entries()) {
        if (value != null) {
            reversedMap.set(value, key);
        }
    }
    return reversedMap;
}

export interface SelectOption {
    label: string;
    value: string;
}

export function renderSelect(
    options: Array<SelectOption> | Array<string>,
    value: string,
    callback: (event: Event) => void
): TemplateResult {
    const emptyOptions = options.length === 0;
    const newOptions = (emptyOptions ? ["---"] : options).map((option) => {
        const isObject = typeof option === "object";
        const optValue = `${isObject ? option.value : option}`;
        const optLabel = `${isObject ? option.label : option}`;
        return html`
            <option value="${optValue}" ?selected="${value === optValue}">
                ${optLabel}
            </option>
        `;
    });
    return html`
        <select
            class="legacy-select"
            @change="${callback}"
            ?disabled=${emptyOptions}
        >
            ${newOptions}
        </select>
    `;
}
