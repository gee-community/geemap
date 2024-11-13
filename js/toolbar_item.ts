import type { AnyModel, RenderProps } from "@anywidget/types";
import { html, css, LitElement } from "lit";
import { property } from "lit/decorators.js";
import { classMap } from 'lit/directives/class-map.js';
import { unsafeHTML } from 'lit/directives/unsafe-html.js';

import { legacyStyles } from './ipywidgets_styles';
import { loadFonts } from "./utils";

export interface ToolbarItemModel {
    active: boolean;
    icon: string;
    tooltip: string;
}

export class ToolbarItem extends LitElement {
    static get componentName() {
        return `tool-button`;
    }

    static styles = [
        legacyStyles,
        css`
            button {
                height: auto;
                padding: 0px 0px 0px 4px;
                width: auto;
            }
        `,
    ];

    private _model: AnyModel<ToolbarItemModel> | undefined = undefined;
    private static modelNameToViewName = new Map<keyof ToolbarItemModel, keyof ToolbarItem | null>([
        ["active", "active"],
        ["icon", "icon"],
        ["tooltip", "tooltip"],
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
    tooltip: string = '';

    render() {
        // Strictly validate the icon, since we are using unsafeHTML
        // directive to render the HTML entity directly. 
        if (this.icon && !this.icon.match(/^&#x[a-fA-F0-9]+;$/)) {
            this.icon = '';
        }
        return html`
            <button
                class=${classMap({
            'legacy-button': true,
            'primary': true,
            'active': this.active,
        })}
                title="${this.tooltip}"
                @click="${this.onClick}">
                <span class="material-symbols-outlined">${unsafeHTML(this.icon)}</span>
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
