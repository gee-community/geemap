import type { RenderProps } from "@anywidget/types";
import { html, css } from "lit";
import { property } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";

import { legacyStyles } from "./ipywidgets_styles";
import { LitWidget } from "./lit_widget";
import { materialStyles } from "./styles";
import { Alignment } from "./tab_panel";
import { loadFonts, updateChildren } from "./utils";

import "./container";
import "./tab_panel";


export interface ToolbarModel {
    accessory_widgets: any;
    main_tools: any;
    extra_tools: any
    expanded: boolean;
    tab_index: number;
}

export class Toolbar extends LitWidget<
    ToolbarModel,
    Toolbar
> {
    static get componentName() {
        return `toolbar-panel`;
    }

    static styles = [
        legacyStyles,
        materialStyles,
        css`
            .hide {
                display: none;
            }

            .expanded {
                display: block; !important
            }

            .tools-container {
                padding: 4px;
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
            ["accessory_widgets", null],
            ["main_tools", null],
            ["extra_tools", null],
            ["expanded", "expanded"],
            ["tab_index", "tab_index"],
        ]);
    }

    @property()
    expanded: boolean = false;

    @property()
    tab_index: number = 0;

    render() {
        return html`
            <widget-container
                .collapsted="${false}"
                .hideCloseButton=${true}
                .noHeader="${true}">
                <tab-panel
                    .index="${this.tab_index}"
                    .tabs=${[{ icon: "layers", width: 74 }, { icon: "build" }]}
                    .alignment="${Alignment.RIGHT}"
                    @tab-changed=${(e: CustomEvent<number>) => {
                    this.tab_index = e.detail;
                }}>
                    <div class="accessory-container">
                        <slot name="accessory-widget"></slot>
                    </div>
                    <div class="tools-container">
                        <slot name="main-tools"></slot>
                        <slot
                            name="extra-tools"
                            class="${classMap({
                    hide: !this.expanded,
                    expanded: this.expanded,
                })}"></slot>
                    </div>
                </tab-panel>
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

    const accessoryWidgetEl = document.createElement("div");
    accessoryWidgetEl.slot = "accessory-widget";
    manager.appendChild(accessoryWidgetEl);

    updateChildren(accessoryWidgetEl, model, "accessory_widgets");
    model.on("change:accessory_widgets", () => {
        updateChildren(accessoryWidgetEl, model, "accessory_widgets");
    });

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
