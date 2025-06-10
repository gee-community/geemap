import type { RenderProps } from "@anywidget/types";
import { css, html, TemplateResult } from "lit";
import { property, query } from "lit/decorators.js";

import { legacyStyles } from "./ipywidgets_styles";
import { LitWidget } from "./lit_widget";
import { RasterLayerEditor } from "./raster_layer_editor";
import { updateChildren } from "./utils";
import { VectorLayerEditor } from "./vector_layer_editor";

import "./container";
import "./palette_editor";
import "./raster_layer_editor";
import "./vector_layer_editor";

export interface LayerEditorModel {
    layer_name: string;
    layer_type: string;
    children: Array<any>;

    // Band names in the image (if applicable).
    band_names: Array<string>;
    // Colormaps available to select.
    colormaps: Array<string>;
}

export class LayerEditor extends LitWidget<LayerEditorModel, LayerEditor> {
    static get componentName(): string {
        return `layer-editor`;
    }

    static override styles = [
        legacyStyles,
        css`
            .confirm-button {
                padding: 0 20px;
            }

            .confirm-button-row {
                display: flex;
                gap: 4px;
                margin-top: 4px;
            }

            .editor-container {
                max-height: 250px;
                max-width: 350px;
                overflow-y: auto;
            }
        `,
    ];

    @property({ type: String }) layerName: string = "";
    @property({ type: String }) layerType: string = "";
    @property({ type: Array }) bandNames: Array<string> = [];
    @property({ type: Array }) colormaps: Array<string> = [];

    @query("raster-layer-editor") rasterEditor?: RasterLayerEditor;
    @query("vector-layer-editor") vectorEditor?: VectorLayerEditor;

    modelNameToViewName(): Map<
        keyof LayerEditorModel,
        keyof LayerEditor | null
    > {
        return new Map([
            ["layer_name", "layerName"],
            ["layer_type", "layerType"],
            ["band_names", "bandNames"],
            ["colormaps", "colormaps"],
            ["children", null],
        ]);
    }

    override onCustomMessage(msg: any): void {
        const msgId = msg.id;
        const response = msg.response;

        if (msgId === "band-stats") {
            this.handleBandStatsResponse(response);
        } else if (msgId === "palette") {
            this.handlePaletteResponse(response);
        } else if (msgId === "fields") {
            this.handleFieldResponse(response);
        } else if (msgId === "field-values") {
            this.handleFieldValuesResponse(response);
        }
    }

    override render(): TemplateResult {
        return html`
            <widget-container
                .title="${this.layerName}"
                @close-clicked="${this.onCloseButtonClicked}"
            >
                <div class="editor-container">
                    ${this.renderLayerEditorType()}
                </div>
                <div class="confirm-button-row">
                    <button
                        class="legacy-button primary confirm-button"
                        @click="${this.onImportClicked}"
                    >
                        Import
                    </button>
                    <button
                        class="legacy-button confirm-button"
                        @click="${this.onApplyClicked}"
                    >
                        Apply
                    </button>
                </div>
            </widget-container>
        `;
    }

    private renderLayerEditorType(): TemplateResult {
        if (this.layerType == "raster") {
            return html`
                <raster-layer-editor
                    .bandNames="${this.bandNames}"
                    .colormaps="${this.colormaps}"
                    @calculate-band-stats="${this.calculateBandStats}"
                    @calculate-palette="${this.calculatePalette}"
                >
                    <slot></slot>
                </raster-layer-editor>
            `;
        } else if (this.layerType == "vector") {
            return html`
                <vector-layer-editor
                    .newLayerName="${this.layerName + " style"}"
                    .colormaps="${this.colormaps}"
                    @calculate-fields="${this.calculateFields}"
                    @calculate-field-values="${this.calculateFieldValues}"
                    @calculate-palette="${this.calculatePalette}"
                >
                    <slot></slot>
                </vector-layer-editor>
            `;
        }
        return html`<div><span>Vis params are uneditable</span></div>`;
    }

    private onCloseButtonClicked(_: Event): void {
        this.model?.send({ type: "click", id: "close" });
    }

    private onApplyClicked(_event: Event): void {
        this.sendCompletion("apply");
    }

    private onImportClicked(_event: Event): void {
        this.sendCompletion("import");
    }

    private sendCompletion(completionType: string): void {
        if (this.rasterEditor) {
            this.model?.send({
                id: completionType,
                type: "click",
                detail: this.rasterEditor.getVisualizationOptions(),
            });
        } else if (this.vectorEditor) {
            this.model?.send({
                id: completionType,
                type: "click",
                detail: this.vectorEditor.getVisualizationOptions(),
            });
        }
    }

    private calculateBandStats(_event: Event): void {
        if (this.rasterEditor) {
            this.model?.send({
                id: "band-stats",
                type: "calculate",
                detail: {
                    bands: this.rasterEditor.selectedBands,
                    stretch: this.rasterEditor.stretch,
                },
            });
        }
    }

    private handleBandStatsResponse(response: any): void {
        if (this.rasterEditor) {
            // Verify the stretch matches in case we get responses out-of-order.
            if (response.stretch === this.rasterEditor.stretch) {
                this.rasterEditor.minValue = response.min;
                this.rasterEditor.maxValue = response.max;
            }
        }
    }

    private calculatePalette(event: CustomEvent): void {
        this.model?.send({
            id: "palette",
            type: "calculate",
            detail: {
                colormap: event.detail.colormap,
                classes: event.detail.classes,
                palette: event.detail.palette,
                bandMin: this.rasterEditor?.minValue ?? 0.0,
                bandMax: this.rasterEditor?.maxValue ?? 1.0,
            },
        });
    }

    private getLegendClassLabels(palette: string): Array<string> {
        if (palette === "") {
            return [];
        }
        const length = palette.split(",").length;
        return Array.from({ length }, (_, i) => `Class ${i + 1}`);
    }

    private handlePaletteResponse(response: any): void {
        const paletteEditor = (this.rasterEditor || this.vectorEditor)
            ?.paletteEditor;
        const legendCustomization = (this.rasterEditor || this.vectorEditor)?.legendCustomization;
        if (paletteEditor && response.palette) {
            paletteEditor.palette = response.palette;
        }
        if (legendCustomization) {
            legendCustomization.labels = this.getLegendClassLabels(response.palette);
        }
    }

    private calculateFields(_event: CustomEvent): void {
        this.model?.send({ id: "fields", type: "calculate", detail: {} });
    }

    private handleFieldResponse(response: any): void {
        if (this.vectorEditor) {
            const fields = response.fields;
            const values = response["field-values"];
            this.vectorEditor.fields = fields;
            this.vectorEditor.fieldValues = values;
            this.vectorEditor.selectedField =
                fields.length > 0 ? fields[0] : "";
            this.vectorEditor.selectedFieldValue =
                values.length > 0 ? values[0] : "";
        }
    }

    private calculateFieldValues(_event: CustomEvent): void {
        if (this.vectorEditor) {
            this.model?.send({
                id: "field-values",
                type: "calculate",
                detail: {
                    field: this.vectorEditor?.selectedField,
                },
            });
        }
    }

    private handleFieldValuesResponse(response: any): void {
        if (this.vectorEditor) {
            const values = response["field-values"];
            this.vectorEditor.fieldValues = values;
            this.vectorEditor.selectedFieldValue =
                values.length > 0 ? values[0] : "";
        }
    }
}

// Without this check, there's a component registry issue when developing locally.
if (!customElements.get(LayerEditor.componentName)) {
    customElements.define(LayerEditor.componentName, LayerEditor);
}

async function render({ model, el }: RenderProps<LayerEditorModel>) {
    const widget = document.createElement(LayerEditor.componentName) as LayerEditor;
    widget.model = model;
    el.appendChild(widget);

    // Update the palette visualization.
    updateChildren(widget, model);
    model.on("change:children", () => {
        updateChildren(widget, model);
    });
}

export default { render };