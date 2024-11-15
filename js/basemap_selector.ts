import type { RenderProps } from "@anywidget/types";
import { css, html, PropertyValues, TemplateResult } from "lit";
import { property, query } from "lit/decorators.js";

import { legacyStyles } from "./ipywidgets_styles";
import { materialStyles } from "./styles";
import { loadFonts } from "./utils";
import { LitWidget } from "./lit_widget";

export interface BasemapSelectorModel {
    basemaps: string[];
    value: string;
}

export class BasemapSelector extends LitWidget<
    BasemapSelectorModel,
    BasemapSelector
> {
    static get componentName() {
        return `basemap-selector`;
    }

    static styles = [
        legacyStyles,
        materialStyles,
        css`
            .row-container {
                align-items: center;
                display: flex;
                height: 32px;
                width: 200px;
            }

            .row-button {
                font-size: 14px;
                height: 26px;
                margin: 4px;
                width: 26px;
            }
        `,
    ];

    modelNameToViewName(): Map<
        keyof BasemapSelectorModel,
        keyof BasemapSelector
    > {
        return new Map([
            ["basemaps", "basemaps"],
            ["value", "value"],
        ]);
    }

    @property({ type: Array }) basemaps: string[] = [];
    @property({ type: String }) value: string = "";
    @query('select') selectElement!: HTMLSelectElement;

    render(): TemplateResult {
        return html`
            <div class="row-container">
                <select class="legacy-select" @change=${this.onChange}>
                    ${this.basemaps.map((basemap) => html`<option>${basemap}</option>`)}
                </select>
                <button
                    class="legacy-button primary row-button close-button"
                    @click="${this.onCloseClicked}"
                >
                    <span class="close-icon material-symbols-outlined">&#xe5cd;</span>
                </button>
            </div>`;
    }

    override update(changedProperties: PropertyValues): void {
        if (changedProperties.has("value") && this.selectElement) {
            this.selectElement.value = this.value;
        }
        super.update(changedProperties);
    }


    private onChange(event: Event) {
        const target = event.target as HTMLInputElement;
        this.value = target.value;
    }

    private onCloseClicked(_: Event) {
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
