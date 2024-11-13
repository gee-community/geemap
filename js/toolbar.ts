import type { AnyModel, RenderProps } from "@anywidget/types";
import { html, css, LitElement } from "lit";
import { property } from "lit/decorators.js";
import { legacyStyles } from './ipywidgets_styles';
import { loadFonts, updateChildren } from "./utils";

import './tab_panel';

export interface ToolbarModel {
    children: any;
    expanded: boolean;
}

export class Toolbar extends LitElement {
    static get componentName() {
        return `toolbar-panel`;
    }

    static styles = [
        legacyStyles,
        css`
            .container {
                padding: 0 4px 2px 4px;
            }`,
    ];

    private _model: AnyModel<ToolbarModel> | undefined = undefined;
    private static modelNameToViewName = new Map<keyof ToolbarModel, keyof Toolbar | null>([
        ["children", null],
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
            <div class="container">
                <tab-panel .tabs=${[{icon: '&#xe875;'}, {icon: '&#xe869;'}]}>
                    <slot name="layer-manager"></slot>
                    <slot name="toolbar"></slot>
                </tab-panel>
            </div>
        `;
    }

    updated(changedProperties: any) {
        // Update the model properties so they're reflected in Python.
        for (const [property, _] of changedProperties) {
            this._model?.set(property, this[property as keyof Toolbar]);
        }
        this._model?.save_changes();
    }

    private onLayerVisibilityChanged(event: Event) {
        const target = event.target as HTMLInputElement;
        this.visible = target.checked;
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

    updateChildren(manager, model);
    model.on("change:children", () => {
        updateChildren(manager, model);
    });
}

export default { render };
