import type { RenderProps } from "@anywidget/types";
import { css, html, PropertyValues, TemplateResult } from "lit";
import { property } from "lit/decorators.js";

import { legacyStyles } from "./ipywidgets_styles";
import { LitWidget } from "./lit_widget";
import { flexStyles, materialStyles } from "./styles";
import { loadFonts, renderSelect } from "./utils";

import "./container";

export interface BasemapSelectorModel {
    basemaps: { [id: string]: string[] };
    provider: string;
    resource: string;
}

export class BasemapSelector extends LitWidget<
    BasemapSelectorModel,
    BasemapSelector
> {
    static get componentName(): string {
        return `basemap-selector`;
    }

    static override styles = [
        flexStyles,
        legacyStyles,
        materialStyles,
        css`
            .horizontal-flex {
                gap: 8px;
            }

            .legacy-text {
                min-width: 70px;
            }

            .legacy-button {
                padding: 0 12px;
            }
        `,
    ];

    modelNameToViewName(): Map<
        keyof BasemapSelectorModel,
        keyof BasemapSelector
    > {
        return new Map([
            ["basemaps", "basemaps"],
            ["provider", "provider"],
            ["resource", "resource"],
        ]);
    }

    @property({ type: Object }) basemaps: { [id: string]: string[] } = {};
    @property({ type: String }) provider: string = "";
    @property({ type: String }) resource: string = "";

    override render(): TemplateResult {
        return html`
            <widget-container
                icon="map"
                title="Basemap"
                @close-clicked="${this.onCloseClicked}"
            >
                <div class="vertical-flex">
                    <div class="horizontal-flex">
                        <span class="legacy-text">Provider</span>
                        ${renderSelect(
                            Object.keys(this.basemaps),
                            this.provider,
                            this.onProviderChanged
                        )}
                    </div>
                    <div class="horizontal-flex">
                        <span class="legacy-text">Resource</span>
                        ${renderSelect(
                            this.getAvailableResources(),
                            this.resource,
                            this.onResourceChanged
                        )}
                    </div>
                    <div class="horizontal-flex ">
                        <button
                            class="legacy-button"
                            @click="${this.onCloseClicked}"
                        >
                            Cancel
                        </button>
                        <button
                            class="legacy-button primary"
                            @click="${this.onApplyClicked}"
                        >
                            Add basemap
                        </button>
                    </div>
                </div>
            </widget-container>
        `;
    }

    override update(changedProperties: PropertyValues): void {
        if (changedProperties.has("provider")) {
            const resources = this.getAvailableResources();
            this.resource = resources.length > 0 ? resources[0] : "";
        }
        super.update(changedProperties);
    }

    private getAvailableResources(): string[] {
        if (this.provider in this.basemaps) {
            return this.basemaps[this.provider];
        }
        return [];
    }

    private onProviderChanged(event: Event): void {
        this.provider = (event.target as HTMLInputElement).value;
    }

    private onResourceChanged(event: Event): void {
        this.resource = (event.target as HTMLInputElement).value;
    }

    private onApplyClicked(_: Event): void {
        this.model?.send({ type: "click", id: "apply" });
    }

    private onCloseClicked(_: Event): void {
        this.model?.send({ type: "click", id: "close" });
    }
}

// Without this check, there's a component registry issue when developing locally.
if (!customElements.get(BasemapSelector.componentName)) {
    customElements.define(BasemapSelector.componentName, BasemapSelector);
}

function render({ model, el }: RenderProps<BasemapSelectorModel>) {
    loadFonts();
    const row = <BasemapSelector>(
        document.createElement(BasemapSelector.componentName)
    );
    row.model = model;
    el.appendChild(row);
}

export default { render };
