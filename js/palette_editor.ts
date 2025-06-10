import { css, html, LitElement, PropertyValues } from "lit";
import { property, query } from "lit/decorators.js";

import { ColorPicker } from "./color_picker";
import { legacyStyles } from "./ipywidgets_styles";
import { flexStyles, materialStyles } from "./styles";
import { SelectOption, renderSelect } from "./utils";

import "./color_picker";

export class PaletteEditor extends LitElement {
    static get componentName() {
        return `palette-editor`;
    }

    static override styles = [
        flexStyles,
        legacyStyles,
        materialStyles,
        css`
            .horizontal-flex > .legacy-button {
                flex-shrink: 0;
                height: 28px;
                width: 28px;
            }
        `,
    ];

    @property({ type: Array }) classesOptions: Array<SelectOption> = [
        { label: "Any", value: "any" },
        ...Array.from({ length: 7 }, (_, i) => ({
            label: `${i + 3}`,
            value: `${i + 3}`,
        })),
    ];
    @property({ type: String }) classes: string = "any";
    @property({ type: Array }) colormaps: Array<string> = [];
    @property({ type: String }) colormap: string = "Custom";
    @property({ type: String }) palette: string = "";

    @query('color-picker') colorPicker!: ColorPicker;

    paletteTokens: Array<string> = [];

    override render() {
        return html`
            <div class="vertical-flex">
                <div class="horizontal-flex">
                    <span class="legacy-text">Colormap:</span>
                    ${renderSelect(
                        this.colormaps,
                        this.colormap,
                        this.onColormapChanged
                    )}
                    <span class="legacy-text">Classes:</span>
                    ${renderSelect(
                        this.classesOptions,
                        this.classes,
                        this.onClassesChanged
                    )}
                </div>
                <div class="horizontal-flex">
                    <span class="legacy-text">Palette:</span>
                    <input
                        type="text"
                        class="legacy-text-input"
                        id="palette"
                        name="palette"
                        .value="${this.palette}"
                        ?disabled="${this.colormap !== "Custom"}"
                        @change="${this.onPaletteChanged}"
                    />
                </div>
                <slot></slot>
                <div class="horizontal-flex">
                    <span class="legacy-text">Add/remove color:</span>
                    <color-picker></color-picker>
                    <button
                        class="legacy-button"
                        @click="${this.onAddButtonClicked}"
                    >
                        <span class="material-symbols-outlined">add</span>
                    </button>
                    <button
                        class="legacy-button"
                        @click="${this.onSubtractButtonClicked}"
                    >
                        <span class="material-symbols-outlined">remove</span>
                    </button>
                    <button
                        class="legacy-button"
                        @click="${this.onClearButtonClicked}"
                    >
                        <span class="material-symbols-outlined">ink_eraser</span>
                    </button>
                </div>
            </div>
        `;
    }

    override updated(changedProperties: PropertyValues<PaletteEditor>): void {
        super.updated(changedProperties);
        if (changedProperties.has("palette")) {
            if (this.palette === "") {
                this.paletteTokens = [];
            } else {
                this.paletteTokens = this.palette.split(",").map(color => color.trim());
            }
        }
    }

    private sendOnPaletteChangedEvent(): void {
        this.dispatchEvent(
            new CustomEvent("calculate-palette", {
                detail: {
                    colormap: this.colormap,
                    classes: this.classes,
                    palette: this.palette,
                },
                bubbles: true,
                composed: true,
            })
        );
    }

    private onClassesChanged(event: Event): void {
        const target = event.target as HTMLInputElement;
        this.classes = target.value;
        this.sendOnPaletteChangedEvent();
    }

    private onColormapChanged(event: Event): void {
        const target = event.target as HTMLInputElement;
        this.colormap = target.value;
        this.sendOnPaletteChangedEvent();
    }

    private onPaletteChanged(event: Event): void {
        const target = event.target as HTMLInputElement;
        this.palette = target.value;
        this.sendOnPaletteChangedEvent();
    }

    private onAddButtonClicked(_event: Event): void {
        this.colormap = "Custom";
        this.classes = "any";

        const tokens = [...this.paletteTokens];
        tokens.push(this.colorPicker.value);
        this.palette = tokens.join(", ");

        this.sendOnPaletteChangedEvent();
    }

    private onSubtractButtonClicked(_event: Event): void {
        this.colormap = "Custom";
        this.classes = "any";

        const tokens = [...this.paletteTokens];
        tokens.pop();
        this.palette = tokens.join(", ");

        this.sendOnPaletteChangedEvent();
    }

    private onClearButtonClicked(_event: Event): void {
        this.colormap = "Custom";
        this.classes = "any";
        this.palette = "";

        this.sendOnPaletteChangedEvent();
    }
}

// Without this check, there's a component registry issue when developing locally.
if (!customElements.get(PaletteEditor.componentName)) {
    customElements.define(PaletteEditor.componentName, PaletteEditor);
}