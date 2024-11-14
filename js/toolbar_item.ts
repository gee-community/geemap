import type { AnyModel, RenderProps } from "@anywidget/types";
import { html, css, LitElement } from "lit";
import { property } from "lit/decorators.js";
import { classMap } from 'lit/directives/class-map.js';

import { legacyStyles } from './ipywidgets_styles';
import { loadFonts } from "./utils";
import { materialStyles } from "./styles";

export interface ToolbarItemModel {
    active: boolean;
    icon: string;
    // Note: "tooltip" is already used by ipywidgets.
    tooltip_: string;
}

export class ToolbarItem extends LitElement {
    static get componentName() {
        return `tool-button`;
    }

    static styles = [
        legacyStyles,
        materialStyles,
        css`
            button {
                font-size: 16px !important;
                height: 32px;
                padding: 0px 0px 0px 4px;
                width: 32px;
                user-select: none;
            }
        `,
    ];

    private _model: AnyModel<ToolbarItemModel> | undefined = undefined;
    private static modelNameToViewName = new Map<keyof ToolbarItemModel, keyof ToolbarItem | null>([
        ["active", "active"],
        ["icon", "icon"],
        ["tooltip_", "tooltip_"],
    ]);

    set model(model: AnyModel<ToolbarItemModel>) {
        this._model = model;
        for (const [modelKey, widgetKey] of ToolbarItem.modelNameToViewName) {
            if (widgetKey) {
                // Get initial values from the Python model.
                (this as any)[widgetKey] = model.get(modelKey);
                // Listen for updates to the model.
                model.on(`change:${modelKey}`, () => {
                    (this as any)[widgetKey] = model.get(modelKey);
                });
            }
        }
    }

    @property({ type: Boolean })
    active: boolean = false;

    @property({ type: String })
    icon: string = '';

    @property({ type: String })
    tooltip_: string = '';

    render() {
        return html`
            <button
                class=${classMap({
            'legacy-button': true,
            'primary': true,
            'active': this.active,
        })}
                title="${this.tooltip_}"
                @click="${this.onClick}">
                <span class="material-symbols-outlined">${this.icon}</span>
            </button>`;
    }

    updated(changedProperties: any) {
        // Update the model properties so they're reflected in Python.
        for (const [property, _] of changedProperties) {
            this._model?.set(property, this[property as keyof ToolbarItem]);
        }
        this._model?.save_changes();
    }

    private onClick(event: Event) {
        this.active = !this.active;
    }
}

// Without this check, there's a component registry issue when developing locally.
if (!customElements.get(ToolbarItem.componentName)) {
    customElements.define(ToolbarItem.componentName, ToolbarItem);
}

async function render({ model, el }: RenderProps<ToolbarItemModel>) {
    loadFonts();
    const manager = <ToolbarItem>document.createElement(ToolbarItem.componentName);
    manager.model = model;
    el.appendChild(manager);
}

export default { render };
