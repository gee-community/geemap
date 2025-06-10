import { css, html, LitElement } from "lit";
import { property } from "lit/decorators.js";

import { legacyStyles } from "./ipywidgets_styles";

export class ColorPicker extends LitElement {
    static get componentName() {
        return `color-picker`;
    }

    static override styles = [
        legacyStyles,
        css`
            .color-swatch {
                border-radius: 0;
                height: 28px;
                padding: 0 2px;
                width: 28px;
            }

            .color-text {
                width: 80px;
            }

            .widget-inline-hbox {
                align-items: baseline;
                box-sizing: border-box;
                display: flex;
                flex-direction: row;
                line-height: 28px;
            }
        `,
    ];

    @property({ type: String }) value: string = "#000000";

    override render() {
        return html`
            <div class="widget-inline-hbox">
                <input
                    type="text"
                    class="legacy-text-input color-text"
                    .value="${this.value}"
                    @change="${this.onValueChanged}"
                >
                <input
                    type="color"
                    class="legacy-color color-swatch"
                    .value="${this.value}"
                    @change="${this.onValueChanged}"
                >
            </div>
        `;
    }

    private onValueChanged(event: Event): void {
        this.value = (event.target as HTMLInputElement).value;
        this.dispatchEvent(new CustomEvent("change", {}));
    }
}

// Without this check, there's a component registry issue when developing locally.
if (!customElements.get(ColorPicker.componentName)) {
    customElements.define(ColorPicker.componentName, ColorPicker);
}