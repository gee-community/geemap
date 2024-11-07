import type { RenderProps } from "@anywidget/types";
import { html, css, TemplateResult } from "lit";
import { property } from "lit/decorators.js";

import { legacyStyles } from "./ipywidgets_styles";
import { LitWidget } from "./lit_widget";
import { loadFonts, updateChildren } from "./utils";

export interface LayerManagerModel {
    children: any;
    visible: boolean;
}

export class LayerManager extends LitWidget<
    LayerManagerModel,
    LayerManager
> {
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

    @property() visible: boolean = false;

    modelNameToViewName(): Map<
        keyof LayerManagerModel,
        keyof LayerManager | null
    > {
        return new Map([
            ["children", null],
            ["visible", "visible"],
        ]);
    }

    render(): TemplateResult {
        return html`
            <div class="container">
                <div class="row">
                    <input
                        type="checkbox"
                        class="visibility-checkbox"
                        .checked="${this.visible}"
                        @change="${this.onLayerVisibilityChanged}"
                    />
                    <span class="legacy-text all-layers-text"
                        >All layers on/off</span
                    >
                </div>
                <slot></slot>
            </div>
        `;
    }

    private onLayerVisibilityChanged(event: Event): void {
        const target = event.target as HTMLInputElement;
        this.visible = target.checked;
    }
}

// Without this check, there's a component registry issue when developing locally.
if (!customElements.get(LayerManager.componentName)) {
    customElements.define(LayerManager.componentName, LayerManager);
}

async function render({ model, el }: RenderProps<LayerManagerModel>) {
    loadFonts();
    const manager = <LayerManager>(
        document.createElement(LayerManager.componentName)
    );
    manager.model = model;
    el.appendChild(manager);

    updateChildren(manager, model);
    model.on("change:children", () => {
        updateChildren(manager, model);
    });
}

export default { render };
