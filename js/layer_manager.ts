import type { AnyModel, RenderProps } from "@anywidget/types";
import { html, css, LitElement } from "lit";
import { property } from "lit/decorators.js";
import { legacyStyles } from './ipywidgets_styles';
import { updateChildren } from "./utils";

import "./common.css";

interface LayerManagerModel {
    children: any;
    visible: boolean;
}

export class LayerManager extends LitElement {
    static get componentName() {
        return `layer-manager`;
    }

    static styles = [
        legacyStyles,
        css`
            .container {
                padding: 0 4px 2px 4px;
            }

            .row {
                align-items: center;
                display: flex;
                gap: 4px;
                height: 30px;
            }

            .visibility-checkbox {
                margin: 2px;
            }
        `,
    ];

    private _model: AnyModel<LayerManagerModel> | undefined = undefined;
    private static modelNameToViewName = new Map<keyof LayerManagerModel, keyof LayerManager | null>([
        ["children", null],
        ["visible", "visible"],
    ]);

    set model(model: AnyModel<LayerManagerModel>) {
        this._model = model;
        for (const [modelKey, widgetKey] of LayerManager.modelNameToViewName) {
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
    visible: boolean = false;

    render() {
        return html`
            <div class="container">
                <div class="row">
                    <input
                        type="checkbox"
                        class="visibility-checkbox"
                        .checked="${this.visible}"
                        @change="${this.onLayerVisibilityChanged}"
                    />
                    <span class="legacy-text all-layers-text">All layers on/off</span>
                </div>
                <slot></slot>
            </div>
        `;
    }

    updated(changedProperties: any) {
        // Update the model properties so they're reflected in Python.
        for (const [property, _] of changedProperties) {
            this._model?.set(property, this[property as keyof LayerManager]);
        }
        this._model?.save_changes();
    }

    private onLayerVisibilityChanged(event: Event) {
        const target = event.target as HTMLInputElement;
        this.visible = target.checked;
    }
}

if (!customElements.get(LayerManager.componentName)) {
    customElements.define(LayerManager.componentName, LayerManager);
}

async function render({ model, el }: RenderProps<LayerManagerModel>) {
    const manager = <LayerManager>document.createElement(LayerManager.componentName);
    manager.model = model;
    el.appendChild(manager);

    updateChildren(manager, model);
    model.on("change:children", () => {
        updateChildren(manager, model);
    });
}

export default { render };
