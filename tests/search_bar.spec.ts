import { AnyModel } from "@anywidget/types";
import "../js/basemap_selector";
import { default as selectorRender, SearchBar, SearchBarModel } from "../js/search_bar";
import { FakeAnyModel } from "./fake_anywidget";

describe("<search-bar>", () => {
    let selector: SearchBar;

    async function makeSelector(model: AnyModel<SearchBarModel>) {
        const container = document.createElement("div");
        selectorRender.render({
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
        selector = await makeSelector(new FakeAnyModel<SearchBarModel>({
            expanded: false,
            tab_index: 0,
            name_address_model: JSON.stringify({
                search: 'my city',
                results: ['my city 1', 'my city 2'],
                selected: '',
                additional_html: '',
            }),
            lat_lon_model: JSON.stringify({
                search: '40, -100',
                results: ['my cool city'],
                selected: '',
                additional_html: '',
            }),
            dataset_model: JSON.stringify({
                search: 'elevation',
                results: ['dataset 1', 'dataset 2'],
                selected: '',
                additional_html: '',
            }),
        }));
    });

    afterEach(() => {
        Array.from(document.querySelectorAll("search-bar")).forEach((el) => {
            el.remove();
        })
    });

    it("can be instantiated.", () => {
        expect(selector.shadowRoot?.querySelector("tab-panel")).toBeDefined();
    });
});