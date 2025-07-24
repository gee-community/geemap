import type { RenderProps } from "@anywidget/types";
import { css, html, HTMLTemplateResult, nothing, TemplateResult } from "lit";
import { property } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";

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

    static override styles = [
        legacyStyles,
        materialStyles,
        css`
            .container {
                background: var(--jp-layout-color1);
                border-radius: 4.5px;
                box-shadow: 4px 5px 8px 0px #9e9e9e;
            }

            div {
                background-color: var(--colab-primary-surface-color, --jp-layout-color1, white);
            }

            .header {
                display: flex;
                gap: 4px;
                padding: 4px;
            }

            .reversed {
                flex-direction: row-reverse;
            }

            .icon {
                align-items: center;
                display: flex;
                font-size: 20px;
                height: 28px;
                justify-content: center;
                padding: 0 4px;
            }

            .widget-container {
                padding: 8px 12px 12px 12px;
            }

            .hidden {
                display: none;
            }

            .header-button {
                font-size: 16px;
                height: 28px;
                width: 28px;
            }

            .compact-header-button {
                background: transparent;
                font-size: 16px;
                height: 28px;
                width: 28px;
            }

            .header-text {
                align-content: center;
                flex-grow: 1;
                padding: 0 12px 0 0;
            }

            .left-padding {
                padding-left: 8px;
            }
        `,
    ];

    @property({ type: String }) icon: string = "";
    @property({ type: String }) override title: string = "";
    @property({ type: Boolean }) collapsed: boolean = false;
    @property({ type: Boolean }) hideCloseButton: boolean = false;
    @property({ type: Boolean }) compactMode: boolean = false;
    @property({ type: Boolean }) noHeader: boolean = false;
    @property({ type: Boolean }) reverseHeader: boolean = false;

    modelNameToViewName(): Map<keyof ContainerModel, keyof Container | null> {
        return new Map([
            ["icon", "icon"],
            ["collapsed", "collapsed"],
            ["title", "title"],
            ["hide_close_button", "hideCloseButton"],
        ]);
    }

    override render() {
        return html`
            <div class="container">
                ${this.noHeader ? nothing : this.renderHeader()}
                <div class="widget-container ${this.collapsed ? "hidden" : ""}">
                    <slot></slot>
                </div>
            </div>
        `;
    }

    private renderHeader(): TemplateResult {
        return this.compactMode ? this.renderCompactHeader() : html`
            <div class="header ${this.reverseHeader ? "reversed" : ""}">
                ${this.renderIcon()}
                ${this.title ? this.renderTitle() : nothing}
                ${this.renderCollapseButton()}
                ${this.renderCloseButton()}
            </div>`;
    }

    private renderCompactHeader(): TemplateResult {
        return html`<div class="header ${this.reverseHeader ? "reversed" : ""}">
            ${this.renderCollapseButton()}
            ${(this.title && !this.collapsed) ? this.renderTitle() : nothing}
            ${this.renderCloseButton()}
        </div>`;
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
        return html`<span
            class="${classMap({
                "legacy-text": true,
                "header-text": true,
                "left-padding":
                    this.compactMode && this.title && !this.reverseHeader,
            })}"
            >${this.title}</span
        >`;
    }

    private onCloseButtonClicked(): void {
        this.dispatchEvent(new CustomEvent("close-clicked", {}));
    }

    private onCollapseToggled(): void {
        this.collapsed = !this.collapsed;
        this.dispatchEvent(new CustomEvent("collapse-clicked", {}));
    }

    private renderIcon(): TemplateResult {
        return html`<span class="icon material-symbols-outlined">
                        ${this.icon}
                    </span>`
    }

    private renderCollapseButton(): TemplateResult {
        let icon: TemplateResult;
        if (this.compactMode) {
            icon = this.renderIcon();
        } else if (this.collapsed) {
            icon = html`<span class="material-symbols-outlined"
                >&#xf830;</span
            >`;
        } else {
            icon = html`<span class="material-symbols-outlined">&#xf507;</span>`;
        }
        return html`<button
            class="${classMap({
            'legacy-button': true,
            'header-button': !this.compactMode,
            'compact-header-button': this.compactMode,
            'active': !this.collapsed,
        })}"
            class="legacy-button header-button"
            @click="${this.onCollapseToggled}"
        >
            ${icon}
        </button>`
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