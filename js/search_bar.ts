import type { RenderProps } from "@anywidget/types";
import { html, css } from "lit";
import { property, query, queryAll } from "lit/decorators.js";

import { legacyStyles } from "./ipywidgets_styles";
import { LitWidget } from "./lit_widget";
import { materialStyles } from "./styles";
import { loadFonts } from "./utils";

import { TabMode } from "./tab_panel";
import { unsafeHTML } from "lit/directives/unsafe-html.js";

import './container';

export interface SearchTab {
    search: string,
    results: string[],
    selected: string,
    additional_html: string,
}

export interface SearchBarModel {
    collapsed: boolean;
    tab_index: number;
    location_model: string,
    dataset_model: string,
}

export class SearchBar extends LitWidget<
    SearchBarModel,
    SearchBar
> {
    static get componentName() {
        return `search-bar`;
    }

    static override styles = [
        legacyStyles,
        materialStyles,
        css`
            .row {
                display: flex;
                gap: 6px;
            }

            .input-container {
                max-width: 320px;
            }

            .input-container > p {
                margin: 8px 3px;
            }

            input.search {
                margin: 2px 2px 8px 2px;
                width: calc(100% - 4px);
            }

            ul.results {
                list-style-type: none;
                margin: 0;
                margin-bottom: 4px;
                padding: 8px 0;
            }

            label.result {
                align-items: center;
                display: flex;
                margin-bottom: 4px;
            }

            .import-button, .reset-button {
                margin: 0 2px 2px 2px;
                padding: 0 8px;
                white-space: nowrap;
            }

            .dataset-select {
                margin-bottom: 2px;
                margin-right: 2px;
            }

            .additional-html-container {
                max-height: 300px;
                overflow: auto;
                padding: 8px 0;
            }

            .additional-html-container pre {
                white-space: break-spaces;
            }
        `,
    ];

    modelNameToViewName(): Map<keyof SearchBarModel, keyof SearchBar> {
        return new Map([
            ["collapsed", "collapsed"],
            ["tab_index", "tab_index"],
            ["location_model", "locationModel"],
            ["dataset_model", "datasetModel"],
        ]);
    }

    @property()
    collapsed: boolean = true;

    @property()
    tab_index: number = 0;

    @property()
    locationModel: string = JSON.stringify({
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

    @query(".location-search")
    locationSearch!: HTMLInputElement;

    @queryAll(".location-results input")
    locationResults!: HTMLInputElement[];

    @query(".dataset-search")
    datasetSearch!: HTMLInputElement;

    override render() {
        return html`
            <widget-container
                icon="search"
                title="Search"
                .collapsed="${this.collapsed}"
                .hideCloseButton="${true}"
                .compactMode="${true}">
                <tab-panel
                    .index="${this.tab_index}"
                    .tabs=${[{ name: "location", width: 110 },
            { name: "data", width: 110 }
            ]}
                    @tab-changed=${(e: CustomEvent<number>) => {
                this.tab_index = e.detail;
            }}
                    .mode="${TabMode.ALWAYS_SHOW}">
                    <div class="input-container location-container">
                        ${this.renderLocationSearch()}
                    </div>
                    <div class="input-container dataset-container">
                        ${this.renderDatasetSearch()}
                    </div>
                </tab-panel>
            </widget-container>`;
    }

    private renderLocationSearch() {
        const locationModel = JSON.parse(this.locationModel) as SearchTab;
        const helpText = html`<p>
            Find your point of interest (by place name,
            address, or coordinates, e.g. 40,-100)
        </p>`;
        const searchInput = html`<input
            class="legacy-input search location-search"
            type="search"
            placeholder="Search by location / lat-lon"
            @keydown="${(e: KeyboardEvent) => {
                if (e.key === "Enter") {
                    e.preventDefault();
                    const locationModel = JSON.parse(this.locationModel) as SearchTab;
                    locationModel.search = this.locationSearch.value || "";
                    this.locationModel = JSON.stringify(locationModel);
                }
            }}" />`;
        const renderedInputs = [helpText, searchInput];
        if (locationModel.results.length) {
            const results = html`
                ${locationModel.results.map((result) => html`
                    <li>
                        <label class="result">
                            <input
                            type="radio"
                            name="location-result"
                            value="${result}"
                            .checked="${locationModel.selected === result}"
                            @input="${(e: Event) => {
                    const input = (e.target as HTMLInputElement);
                    const locationModel = JSON.parse(this.locationModel) as SearchTab;
                    locationModel.selected = input.value || "";
                    this.locationModel = JSON.stringify(locationModel);
                }}" />
                            <span>${result}</span>
                        </label>
                    </li>`)}
            `;
            renderedInputs.push(html`<ul class="results location-results">
                ${results}
            </ul>`);
        }
        if (locationModel.additional_html) {
            renderedInputs.push(html`<div class="additional-html-container">
                ${unsafeHTML(locationModel.additional_html)}
            </div>`);
        }
        if (locationModel.search ||
            locationModel.results.length ||
            locationModel.selected) {
            renderedInputs.push(html`<button
                    class="legacy-button primary reset-button"
                    @click="${() => {
                    this.locationModel = JSON.stringify({
                        search: "",
                        results: [],
                        selected: "",
                        additional_html: "",
                    });
                    if (this.locationSearch) {
                        this.locationSearch.value = "";
                    }
                }}">Reset</button>`)
        }
        return renderedInputs;
    }

    private renderDatasetSearch() {
        const datasetModel = JSON.parse(this.datasetModel) as SearchTab;
        const helpText = html`<p>
            Find a dataset by GEE data catalog name or keywords, e.g. elevation
        </p>`;
        const searchInput = html`<input
            class="legacy-input search dataset-search"
            type="search"
            placeholder="Search dataset / keywords"
            @keydown="${(e: KeyboardEvent) => {
                if (e.key === "Enter") {
                    e.preventDefault();
                    const datasetModel = JSON.parse(this.datasetModel) as SearchTab;
                    datasetModel.search = this.datasetSearch?.value || "";
                    // Force a rerender.
                    this.datasetModel = JSON.stringify(datasetModel);
                }
            }}" />`;
        const renderedInputs = [helpText, searchInput];
        const importButton = html`<button
            class="legacy-button primary import-button"
            title="Click to import the selected asset"
            @click="${() => {
                this.model?.send({ type: "click", id: "import" });
            }}">
            Reveal Code
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
            </div>`);
        if (datasetModel.additional_html) {
            renderedInputs.push(html`<div class="additional-html-container">
                ${unsafeHTML(datasetModel.additional_html)}
            </div>`)
        }
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
