import type { RenderProps } from "@anywidget/types";
import { html, css } from "lit";
import { property, query, queryAll } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";

import { legacyStyles } from "./ipywidgets_styles";
import { LitWidget } from "./lit_widget";
import { materialStyles } from "./styles";
import { loadFonts } from "./utils";

import { TabMode } from "./tab_panel";
import { unsafeHTML } from "lit/directives/unsafe-html.js";

export interface SearchTab {
    search: string,
    results: string[],
    selected: string,
    additional_html: string,
}

export interface SearchBarModel {
    expanded: boolean;
    tab_index: number;
    name_address_model: string,
    lat_lon_model: string,
    dataset_model: string,
}

export class SearchBar extends LitWidget<
    SearchBarModel,
    SearchBar
> {
    static get componentName() {
        return `search-bar`;
    }

    static styles = [
        legacyStyles,
        materialStyles,
        css`
            .row {
                display: flex;
            }

            .expand-button {
                border-radius: 5px;
                font-size: 16px;
                height: 28px;
                margin: 2px;
                user-select: none;
                width: 28px;
            }

            .hide {
                display: none;
            }

            .expanded {
                display: block; !important
            }

            input.search {
                margin: 2px;
                width: calc(100% - 4px);
            }

            ul.results {
                list-style-type: none;
                margin: 0;
                margin-bottom: 4px;
                max-width: 340px;
                padding: 0;
            }

            label.result {
                align-items: center;
                display: flex;
            }

            .import-button, .reset-button {
                margin: 0 2px 2px 2px;
                padding: 0 8px;
            }

            .dataset-select {
                margin-bottom: 2px;
                margin-right: 2px;
                max-width: 285px;
            }

            .additional-html-container {
                max-height: 300px;
                max-width: 340px;
                overflow: auto;
            }

            .additional-html-container pre {
                white-space: break-spaces;
            }
        `,
    ];

    modelNameToViewName(): Map<keyof SearchBarModel, keyof SearchBar> {
        return new Map([
            ["expanded", "expanded"],
            ["tab_index", "tab_index"],
            ["name_address_model", "nameAddressModel"],
            ["lat_lon_model", "latLonModel"],
            ["dataset_model", "datasetModel"],
        ]);
    }

    @property()
    expanded: boolean = false;

    @property()
    tab_index: number = 0;

    @property()
    nameAddressModel: string = JSON.stringify({
        search: "",
        results: [],
        selected: "",
        additional_html: "",
    });

    @property()
    latLonModel: string = JSON.stringify({
        search: "",
        results: [],
        selected: "",
        additional_html: "",
    });

    @property()
    datasetModel: string = JSON.stringify({
        search: "",
        results: [],
        selected: "",
        additional_html: "",
    });

    @query(".name-address-search")
    nameAddressSearch!: HTMLInputElement;

    @queryAll(".name-address-results input")
    nameAddressResults!: HTMLInputElement[];

    @query(".lat-lon-search")
    latLonSearch!: HTMLInputElement;

    @queryAll(".lat-lon-results input")
    latLonResults!: HTMLInputElement[];

    @query(".dataset-search")
    datasetSearch!: HTMLInputElement;

    render() {
        return html`
            <div class="row">
                <button
                    class=${classMap({
            "expand-button": true,
            "legacy-button": true,
            "active": this.expanded,
        })}
                    title="Search location/data"
                    @click="${this.onExpandClick}">
                    <span class="material-symbols-outlined">search</span>
                </button>
                <tab-panel
                    .index="${this.tab_index}"
                    .tabs=${[
                { name: "name/address", width: 110 },
                { name: "lat-lon", width: 110 },
                { name: "data", width: 110 }
            ]}
                    @tab-changed=${(e: CustomEvent<number>) => {
                this.tab_index = e.detail;
            }}
                    .mode="${TabMode.ALWAYS_SHOW}"
                    class="${classMap({
                hide: !this.expanded,
                expanded: this.expanded,
            })}">
                    <div class="name-address-container">
                        ${this.renderNameAddressSearch()}
                    </div>
                    <div class="lat-lon-container">
                        ${this.renderLatLonSearch()}
                    </div>
                    <div class="dataset-container">
                        ${this.renderDatasetSearch()}
                    </div>
                </tab-panel>
            </div>
        `;
    }

    private onExpandClick(_: Event) {
        this.expanded = !this.expanded;
    }

    private renderNameAddressSearch() {
        const nameAddressModel = JSON.parse(this.nameAddressModel) as SearchTab;
        const searchInput = html`<input
            class="legacy-input search name-address-search"
            type="search"
            placeholder="Search by place name or address, e.g., Paris"
            @keydown="${(e: KeyboardEvent) => {
                if (e.key === "Enter") {
                    e.preventDefault();
                    const nameAddressModel = JSON.parse(this.nameAddressModel) as SearchTab;
                    nameAddressModel.search = this.nameAddressSearch.value || "";
                    this.nameAddressModel = JSON.stringify(nameAddressModel);
                }
            }}" />`;
        const renderedInputs = [searchInput];
        if (nameAddressModel.results.length) {
            const results = html`
                ${nameAddressModel.results.map((result) => html`
                    <li>
                        <label class="result">
                            <input
                            type="radio"
                            name="name-address-result"
                            value="${result}"
                            .checked="${nameAddressModel.selected === result}"
                            @input="${(e: Event) => {
                    const input = (e.target as HTMLInputElement);
                    const nameAddressModel = JSON.parse(this.nameAddressModel) as SearchTab;
                    nameAddressModel.selected = input.value || "";
                    this.nameAddressModel = JSON.stringify(nameAddressModel);
                }}" />
                            <span>${result}</span>
                        </label>
                    </li>`)}
            `;
            renderedInputs.push(html`<ul class="results name-address-results">
                ${results}
            </ul>`);
        }
        renderedInputs.push(html`<div class="additional-html-container">
            ${unsafeHTML(nameAddressModel.additional_html)}
        </div>`);
        if (nameAddressModel.search ||
            nameAddressModel.results.length ||
            nameAddressModel.selected) {
            renderedInputs.push(html`<button
                    class="legacy-button primary reset-button"
                    @click="${() => {
                    this.nameAddressModel = JSON.stringify({
                        search: "",
                        results: [],
                        selected: "",
                        additional_html: "",
                    });
                    if (this.nameAddressSearch) {
                        this.nameAddressSearch.value = "";
                    }
                }}">Reset</button>`)
        }
        return renderedInputs;
    }

    private renderLatLonSearch() {
        const latLonModel = JSON.parse(this.latLonModel) as SearchTab;
        const searchInput = html`<input
            class="legacy-input search lat-lon-search"
            type="search"
            placeholder="Search by lat-lon coordinates, e.g., 40,-100"
            @keydown="${(e: KeyboardEvent) => {
                if (e.key === "Enter") {
                    e.preventDefault();
                    const latLonModel = JSON.parse(this.latLonModel) as SearchTab;
                    latLonModel.search = this.latLonSearch?.value || "";
                    this.latLonModel = JSON.stringify(latLonModel);
                }
            }}" />`;
        const renderedInputs = [searchInput];
        if (latLonModel.results.length) {
            const results = html`
                ${latLonModel.results.map((result, i) => html`
                    <li>
                        <label class="result">
                            <input
                            type="radio"
                            name="lat-lon-result"
                            .checked="${i === 0}"
                            value="${result}"
                            @input="${(e: Event) => {
                    const input = (e.target as HTMLInputElement);
                    const latLonModel = JSON.parse(this.latLonModel) as SearchTab;
                    latLonModel.selected = input.value || "";
                    this.latLonModel = JSON.stringify(latLonModel);
                }}" />
                            <span>${result}</span>
                        </label>
                    </li>
                `)}
            `;
            renderedInputs.push(html`<ul class="results lat-lon-results">
                ${results}
            </ul>`);
        }
        renderedInputs.push(html`<div class="additional-html-container">
            ${unsafeHTML(latLonModel.additional_html)}
        </div>`);
        if (latLonModel.search ||
            latLonModel.results.length ||
            latLonModel.selected) {
            renderedInputs.push(html`<button
                    class="legacy-button primary reset-button"
                    @click="${() => {
                    this.latLonModel = JSON.stringify({
                        search: "",
                        results: [],
                        selected: "",
                        additional_html: "",
                    });
                    if (this.latLonSearch) {
                        this.latLonSearch.value = "";
                    }
                }}">Reset</button>`)
        }
        return renderedInputs;
    }

    private renderDatasetSearch() {
        const datasetModel = JSON.parse(this.datasetModel) as SearchTab;
        const searchInput = html`<input
            class="legacy-input search dataset-search"
            type="search"
            placeholder="Search GEE data catalog by keywords, e.g., elevation"
            @keydown="${(e: KeyboardEvent) => {
                if (e.key === "Enter") {
                    e.preventDefault();
                    const datasetModel = JSON.parse(this.datasetModel) as SearchTab;
                    datasetModel.search = this.datasetSearch?.value || "";
                    // Force a rerender.
                    this.datasetModel = JSON.stringify(datasetModel);
                }
            }}" />`;
        const renderedInputs = [searchInput];
        const importButton = html`<button
            class="legacy-button primary import-button"
            title="Click to import the selected asset"
            @click="${() => {
                this.model?.send({ type: "click", id: "import" });
            }}">
            Import
        </button>`;
        const results = html`
            <select
                class="legacy-select dataset-select"
                @input="${(e: Event) => {
                const input = (e.target as HTMLInputElement);
                const datasetModel = JSON.parse(this.datasetModel) as SearchTab;
                datasetModel.selected = input.value || "";
                // Force a rerender.
                this.datasetModel = JSON.stringify(datasetModel);
            }}">
                ${datasetModel.results.map((result) => html`
                <option>
                    ${result}
                </option>
                `)}
            </select>
        `;
        renderedInputs.push(
            html`<div class="row">
                ${importButton}
                ${results}
            </div>`,
            html`<div class="additional-html-container">
                ${unsafeHTML(datasetModel.additional_html)}
            </div>`);
        return renderedInputs;
    }
}

// Without this check, there's a component registry issue when developing locally.
if (!customElements.get(SearchBar.componentName)) {
    customElements.define(SearchBar.componentName, SearchBar);
}

async function render({ model, el }: RenderProps<SearchBarModel>) {
    loadFonts();
    const row = <SearchBar>(
        document.createElement(SearchBar.componentName)
    );
    row.model = model;
    el.appendChild(row);
}

export default { render };
