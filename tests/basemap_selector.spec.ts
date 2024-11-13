import { AnyModel } from "@anywidget/types";
import "../js/basemap_selector";
import { default as selectorRender, BasemapSelector, BasemapSelectorModel } from "../js/basemap_selector";
import { FakeAnyModel } from "./fake_anywidget";

describe("<basemap-selector>", () => {
    let selector: BasemapSelector;

    async function makeSelector(model: AnyModel<BasemapSelectorModel>) {
        const container = document.createElement("div");
        selectorRender.render({
            model, el: container, experimental: {
                invoke: () => new Promise(() => [model, []]),
            }
        });
        const element = container.firstElementChild as BasemapSelector;
        document.body.appendChild(element);
        await element.updateComplete;
        return element;
    }

    beforeEach(async () => {
        selector = await makeSelector(new FakeAnyModel<BasemapSelectorModel>({
            basemaps: ["select", "default", "bounded"],
            value: "default",
        }));
    });

    afterEach(() => {
        Array.from(document.querySelectorAll("basemap-selector")).forEach((el) => {
            el.remove();
        })
    });

    it("can be instantiated.", () => {
        expect(selector.shadowRoot?.querySelector("select")?.textContent).toContain("bounded");
    });

    it("renders the basemap options.", () => {
        const options = selector.shadowRoot?.querySelectorAll("option")!;
        expect(options.length).toBe(3);
        expect(options[0].textContent).toContain("select");
        expect(options[1].textContent).toContain("default");
        expect(options[2].textContent).toContain("bounded");
    });

    it("setting the value on model changes the value on select.", async () => {
        selector.value = "select";
        await selector.updateComplete;
        expect(selector.selectElement.value).toBe("select");
    });

    it("sets value on model when option changes.", async () => {
        const setSpy = spyOn(FakeAnyModel.prototype, "set");
        const saveSpy = spyOn(FakeAnyModel.prototype, "save_changes");

        selector.selectElement.value = "select";
        selector.selectElement.dispatchEvent(new Event('change'));

        await selector.updateComplete;
        expect(setSpy).toHaveBeenCalledOnceWith("value", "select");
        expect(saveSpy).toHaveBeenCalledTimes(1);
    });

    it("emits close event when clicked.", async () => {
        const sendSpy = spyOn(FakeAnyModel.prototype, "send");
        // Close button emits an event.
        (selector.shadowRoot?.querySelector(".close-button") as HTMLButtonElement).click();
        await selector.updateComplete;
        expect(sendSpy).toHaveBeenCalledOnceWith({
            type: "click",
            id: "close"
        });
    });
});