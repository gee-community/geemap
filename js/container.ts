import type { RenderProps } from "@anywidget/types";
import { css, html, TemplateResult } from "lit";
import { property } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";

import { legacyStyles } from "./ipywidgets_styles";
import { LitWidget } from "./lit_widget";
import { materialStyles } from "./styles";

export interface ContainerModel {
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
                padding-left: 4px;
                padding-right: 4px;
            }
        `,
    ];

    @property() title: string = "";
    @property() collapsed: boolean = false;
    @property() hideCloseButton: boolean = false;

    modelNameToViewName(): Map<keyof ContainerModel, keyof Container | null> {
        return new Map([
            ["collapsed", "collapsed"],
            ["title", "title"],
            ["hide_close_button", "hideCloseButton"],
        ]);
    }

    render() {
        return html`
            <div class="header">
                <button
                    class=${classMap({
                        "legacy-button": true,
                        primary: true,
                        "header-button": true,
                        hidden: this.hideCloseButton,
                    })}
                    @click="${this.onCloseButtonClicked}"
                >
                    <span class="material-symbols-outlined">&#xe5cd;</span>
                </button>
                <button
                    class="legacy-button header-button"
                    @click="${this.onCollapseToggled}"
                >
                    ${this.renderCollapseButtonIcon()}
                </button>
                <span
                    class=${classMap({
                        "legacy-text": true,
                        "header-text": true,
                        hidden: !this.title,
                    })}
                >
                    ${this.title}
                </span>
            </div>
            <div
                class=${classMap({
                    "widget-container": true,
                    hidden: this.collapsed,
                })}
            >
                <slot></slot>
            </div>
        `;
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
