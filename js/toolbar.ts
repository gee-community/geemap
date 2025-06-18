import type { RenderProps } from "@anywidget/types";
import { html, css } from "lit";
import { property } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";

import { legacyStyles } from "./ipywidgets_styles";
import { LitWidget } from "./lit_widget";
import { materialStyles } from "./styles";
import { loadFonts, updateChildren } from "./utils";

import "./container";
import "./tab_panel";

export interface ToolbarModel {
    main_tools: any;
    extra_tools: any;
    expanded: boolean;
}

export class Toolbar extends LitWidget<ToolbarModel, Toolbar> {
    static get componentName() {
        return `toolbar-panel`;
    }

    static override styles = [
        legacyStyles,
        materialStyles,
        css`
            .hide {
                display: none;
            }

            .expanded {
                display: block; !important
            }

            slot[name="extra-tools"] {
                margin-top: 4px;
            }

            ::slotted([slot="main-tools"]),
            ::slotted([slot="extra-tools"])  {
                align-items: center;
                display: inline-grid;
                grid-template-columns: auto auto auto;
                grid-gap: 4px;
                justify-items: center;
            }
        `,
    ];

    modelNameToViewName(): Map<keyof ToolbarModel, keyof Toolbar | null> {
        return new Map([
            ["main_tools", null],
            ["extra_tools", null],
            ["expanded", "expanded"],
        ]);
    }

    @property()
    expanded: boolean = false;

    override render() {
        return html`
            <widget-container
                icon="build"
                title=""
                .collapsed="${true}"
                .hideCloseButton=${true}
                .compactMode="${true}"
                .reverseHeader="${true}"
            >
                <div class="tools-container">
                    <slot name="main-tools"></slot>
                    <slot
                        name="extra-tools"
                        class="${classMap({
                            hide: !this.expanded,
                            expanded: this.expanded,
                        })}"
                    ></slot>
                </div>
            </widget-container>
        `;
    }
}

// Without this check, there's a component registry issue when developing locally.
if (!customElements.get(Toolbar.componentName)) {
    customElements.define(Toolbar.componentName, Toolbar);
}

async function render({ model, el }: RenderProps<ToolbarModel>) {
    loadFonts();
    const manager = <Toolbar>document.createElement(Toolbar.componentName);
    manager.model = model;
    el.appendChild(manager);

    const mainToolsEl = document.createElement("div");
    mainToolsEl.slot = "main-tools";
    manager.appendChild(mainToolsEl);

    updateChildren(mainToolsEl, model, "main_tools");
    model.on("change:main_tools", () => {
        updateChildren(mainToolsEl, model, "main_tools");
    });

    const extraToolsEl = document.createElement("div");
    extraToolsEl.slot = "extra-tools";
    manager.appendChild(extraToolsEl);

    updateChildren(extraToolsEl, model, "extra_tools");
    model.on("change:extra_tools", () => {
        updateChildren(extraToolsEl, model, "extra_tools");
    });
}

export default { render };
