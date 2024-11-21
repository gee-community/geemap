import type { RenderProps } from "@anywidget/types";
import { html, css } from "lit";
import { property } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";

import { legacyStyles } from "./ipywidgets_styles";
import { LitWidget } from "./lit_widget";
import { materialStyles } from "./styles";
import { loadFonts, updateChildren } from "./utils";

import { TabMode } from "./tab_panel";

export interface SearchTab {
    search: string,
    results: string[],
    selected: string,
    additional_html: string,
}


export interface SearchBarModel {
    expanded: boolean;
    tab_index: number;
    name_address_model: SearchTab,
    lat_lon_model: SearchTab,
    dataset_model: SearchTab,
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
        `,
    ];

    modelNameToViewName(): Map<keyof SearchBarModel, keyof SearchBar> {
        return new Map([
            ["expanded", "expanded"],
            ["tab_index", "tab_index"],
            ["name_address_model", "name_address_model"],
            ["lat_lon_model", "lat_lon_model"],
            ["dataset_model", "dataset_model"],
        ]);
    }

    @property()
    expanded: boolean = false;

    @property()
    tab_index: number = 0;

    @property()
    name_address_model: SearchTab = {
        search: "",
        results: [],
        selected: "",
        additional_html: "",
    };

    @property()
    lat_lon_model: SearchTab = {
        search: "",
        results: [],
        selected: "",
        additional_html: "",
    };

    @property()
    dataset_model: SearchTab = {
        search: "",
        results: [],
        selected: "",
        additional_html: "",
    };

    render() {
        return html`
            <div class="row">
                <button
                    class=${classMap({
                'expand-button': true,
                'legacy-button': true,
                'active': this.expanded,
            })}
                    title="Search location/data"
                    @click="${this.onExpandClick}">
                    <span class="material-symbols-outlined">search</span>
                </button>
                <tab-panel
                    .index="${this.tab_index}"
                    .tabs=${[{ name: "name/address" }, { name: "lat-lon" }, { name: "data" }]}
                    .mode="${TabMode.ALWAYS_SHOW}"
                    class="${classMap({
                hide: !this.expanded,
                expanded: this.expanded,
            })}"
                    @tab-clicked=${(e: CustomEvent<number>) => {
                    this.tab_index = e.detail;
                }}>
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
        const searchInput = html`<input
            class="legacy-input search name-address-search"
            type="text"
            placeholder="Search by place name or address"
            @change="${(e: Event) => {
                const input = (e.target as HTMLInputElement);
                this.name_address_model.search = input.value || "";
                // Force a rerender.
                this.name_address_model = Object.assign({}, this.name_address_model);
            }}" />`;
        const renderedInputs = [searchInput];
        if (this.name_address_model.results.length) {
            const results = html`
                ${this.name_address_model.results.map((result) => html`
                    <label>
                        <input
                        type="radio"
                        name="name-address-result"
                        value="${result}"
                        @change="${(e: Event) => {
                            const input = (e.target as HTMLInputElement);
                            this.name_address_model.selected = input.value || "";
                            // Force a rerender.
                            this.name_address_model = Object.assign({}, this.name_address_model);
                        }}" />
                        ${result}
                    </label>
                `)}
            `;
            renderedInputs.push(results);
        }
        renderedInputs.push(html`${this.name_address_model.additional_html}`);
        return renderedInputs;
    }

    private renderLatLonSearch() {
        const searchInput = html`<input
            class="legacy-input search lat-lon"
            type="text"
            placeholder="Search by lat-lon coordinates"
            @change="${(e: Event) => {
                const input = (e.target as HTMLInputElement);
                this.lat_lon_model.search = input.value || "";
                // Force a rerender.
                this.lat_lon_model = Object.assign({}, this.lat_lon_model);
            }}" />`;
        const renderedInputs = [searchInput];
        if (this.lat_lon_model.results.length) {
            const results = html`
                ${this.lat_lon_model.results.map((result) => html`
                    <label>
                        <input
                        type="radio"
                        name="lat-lon-result"
                        value="${result}"
                        @change="${(e: Event) => {
                            const input = (e.target as HTMLInputElement);
                            this.lat_lon_model.selected = input.value || "";
                            // Force a rerender.
                            this.lat_lon_model = Object.assign({}, this.lat_lon_model);
                        }}" />
                        ${result}
                    </label>
                `)}
            `;
            renderedInputs.push(results);
        }
        renderedInputs.push(html`${this.lat_lon_model.additional_html}`);
        return renderedInputs;
    }

    private renderDatasetSearch() {
        const searchInput = html`<input
            class="legacy-input search dataset-search"
            type="text"
            placeholder="Search Earth Engine data catalog"
            @change="${(e: Event) => {
                const input = (e.target as HTMLInputElement);
                this.dataset_model.search = input.value || "";
                // Force a rerender.
                this.dataset_model = Object.assign({}, this.dataset_model);
            }}" />`;
        const renderedInputs = [searchInput];
        if (this.dataset_model.results.length) {
            const importButton = html`<button
                class="legacy-button primary"
                title="Click to import the selected asset"
                @click="${() => {
                    this.model?.send({ type: "click", id: "import" });
                }}">
            </button>`;
            const results = html`
                ${this.dataset_model.results.map((result) => html`
                    <select
                        @change="${(e: Event) => {
                            const input = (e.target as HTMLInputElement);
                            this.dataset_model.selected = input.value || "";
                            // Force a rerender.
                            this.dataset_model = Object.assign({}, this.dataset_model);
                        }}">
                        <option>
                        ${result}
                    </select>
                `)}
            `;
            renderedInputs.push(importButton, results);
        }
        renderedInputs.push(html`${this.dataset_model.additional_html}`);
        return renderedInputs;
    }
}

// Without this check, there's a component registry issue when developing locally.
if (!customElements.get(SearchBar.componentName)) {
    customElements.define(SearchBar.componentName, SearchBar);
}

async function render({ model, el }: RenderProps<SearchBarModel>) {
    loadFonts();
    const manager = <SearchBar>document.createElement(SearchBar.componentName);
    manager.model = model;
    el.appendChild(manager);

    const accessoryWidgetEl = document.createElement("div");
    accessoryWidgetEl.slot = "accessory-widget";
    manager.appendChild(accessoryWidgetEl);

    updateChildren(accessoryWidgetEl, model, "accessory_widgets");
    model.on("change:accessory_widgets", () => {
        updateChildren(accessoryWidgetEl, model, "accessory_widgets");
    });

    const mainToolsEl = document.createElement("div");
    mainToolsEl.slot = "main-tools";
    manager.appendChild(mainToolsEl);

    updateChildren(mainToolsEl, model, "main_tools");
    model.on("change:main_tools", () => {
        updateChildren(mainToolsEl, model, "main_tools");
    });

    const extraToolsEl = document.createElement("div");
    extraToolsEl.slot = "extra-tools";
    manager.appendChild(extraToolsEl);

    updateChildren(extraToolsEl, model, "extra_tools");
    model.on("change:extra_tools", () => {
        updateChildren(extraToolsEl, model, "extra_tools");
    });
}

export default { render };
