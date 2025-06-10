import type { RenderProps } from "@anywidget/types";
import { html, css } from "lit";
import { property } from "lit/decorators.js";
import { classMap } from 'lit/directives/class-map.js';

import { legacyStyles } from './ipywidgets_styles';
import { LitWidget } from "./lit_widget";
import { materialStyles } from "./styles";
import { loadFonts } from "./utils";

export interface ToolbarItemModel {
    active: boolean;
    primary: boolean;
    icon: string;
    // Note: "tooltip" is already used by ipywidgets.
    tooltip_text: string;
}

export class ToolbarItem extends LitWidget<ToolbarItemModel, ToolbarItem> {
    static get componentName() {
        return `tool-button`;
    }

    static override styles = [
        legacyStyles,
        materialStyles,
        css`
            button {
                font-size: 16px !important;
                height: 32px;
                padding: 0px 0px 0px 4px;
                width: 32px;
            }
        `,
    ];

    modelNameToViewName(): Map<keyof ToolbarItemModel, keyof ToolbarItem> {
        return new Map([
            ["active", "active"],
            ["primary", "primary"],
            ["icon", "icon"],
            ["tooltip_text", "tooltip_text"],
        ]);
    }

    @property({ type: Boolean })
    active: boolean = false;

    @property({ type: Boolean })
    primary: boolean = true;

    @property({ type: String })
    icon: string = '';

    @property({ type: String })
    tooltip_text: string = '';

    override render() {
        return html`
            <button
                class=${classMap({
            'legacy-button': true,
            'primary': this.primary,
            'active': this.active,
        })}
                title="${this.tooltip_text}"
                @click="${this.onClick}">
                <span class="material-symbols-outlined">${this.icon}</span>
            </button>`;
    }

    private onClick(_: Event) {
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
