import type { RenderProps } from "@anywidget/types";
import { html, css, TemplateResult } from "lit";
import { property } from "lit/decorators.js";

import { legacyStyles } from "./ipywidgets_styles";
import { LitWidget } from "./lit_widget";
import { loadFonts, updateChildren } from "./utils";

import "./container";

export interface LayerManagerModel {
    children: any;
    visible: boolean;
}

export class LayerManager extends LitWidget<LayerManagerModel, LayerManager> {
    static get componentName() {
        return `layer-manager`;
    }

    static override styles = [
        legacyStyles,
        css`
            .row {
                align-items: center;
                display: flex;
                gap: 4px;
                height: 28px;
            }

            .visibility-checkbox {
                margin: 2px;
            }

            .layer-manager-rows {
                display: flex;
                flex-direction: column;
                gap: 10px;
            }
        `,
    ];

    @property() visible: boolean = false;
    @property() override tabIndex: number = 0;
    @property() collapsed: boolean = true;

    modelNameToViewName(): Map<
        keyof LayerManagerModel,
        keyof LayerManager | null
    > {
        return new Map([
            ["children", null],
            ["visible", "visible"],
        ]);
    }

    override render(): TemplateResult {
        return html`
            <widget-container
                icon="layers"
                title=""
                .collapsed="${this.collapsed}"
                .hideCloseButton="${true}"
                .compactMode="${true}"
                .reverseHeader="${true}"
            >
                <div class="container">
                    <div class="layer-manager-rows">
                        <div class="row">
                            <input
                                type="checkbox"
                                class="visibility-checkbox"
                                .checked="${this.visible}"
                                @change="${this.onLayerVisibilityChanged}"
                            />
                            <span
                                class="legacy-text all-layers-text"
                                @click="${this.onLayerVisibilityChanged}"
                            >
                                All layers on/off</span
                            >
                        </div>
                        <slot></slot>
                    </div>
                </div>
            </widget-container>
        `;
    }

    private onLayerVisibilityChanged(_event: Event): void {
        this.visible = !this.visible;
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
