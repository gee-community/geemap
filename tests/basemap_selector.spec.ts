import { AnyModel } from "@anywidget/types";
import "../js/basemap_selector";
import {
    default as selectorRender,
    BasemapSelector,
    BasemapSelectorModel,
} from "../js/basemap_selector";
import { FakeAnyModel } from "./fake_anywidget";

describe("<basemap-selector>", () => {
    let selector: BasemapSelector;

    async function makeSelector(model: AnyModel<BasemapSelectorModel>) {
        const container = document.createElement("div");
        selectorRender.render({
            model,
            el: container,
            experimental: {
                invoke: () => new Promise(() => [model, []]),
            },
        });
        const element = container.firstElementChild as BasemapSelector;
        document.body.appendChild(element);
        await element.updateComplete;
        return element;
    }

    beforeEach(async () => {
        selector = await makeSelector(
            new FakeAnyModel<BasemapSelectorModel>({
                basemaps: {
                    DEFAULT: [],
                    "a-provider": ["resource-1", "resource-2"],
                    "another-provider": [],
                },
                provider: "DEFAULT",
                resource: "",
            })
        );
    });

    afterEach(() => {
        Array.from(document.querySelectorAll("basemap-selector")).forEach(
            (el) => {
                el.remove();
            }
        );
    });

    it("can be instantiated.", () => {
        expect(
            selector.shadowRoot?.querySelector("select")?.textContent
        ).toContain("DEFAULT");
    });

    it("selects the default provider appropriately.", () => {
        const selects = selector.shadowRoot?.querySelectorAll("select")!;
        const providerSelect = selects[0];
        const resourceSelect = selects[1];

        expect(selects.length).toBe(2); // Resource select should display "---".
        expect(providerSelect.value).toBe("DEFAULT");
        expect(selector.provider).toBe("DEFAULT");
        expect(resourceSelect.value).toBe("---");
        expect(selector.resource).toBe("");
    });

    it("setting the provider and resource on model updates the view.", async () => {
        selector.provider = "a-provider";
        await selector.updateComplete;

        const selects = selector.shadowRoot?.querySelectorAll("select")!;
        expect(selects.length).toBe(2);
        const providerSelect = selects[0];
        const resourceSelect = selects[1];

        expect(providerSelect.value).toBe("a-provider");
        expect(resourceSelect.value).toBe("resource-1");
        expect(selector.resource).toBe("resource-1");

        selector.resource = "resource-2";
        await selector.updateComplete;

        expect(providerSelect.value).toBe("a-provider");
        expect(selector.provider).toBe("a-provider");
        expect(resourceSelect.value).toBe("resource-2");
    });

    it("sets value on model when option changes.", async () => {
        const setSpy = spyOn(FakeAnyModel.prototype, "set");
        const saveSpy = spyOn(FakeAnyModel.prototype, "save_changes");

        let selects = selector.shadowRoot?.querySelectorAll("select")!;
        const providerSelect = selects[0];

        providerSelect.value = "a-provider";
        providerSelect.dispatchEvent(new Event("change"));
        await selector.updateComplete;

        expect(setSpy).toHaveBeenCalledWith("provider", "a-provider");
        expect(setSpy).toHaveBeenCalledWith("resource", "resource-1");
        expect(setSpy).toHaveBeenCalledTimes(2);
        expect(saveSpy).toHaveBeenCalledTimes(1);

        selects = selector.shadowRoot?.querySelectorAll("select")!;
        const resourceSelect = selects[1];

        resourceSelect.value = "resource-2";
        resourceSelect.dispatchEvent(new Event("change"));
        await selector.updateComplete;

        expect(setSpy).toHaveBeenCalledWith("resource", "resource-2");
        expect(setSpy).toHaveBeenCalledTimes(3);
        expect(saveSpy).toHaveBeenCalledTimes(2);
    });
});
