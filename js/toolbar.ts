import type { AnyModel, RenderProps } from "@anywidget/types";
import { html, css, LitElement } from "lit";
import { property } from "lit/decorators.js";
import { legacyStyles } from "./ipywidgets_styles";
import { loadFonts, updateChildren } from "./utils";

import "./tab_panel";
import { classMap } from "lit/directives/class-map.js";
import { materialStyles } from "./styles";

export interface ToolbarModel {
    accessory_widget: any;
    main_tools: any;
    extra_tools: any
    expanded: boolean;
}

export class Toolbar extends LitElement {
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

    private _model: AnyModel<ToolbarModel> | undefined = undefined;
    private static modelNameToViewName = new Map<keyof ToolbarModel, keyof Toolbar | null>([
        ["accessory_widget", null],
        ["main_tools", null],
        ["extra_tools", null],
        ["expanded", "expanded"],
    ]);

    set model(model: AnyModel<ToolbarModel>) {
        this._model = model;
        for (const [modelKey, widgetKey] of Toolbar.modelNameToViewName) {
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

    @property()
    expanded: boolean = false;

    render() {
        return html`
            <tab-panel .tabs=${[{icon: "layers"}, {icon: "build"}]}>
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
        `;
    }

    updated(changedProperties: any) {
        // Update the model properties so they're reflected in Python.
        for (const [property, _] of changedProperties) {
            this._model?.set(property, this[property as keyof Toolbar]);
        }
        this._model?.save_changes();
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

    updateChildren(accessoryWidgetEl, model, "accessory_widget");
    model.on("change:accessory_widget", () => {
        updateChildren(accessoryWidgetEl, model, "accessory_widget");
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
