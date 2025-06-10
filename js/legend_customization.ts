import {
    css,
    html,
    HTMLTemplateResult,
    LitElement,
    nothing,
    TemplateResult,
} from "lit";
import { property } from "lit/decorators.js";

import { legacyStyles } from "./ipywidgets_styles";
import { SelectOption } from "./utils";
import { flexStyles } from "./styles";

enum LegendType {
    Linear = "linear",
    Step = "step",
}

export class LegendCustomization extends LitElement {
    static get componentName() {
        return `legend-customization`;
    }

    static override styles = [
        flexStyles,
        legacyStyles,
        css`
            .hidden {
                display: none;
            }

            .legend-checkbox {
                vertical-align: middle;
            }
        `,
    ];

    @property({ type: Array }) legendTypes: Array<SelectOption> = [
        { label: "Linear", value: LegendType.Linear },
        { label: "Step", value: LegendType.Step },
    ];

    @property({ type: Boolean }) showLegend: boolean = false;
    @property({ type: String }) legendType: string = "linear";
    @property({ type: String }) override title: string = "Legend";
    @property({ type: String }) labels: Array<string> = [];

    override render() {
        return html`
            <div class="vertical-flex">
                <div class="horizontal-flex">
                    <span>
                        <input
                            type="checkbox"
                            class="legend-checkbox"
                            .checked="${this.showLegend}"
                            @change="${this.showLegendToggleChanged}"
                        />
                        <span class="legacy-text">Legend</span>
                    </span>
                </div>
                ${this.renderLegendContents()}
            </div>
        `;
    }

    getLegendData(): void | undefined {
        if (this.showLegend) {
            const data: any = {type: this.legendType};
            if (this.legendType === LegendType.Step) {
                data.title = this.title;
                data.labels = this.labels;
            }
            return data;
        }
        return undefined;
    }

    private renderLegendTypeRadio(option: SelectOption): TemplateResult {
        return html`
            <span>
                <input
                    type="radio"
                    class="legacy-radio"
                    id="${option.value}"
                    name="legend-type"
                    value="${option.value}"
                    @click="${this.onLegendTypeChanged}"
                    ?checked="${this.legendType === option.value}"
                />
                <label class="legacy-text">${option.label}</label>
            </span>
        `;
    }

    private renderLegendContents(): TemplateResult | typeof nothing {
        if (this.showLegend) {
            return html`
                <div class="horizontal-flex">
                    ${this.legendTypes.map((model) =>
                        this.renderLegendTypeRadio(model)
                    )}
                </div>
                ${this.renderLegendTitleAndLabels()}
            `;
        }
        return nothing;
    }

    private renderLegendTitleAndLabels(): HTMLTemplateResult | typeof nothing {
        if (this.legendType === LegendType.Step) {
            return html`
                <div class="horizontal-flex">
                    <span class="legacy-text">Legend title:</span>
                    <input
                        type="text"
                        class="legacy-text-input"
                        id="labels"
                        name="labels"
                        .value="${this.title}"
                        @change="${this.onTitleChanged}"
                    />
                </div>
                <div class="horizontal-flex">
                    <span class="legacy-text">Legend labels:</span>
                    <input
                        type="text"
                        class="legacy-text-input"
                        id="labels"
                        name="labels"
                        .value="${this.labels.join(", ")}"
                        @change="${this.onLabelsChanged}"
                    />
                </div>
            `;
        }
        return nothing;
    }

    private showLegendToggleChanged(event: Event): void {
        this.showLegend = (event.target as HTMLInputElement).checked;
    }

    private onLegendTypeChanged(event: Event): void {
        this.legendType = (event.target as HTMLInputElement).value;
    }

    private onTitleChanged(event: Event): void {
        this.title = (event.target as HTMLInputElement).value;
    }

    private onLabelsChanged(event: Event): void {
        const labels = (event.target as HTMLInputElement).value;
        this.labels = labels.split(",").map(token => token.trim());
    }
}

// Without this check, there's a component registry issue when developing locally.
if (!customElements.get(LegendCustomization.componentName)) {
    customElements.define(
        LegendCustomization.componentName,
        LegendCustomization
    );
}
