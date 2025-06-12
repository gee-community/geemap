import type { RenderProps } from "@anywidget/types";
import { css, html, nothing, TemplateResult } from "lit";
import { property } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";

import { legacyStyles } from "./ipywidgets_styles";
import { materialStyles } from "./styles";
import { loadFonts } from "./utils";
import { LitWidget } from "./lit_widget";

export interface LayerManagerRowModel {
    name: string;
    visible: boolean;
    opacity: number;
    is_loading: boolean;
}

export class LayerManagerRow extends LitWidget<
    LayerManagerRowModel,
    LayerManagerRow
> {
    static get componentName() {
        return `layer-manager-row`;
    }

    static override styles = [
        legacyStyles,
        materialStyles,
        css`
            .row {
                align-items: center;
                display: flex;
                gap: 4px;
            }

            .layer-name {
                cursor: pointer;
                flex-grow: 1;
                max-width: 150px;
                overflow: hidden;
                text-overflow: ellipsis;
            }

            .row-button {
                font-size: 16px;
                height: 28px;
                width: 28px;
            }

            .layer-opacity-slider {
                width: 70px;
            }

            .layer-visibility-checkbox {
                margin: 2px;
            }

            .spinner {
                -webkit-animation: spin 2s linear infinite;
                animation: spin 2s linear infinite;
                border-radius: 50%;
                border: 4px solid var(--jp-widgets-input-border-color);
                border-top: 4px solid var(--jp-widgets-color);
                height: 12px;
                width: 12px;
            }

            @-webkit-keyframes spin {
                0% {
                    -webkit-transform: rotate(0deg);
                }
                100% {
                    -webkit-transform: rotate(360deg);
                }
            }

            @keyframes spin {
                0% {
                    transform: rotate(0deg);
                }
                100% {
                    transform: rotate(360deg);
                }
            }

            button.loading .spinner,
            button.loading:hover .close-icon,
            button.done-loading .close-icon {
                display: block;
            }

            button.loading .close-icon,
            button.loading:hover .spinner,
            button.done-loading .spinner {
                display: none;
            }

            .remove-layer-text {
                flex-grow: 1;
                padding-left: 22px;
            }

            .confirm-deletion-container {
                margin-top: 4px;
            }

            .confirm-deletion-container button {
                height: 28px;
                width: 70px;
            }
        `,
    ];

    modelNameToViewName(): Map<
        keyof LayerManagerRowModel,
        keyof LayerManagerRow | null
    > {
        return new Map([
            ["name", "name"],
            ["visible", "visible"],
            ["opacity", "opacity"],
            ["is_loading", "isLoading"],
        ]);
    }

    @property() name: string = "";
    @property() visible: boolean = true;
    @property() opacity: number = 1;
    @property() isLoading: boolean = false;
    @property() isConfirmDialogVisible: boolean = false;

    override render(): TemplateResult {
        return html`
            <div class="row">
                <input
                    type="checkbox"
                    class="layer-visibility-checkbox"
                    .checked="${this.visible}"
                    @click="${this.onLayerVisibilityChanged}"
                />
                <span
                    class="legacy-text layer-name"
                    @click="${this.onLayerVisibilityChanged}"
                >
                    ${this.name}
                </span>
                <input
                    type="range"
                    class="legacy-slider layer-opacity-slider"
                    min="0"
                    max="1"
                    step="0.01"
                    .value="${this.opacity}"
                    @input="${this.onLayerOpacityChanged}"
                />
                <button
                    class="legacy-button row-button settings-button"
                    @click="${this.onSettingsClicked}"
                >
                    <span class="material-symbols-outlined">settings</span>
                </button>
                <button
                    class=${classMap({
                        "legacy-button": true,
                        "row-button": true,
                        "delete-button": true,
                        loading: this.isLoading,
                        "done-loading": !this.isLoading,
                    })}
                    @click="${this.onDeleteClicked}"
                >
                    <div class="spinner"></div>
                    <span class="close-icon material-symbols-outlined"
                        >delete</span
                    >
                </button>
            </div>
            ${this.renderConfirmDialog()}
        `;
    }

    private renderConfirmDialog(): TemplateResult | typeof nothing {
        if (!this.isConfirmDialogVisible) {
            return nothing;
        }
        return html`
            <div class="row confirm-deletion-container">
                <span class="legacy-text remove-layer-text">Remove layer?</span>
                <button
                    class="legacy-button"
                    @click="${this.cancelDeletion}"
                >
                    No
                </button>
                <button
                    class="legacy-button primary confirm-deletion-button"
                    @click="${this.confirmDeletion}"
                >
                    Yes
                </button>
            </div>
        `;
    }

    private onLayerVisibilityChanged(_event: Event) {
        this.visible = !this.visible;
    }

    private onLayerOpacityChanged(event: Event) {
        const target = event.target as HTMLInputElement;
        this.opacity = parseFloat(target.value);
    }

    private onSettingsClicked(_: Event) {
        this.model?.send({ type: "click", id: "settings" });
    }

    private onDeleteClicked(_: Event) {
        this.isConfirmDialogVisible = true;
    }

    private confirmDeletion(_: Event) {
        this.model?.send({ type: "click", id: "delete" });
    }

    private cancelDeletion(_: Event) {
        this.isConfirmDialogVisible = false;
    }
}

// Without this check, there's a component registry issue when developing locally.
if (!customElements.get(LayerManagerRow.componentName)) {
    customElements.define(LayerManagerRow.componentName, LayerManagerRow);
}

function render({ model, el }: RenderProps<LayerManagerRowModel>) {
    loadFonts();
    const row = <LayerManagerRow>(
        document.createElement(LayerManagerRow.componentName)
    );
    row.model = model;
    el.appendChild(row);
}

export default { render };
