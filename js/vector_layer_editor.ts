import { css, html, LitElement, nothing, TemplateResult } from "lit";
import { property, query } from "lit/decorators.js";

import { ColorPicker } from "./color_picker";
import { legacyStyles } from "./ipywidgets_styles";
import { LegendCustomization } from "./legend_customization";
import { PaletteEditor } from "./palette_editor";
import { flexStyles } from "./styles";
import { renderSelect } from "./utils";

import "./palette_editor";

export class VectorLayerEditor extends LitElement {
    static get componentName() {
        return `vector-layer-editor`;
    }

    static override styles = [
        flexStyles,
        legacyStyles,
        css`
            .style-by-attribute-checkbox {
                vertical-align: middle;
            }
        `,
    ];

    static pointShapes: Array<string> = [
        "circle",
        "square",
        "diamond",
        "cross",
        "plus",
        "pentagram",
        "hexagram",
        "triangle",
        "triangle_up",
        "triangle_down",
        "triangle_left",
        "triangle_right",
        "pentagon",
        "hexagon",
        "star5",
        "star6",
    ];

    static lineTypes: Array<string> = [
        "solid",
        "dotted",
        "dashed",
    ];

    @property({ type: Array }) colormaps: Array<string> = [];
    @property({ type: String }) newLayerName: string = "";
    @property({ type: Number }) opacity: number = 1.0;
    @property({ type: Number }) pointSize: number = 3.0;
    @property({ type: String }) pointShape: string = VectorLayerEditor.pointShapes[0];
    @property({ type: Number }) lineWidth: number = 2.0;
    @property({ type: String }) lineType: string = VectorLayerEditor.lineTypes[0];
    @property({ type: Number }) fillOpacity: number = 1.0;
    @property({ type: Boolean }) shouldStyleByAttribute: boolean = false;
    @property({ type: Array }) fields: Array<string> = [];
    @property({ type: String }) selectedField: string = "";
    @property({ type: Array }) fieldValues: Array<string> = [];
    @property({ type: String }) selectedFieldValue: string = "";

    @query("palette-editor") paletteEditor?: PaletteEditor;
    @query("legend-customization") legendCustomization?: LegendCustomization;
    @query("#color-picker") colorPicker!: ColorPicker;
    @query("#fill-color-picker") fillColorPicker!: ColorPicker;

    getVisualizationOptions(): any {
        let visParams = {
            layerName: this.newLayerName,
            color: this.colorPicker.value,
            opacity: this.opacity,
            pointSize: this.pointSize,
            pointShape: this.pointShape,
            lineWidth: this.lineWidth,
            lineType: this.lineType,
            fillColor: this.fillColorPicker.value,
            fillOpacity: this.fillOpacity,
            shouldStyleByAttribute: this.shouldStyleByAttribute,
        } as any;
        if (this.shouldStyleByAttribute) {
            visParams.palette = this.paletteEditor?.paletteTokens ?? [];
            visParams.field = this.selectedField;
        }
        if (this.legendCustomization) {
            visParams.legend = this.legendCustomization.getLegendData();
        }
        return visParams;
    }

    override render() {
        return html`
            <div class="vertical-flex">
                <div class="horizontal-flex">
                    <span class="legacy-text">New layer name:</span>
                    <input
                        type="text"
                        class="legacy-text-input"
                        id="new-layer-name"
                        name="new-layer-name"
                        .value="${this.newLayerName}"
                        @change="${this.onNewLayerNameChanged}"
                    />
                </div>
                <div class="horizontal-flex">
                    <color-picker id="color-picker"></color-picker>
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
                <div class="horizontal-flex">
                    <span class="legacy-text">Point size:</span>
                    <input
                        type="number"
                        class="legacy-text-input"
                        id="point-size"
                        name="point-size"
                        min="1"
                        max="50"
                        .value="${this.pointSize}"
                        @change="${this.onPointSizeChanged}"
                    />
                    <span class="legacy-text">Point shape:</span>
                    ${renderSelect(VectorLayerEditor.pointShapes, this.pointShape, this.onPointShapeChanged)}
                </div>
                <div class="horizontal-flex">
                    <span class="legacy-text">Line width:</span>
                    <input
                        type="number"
                        class="legacy-text-input"
                        id="line-width"
                        name="line-width"
                        min="1"
                        max="50"
                        .value="${this.lineWidth}"
                        @change="${this.onLineWidthChanged}"
                    />
                    <span class="legacy-text">Line type:</span>
                    ${renderSelect(VectorLayerEditor.lineTypes, this.lineType, this.onLineTypeChanged)}
                </div>
                <div class="horizontal-flex">
                    <span class="legacy-text">Fill:</span>
                    <color-picker id="fill-color-picker"></color-picker>
                    <span class="legacy-text">Opacity:</span>
                    <input
                        type="range"
                        class="legacy-slider"
                        id="fill-opacity"
                        name="fill-opacity"
                        min="0"
                        max="1.0"
                        step="0.01"
                        .value=${this.fillOpacity}
                        @input=${this.onFillOpacityChanged}
                    />
                    <span class="legacy-text">${this.fillOpacity.toFixed(2)}</span>
                </div>
                <div class="horizontal-flex">
                    <span>
                        <input
                            class="style-by-attribute-checkbox"
                            type="checkbox"
                            .checked="${this.shouldStyleByAttribute}"
                            @change="${this.onShouldStyleByAttributeChanged}"
                        />
                        <span class="legacy-text all-layers-text"
                            >Style by attribute</span
                        >
                    </span>
                </div>
                ${this.renderStyleByAttributeSettings()}
                ${this.renderLegendCustomization()}
            </div>
        `;
    }

    private renderStyleByAttributeSettings(): TemplateResult | typeof nothing {
        if (!this.shouldStyleByAttribute) {
            return nothing;
        }
        return html`
            <div class="horizontal-flex">
                <span class="legacy-text">Field:</span>
                ${renderSelect(this.fields, this.selectedField, this.onStyleAttributeChanged)}
                <span class="legacy-text">Values:</span>
                ${renderSelect(this.fieldValues, this.selectedFieldValue, this.onValueChanged)}
            </div>
            <palette-editor .colormaps="${this.colormaps}">
                <slot></slot>
            </palette-editor>
        `;
    }

    private renderLegendCustomization(): TemplateResult | typeof nothing {
        if (this.shouldStyleByAttribute) {
            return html`<legend-customization></legend-customization>`;
        }
        return nothing;
    }

    private onNewLayerNameChanged(event: Event): void {
        this.newLayerName = (event.target as HTMLInputElement).value;
    }

    private onOpacityChanged(event: Event): void {
        this.opacity = (event.target as HTMLInputElement).valueAsNumber;
    }

    private onPointSizeChanged(event: Event): void {
        this.pointSize = (event.target as HTMLInputElement).valueAsNumber;
    }

    private onPointShapeChanged(event: Event): void {
        this.pointShape = (event.target as HTMLInputElement).value;
    }

    private onLineWidthChanged(event: Event): void {
        this.lineWidth = (event.target as HTMLInputElement).valueAsNumber;
    }

    private onLineTypeChanged(event: Event): void {
        this.lineType = (event.target as HTMLInputElement).value;
    }

    private onFillOpacityChanged(event: Event): void {
        this.fillOpacity = (event.target as HTMLInputElement).valueAsNumber;
    }

    private onShouldStyleByAttributeChanged(event: Event): void {
        this.shouldStyleByAttribute = (event.target as HTMLInputElement).checked;
        this.dispatchEvent(new CustomEvent("calculate-fields", {}));
    }

    private onStyleAttributeChanged(event: Event): void {
        this.selectedField = (event.target as HTMLInputElement).value;
        this.dispatchEvent(new CustomEvent("calculate-field-values", {}));
    }

    private onValueChanged(event: Event): void {
        this.selectedFieldValue = (event.target as HTMLInputElement).value;
    }
}

// Without this check, there's a component registry issue when developing locally.
if (!customElements.get(VectorLayerEditor.componentName)) {
    customElements.define(VectorLayerEditor.componentName, VectorLayerEditor);
}
