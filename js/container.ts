import type { RenderProps } from "@anywidget/types";
import { css, html, HTMLTemplateResult, nothing, TemplateResult } from "lit";
import { property } from "lit/decorators.js";

import { legacyStyles } from "./ipywidgets_styles";
import { LitWidget } from "./lit_widget";
import { materialStyles } from "./styles";

export interface ContainerModel {
    icon: string;
    title: string;
    collapsed: boolean;
    hide_close_button: boolean;
}

export class Container extends LitWidget<ContainerModel, Container> {
    static get componentName(): string {
        return `widget-container`;
    }

    static styles = [
        legacyStyles,
        materialStyles,
        css`
            .header {
                display: flex;
                gap: 4px;
                padding: 4px;
            }

            .icon {
                align-items: center;
                display: flex;
                font-size: 20px;
                height: 28px;
                justify-content: center;
            }

            .widget-container {
                padding: 4px;
            }

            .hidden {
                display: none;
            }

            .header-button {
                font-size: 16px;
                height: 28px;
                width: 28px;
            }

            .header-text {
                align-content: center;
                flex-grow: 1;
                padding-right: 12px;
            }
        `,
    ];

    @property({ type: String }) icon: string = "";
    @property({ type: String }) title: string = "";
    @property({ type: Boolean }) collapsed: boolean = false;
    @property({ type: Boolean }) hideCloseButton: boolean = false;

    modelNameToViewName(): Map<keyof ContainerModel, keyof Container | null> {
        return new Map([
            ["icon", "icon"],
            ["collapsed", "collapsed"],
            ["title", "title"],
            ["hide_close_button", "hideCloseButton"],
        ]);
    }

    render() {
        return html`
            <div class="header">
                <span class="icon material-symbols-outlined">${this.icon}</span>
                ${this.renderTitle()}
                <button
                    class="legacy-button header-button"
                    @click="${this.onCollapseToggled}"
                >
                    ${this.renderCollapseButtonIcon()}
                </button>
                ${this.renderCloseButton()}
            </div>
            <div class="widget-container ${this.collapsed ? "hidden" : ""}">
                <slot></slot>
            </div>
        `;
    }

    private renderCloseButton(): HTMLTemplateResult | typeof nothing {
        if (this.hideCloseButton) {
            return nothing;
        }
        return html`
            <button
                class="legacy-button primary header-button"
                @click="${this.onCloseButtonClicked}"
            >
                <span class="material-symbols-outlined">&#xe5cd;</span>
            </button>
        `;
    }

    private renderTitle(): HTMLTemplateResult {
        return html`<span class="legacy-text header-text">${this.title}</span>`;
    }

    private onCloseButtonClicked(): void {
        this.dispatchEvent(new CustomEvent("close-clicked", {}));
    }

    private onCollapseToggled(): void {
        this.collapsed = !this.collapsed;
        this.dispatchEvent(new CustomEvent("collapse-clicked", {}));
    }

    private renderCollapseButtonIcon(): TemplateResult {
        if (this.collapsed) {
            return html`<span class="material-symbols-outlined"
                >&#xf830;</span
            >`;
        }
        return html`<span class="material-symbols-outlined">&#xf507;</span>`;
    }
}

// Without this check, there's a component registry issue when developing locally.
if (!customElements.get(Container.componentName)) {
    customElements.define(Container.componentName, Container);
}

async function render({ model, el }: RenderProps<ContainerModel>) {
    const manager = document.createElement(
        Container.componentName
    ) as Container;
    manager.model = model;
    el.appendChild(manager);
}

export default { render };