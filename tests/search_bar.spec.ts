import { AnyModel } from "@anywidget/types";
import { default as searchBarRender, SearchBar, SearchBarModel } from "../js/search_bar";
import { FakeAnyModel } from "./fake_anywidget";

import "../js/search_bar";

describe("<search-bar>", () => {
    let searchBar: SearchBar;

    async function makeSearchBar(model: AnyModel<SearchBarModel>) {
        const container = document.createElement("div");
        searchBarRender.render({
            model, el: container, experimental: {
                invoke: () => new Promise(() => [model, []]),
            }
        });
        const element = container.firstElementChild as SearchBar;
        document.body.appendChild(element);
        await element.updateComplete;
        return element;
    }

    beforeEach(async () => {
        searchBar = await makeSearchBar(new FakeAnyModel<SearchBarModel>({
            collapsed: true,
            tab_index: 0,
            location_model: JSON.stringify({
                search: "",
                results: [],
                selected: "",
                additional_html: "",
            }),
            dataset_model: JSON.stringify({
                search: "",
                results: [],
                selected: "",
                additional_html: "",
            }),
        }));
    });

    afterEach(() => {
        Array.from(document.querySelectorAll("search-bar")).forEach((el) => {
            el.remove();
        })
    });

    it("can be instantiated.", () => {
        expect(searchBar.shadowRoot?.querySelector("tab-panel")).toBeDefined();
    });

    it("renders and updates the name address search", async () => {
        searchBar.locationModel = JSON.stringify({
            search: "my city",
            results: ["my city 1", "my city 2"],
            selected: "my city 1",
            additional_html: `<p class="name-address-extra">An extra message </p>`,
        })
        await searchBar.updateComplete;
        expect(searchBar.locationSearch).toBeDefined();
        expect(searchBar.locationResults).toBeDefined();
        expect(searchBar.locationResults[0].checked).toBeTrue();
        const results = Array.from(searchBar.locationResults).map((el) => el.value);
        expect(results).toEqual(["my city 1", "my city 2"]);
        expect(searchBar.shadowRoot!.querySelector(".name-address-extra")).toBeDefined();
        expect(searchBar.shadowRoot!.querySelector(".name-address-container .reset-button")).toBeDefined();

        jasmine.clock().install();
        searchBar.locationSearch.value = "my new search";
        searchBar.locationSearch.dispatchEvent(new KeyboardEvent('keydown', { 'key': 'Enter' }));
        jasmine.clock().tick(500);
        await searchBar.updateComplete;
        expect(JSON.parse(searchBar.locationModel).search).toBe("my new search");
        jasmine.clock().uninstall();

        searchBar.locationResults[1].checked = true;
        searchBar.locationResults[1].dispatchEvent(new Event("input"));
        expect(JSON.parse(searchBar.locationModel).selected).toBe("my city 2");
    });

    it("renders and updates the lat-lon search", async () => {
        searchBar.locationModel = JSON.stringify({
            search: "40, -100",
            results: ["my cool city"],
            selected: "my cool city",
            additional_html: `<p class="lat-lon-extra">An extra message </p>`,
        })
        await searchBar.updateComplete;
        expect(searchBar.locationSearch).toBeDefined();
        expect(searchBar.locationResults).toBeDefined();
        expect(searchBar.locationResults[0].checked).toBeTrue();
        const results = Array.from(searchBar.locationResults).map((el) => el.value);
        expect(results).toEqual(["my cool city"]);
        expect(searchBar.shadowRoot!.querySelector(".lat-lon-extra")).toBeDefined();
        expect(searchBar.shadowRoot!.querySelector(".lat-lon-container .reset-button")).toBeDefined();

        jasmine.clock().install();
        searchBar.locationSearch.value = "my new search";
        searchBar.locationSearch.dispatchEvent(new KeyboardEvent('keydown', { 'key': 'Enter' }));
        jasmine.clock().tick(500);
        await searchBar.updateComplete;
        expect(JSON.parse(searchBar.locationModel).search).toBe("my new search");
        jasmine.clock().uninstall();
    });

    it("renders and updates the dataset search", async () => {
        searchBar.datasetModel = JSON.stringify({
            search: "elevation",
            results: ["dataset 1", "dataset 2"],
            selected: "dataset 1",
            additional_html: `<p class="dataset-extra">A cool dataset</p>`,
        })
        await searchBar.updateComplete;
        expect(searchBar.datasetSearch).toBeDefined();
        expect(searchBar.shadowRoot!.querySelector(".dataset-extra")).toBeDefined();

        jasmine.clock().install();
        searchBar.datasetSearch.value = "my new search";
        searchBar.datasetSearch.dispatchEvent(new KeyboardEvent('keydown', { 'key': 'Enter' }));
        jasmine.clock().tick(500);
        await searchBar.updateComplete;
        expect(JSON.parse(searchBar.datasetModel).search).toBe("my new search");
        jasmine.clock().uninstall();
    });
});