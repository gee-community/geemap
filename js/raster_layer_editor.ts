import {
    css,
    html,
    nothing,
    LitElement,
    PropertyValues,
    TemplateResult,
} from "lit";
import { property, query, queryAll } from "lit/decorators.js";

import { legacyStyles } from "./ipywidgets_styles";
import { LegendCustomization } from "./legend_customization";
import { materialStyles, flexStyles } from "./styles";
import { SelectOption, renderSelect } from "./utils";
import { PaletteEditor } from "./palette_editor";

import "./legend_customization";
import "./palette_editor";

enum ColorModel {
    RGB = "rgb",
    Gray = "gray",
}

enum ColorRamp {
    Palette = "palette",
    Gamma = "gamma",
}

export class RasterLayerEditor extends LitElement {
    static get componentName() {
        return `raster-layer-editor`;
    }

    static override styles = [
        flexStyles,
        legacyStyles,
        materialStyles,
        css`
            .horizontal-flex > button {
                height: 28px;
                width: 28px;
            }
        `,
    ];

    @property({ type: Array }) stretchOptions: Array<SelectOption> = [
        { label: "Custom", value: "custom" },
        { label: "1σ", value: "sigma-1" },
        { label: "2σ", value: "sigma-2" },
        { label: "3σ", value: "sigma-3" },
        { label: "90%", value: "percent-90" },
        { label: "98%", value: "percent-98" },
        { label: "100%", value: "percent-100" },
    ];
    @property({ type: Array }) colorModels: Array<SelectOption> = [
        { label: "1 band (Grayscale)", value: ColorModel.Gray },
        { label: "3 bands (RGB)", value: ColorModel.RGB },
    ];
    @property({ type: Array }) colorRamps: Array<SelectOption> = [
        { label: "Gamma", value: ColorRamp.Gamma },
        { label: "Palette", value: ColorRamp.Palette },
    ];

    @property({ type: String }) colorModel: string = "";
    @property({ type: Array }) bandNames: Array<string> = [];
    @property({ type: Array }) selectedBands: Array<string> = [];
    @property({ type: String }) stretch: string = this.stretchOptions[0].value;
    @property({ type: Number }) minValue: number | undefined = 0.0; // undefined is loading state.
    @property({ type: Number }) maxValue: number | undefined = 1.0; // undefined is loading state.
    @property({ type: Boolean }) minAndMaxValuesLocked: boolean = false;
    @property({ type: Number }) opacity: number = 1.0;
    @property({ type: String }) colorRamp: string = ColorRamp.Gamma;
    @property({ type: Number }) gamma: number = 1.0;
    @property({ type: Array }) colormaps: Array<string> = [];

    @query("palette-editor") paletteEditor?: PaletteEditor;
    @query("legend-customization") legendCustomization?: LegendCustomization;
    @queryAll("#band-selection select") bandSelects!: NodeListOf<HTMLInputElement>;

    @query("#min") private minInput!: HTMLInputElement;
    @query("#max") private maxInput!: HTMLInputElement;

    override connectedCallback() {
        super.connectedCallback();
        this.colorModel =
            this.bandNames.length > 1 ? ColorModel.RGB : ColorModel.Gray;
    }

    getVisualizationOptions(): any {
        const visOptions = {
            bands: this.selectedBands,
            min: this.minValue,
            max: this.maxValue,
            opacity: this.opacity,
        } as any;
        if (this.colorModel === ColorModel.Gray) {
            if (this.colorRamp === ColorRamp.Palette) {
                visOptions.palette = this.paletteEditor?.paletteTokens ?? [];
            } else if (this.colorRamp === ColorRamp.Gamma) {
                visOptions.gamma = this.gamma;
            }
        } else if (this.colorModel === ColorModel.RGB) {
            visOptions.gamma = this.gamma;
        }
        if (this.legendCustomization) {
            visOptions.legend = this.legendCustomization.getLegendData();
        }
        return visOptions;
    }

    override render(): TemplateResult {
        return html`
            <div class="vertical-flex">
                <div class="horizontal-flex">
                    ${this.colorModels.map((model) =>
                        this.renderColorModelRadio(model)
                    )}
                </div>
                <div id="band-selection" class="horizontal-flex">
                    ${this.selectedBands.map((band) =>
                        this.renderBandSelection(band)
                    )}
                </div>
                <div class="horizontal-flex">
                    <span class="legacy-text">Stretch:</span>
                    ${renderSelect(
                        this.stretchOptions,
                        this.stretch,
                        this.onStretchChanged
                    )}
                    <button
                        class="legacy-button"
                        @click="${this.onRefreshButtonClicked}"
                    >
                        <span class="material-symbols-outlined">refresh</span>
                    </button>
                </div>
                <div class="horizontal-flex">
                    <span class="legacy-text">Range:</span>
                    <input
                        type="text"
                        class="legacy-text-input"
                        id="min"
                        name="min"
                        .value="${this.minValue ?? "Loading..."}"
                        @keydown="${this.onInputKeyDown}"
                        @change="${this.onMinTextChanged}"
                        ?disabled="${this.minAndMaxValuesLocked}"
                    />
                    <span class="legacy-text">to</span>
                    <input
                        type="text"
                        class="legacy-text-input"
                        id="max"
                        name="max"
                        .value="${this.maxValue ?? "Loading..."}"
                        @keydown="${this.onInputKeyDown}"
                        @change="${this.onMaxTextChanged}"
                        ?disabled="${this.minAndMaxValuesLocked}"
                    />
                </div>
                <div class="horizontal-flex">
                    <span class="legacy-text">Opacity:</span>
                    <input
                        type="range"
                        class="legacy-slider"
                        id="opacity"
                        name="opacity"
                        min="0"
                        max="1.0"
                        step="0.01"
                        .value=${this.opacity}
                        @input=${this.onOpacityChanged}
                    />
                    <span class="legacy-text">${this.opacity.toFixed(2)}</span>
                </div>
                ${this.renderPaletteGammaSelector()}
                ${this.renderPaletteEditor()}
                ${this.renderGammaSlider()}
                ${this.renderLegendCustomization()}
            </div>
        `;
    }

    private renderPaletteGammaSelector(): TemplateResult | typeof nothing {
        if (this.colorModel === ColorModel.Gray) {
            return html`
                <div class="horizontal-flex">
                    ${this.colorRamps.map((model) =>
                        this.renderColorRampRadio(model)
                    )}
                </div>
            `;
        }
        return nothing;
    }

    private renderPaletteEditor(): TemplateResult | typeof nothing {
        if (
            this.colorRamp === ColorRamp.Palette &&
            this.colorModel === ColorModel.Gray
        ) {
            return html`
                <palette-editor .colormaps="${this.colormaps}">
                    <slot></slot>
                </palette-editor>
            `;
        }
        return nothing;
    }

    private renderLegendCustomization(): TemplateResult | typeof nothing {
        if (
            this.colorRamp === ColorRamp.Palette &&
            this.colorModel === ColorModel.Gray
        ) {
            return html`<legend-customization></legend-customization>`;
        }
        return nothing;
    }

    private renderGammaSlider(): TemplateResult | typeof nothing {
        if (
            this.colorRamp === ColorRamp.Gamma ||
            this.colorModel === ColorModel.RGB
        ) {
            return html`
                <div class="horizontal-flex">
                    <span class="legacy-text">Gamma:</span>
                    <input
                        type="range"
                        class="legacy-slider"
                        id="gamma"
                        name="gamma"
                        min="0.1"
                        max="10"
                        step="0.01"
                        .value=${this.gamma}
                        @input=${this.onGammaChanged}
                    />
                    <span class="legacy-text">${this.gamma.toFixed(2)}</span>
                </div>
            `;
        }
        return nothing;
    }

    private renderColorModelRadio(option: SelectOption): TemplateResult {
        return html`
            <span>
                <input
                    type="radio"
                    class="legacy-radio"
                    id="${option.value}"
                    name="color-model"
                    value="${option.value}"
                    @click="${this.onColorModelChanged}"
                    ?checked="${this.colorModel === option.value}"
                />
                <label class="legacy-text">${option.label}</label>
            </span>
        `;
    }

    private renderColorRampRadio(option: SelectOption): TemplateResult {
        return html`
            <span>
                <input
                    type="radio"
                    class="legacy-radio"
                    id="${option.value}"
                    name="color-ramp"
                    value="${option.value}"
                    @click="${this.onColorRampChanged}"
                    ?checked="${this.colorRamp === option.value}"
                />
                <label class="legacy-text">${option.label}</label>
            </span>
        `;
    }

    private onColorRampChanged(event: Event): void {
        this.colorRamp = (event.target as HTMLInputElement).value;
    }

    private renderBandSelection(value: string): TemplateResult {
        return renderSelect(this.bandNames, value, this.onBandSelectionChanged);
    }

    private onRefreshButtonClicked(event: Event): void {
        event.stopImmediatePropagation();
        this.calculateBandStats();
    }

    private onOpacityChanged(event: Event): void {
        this.opacity = (event.target as HTMLInputElement).valueAsNumber;
    }

    private onGammaChanged(event: Event): void {
        this.gamma = (event.target as HTMLInputElement).valueAsNumber;
    }

    private onInputKeyDown(event: KeyboardEvent): void {
        event.stopPropagation();  // Prevent the event from bubbling up to the document.
    }

    private onMinTextChanged(_event: Event): void {
        this.minValue = +this.minInput.value;  // Convert input string to number.
    }

    private onMaxTextChanged(_event: Event): void {
        this.maxValue = +this.maxInput.value;  // Convert input string to number.
    }

    private calculateBandStats(): void {
        if (this.stretch === "custom") {
            return;
        }
        this.minValue = undefined;
        this.maxValue = undefined;
        this.dispatchEvent(
            new CustomEvent("calculate-band-stats", {
                bubbles: true,
                composed: true,
            })
        );
    }

    private onStretchChanged(event: Event): void {
        this.stretch = (event.target as HTMLInputElement).value;
        this.minAndMaxValuesLocked = this.stretch !== "custom";
    }

    private onBandSelectionChanged(_event: Event): void {
        this.selectedBands = this.getSelectedBands();
    }

    private onColorModelChanged(event: Event): void {
        this.colorModel = (event.target as HTMLInputElement).value;
    }

    override updated(changedProperties: PropertyValues<RasterLayerEditor>): void {
        super.updated(changedProperties);

        if (changedProperties.has("colorModel")) {
            if (this.colorModel === ColorModel.Gray) {
                this.selectedBands = [this.bandNames[0]];
            } else if (this.colorModel == ColorModel.RGB) {
                this.selectedBands = [
                    this.bandNames[0],
                    this.bandNames[0],
                    this.bandNames[0],
                ];
            }
        }

        if (
            changedProperties.has("selectedBands") ||
            changedProperties.has("stretch")
        ) {
            this.calculateBandStats();
        }
    }

    private getSelectedBands(): Array<string> {
        return Array.from(this.bandSelects).map(input => input.value);
    }
}

// Without this check, there's a component registry issue when developing locally.
if (!customElements.get(RasterLayerEditor.componentName)) {
    customElements.define(RasterLayerEditor.componentName, RasterLayerEditor);
}
