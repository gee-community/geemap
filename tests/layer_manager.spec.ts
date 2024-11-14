import { AnyModel } from "@anywidget/types";
import "../js/layer_manager";

import { default as layerManagerRender, LayerManager, LayerManagerModel } from "../js/layer_manager";
import { FakeAnyModel } from "./fake_anywidget";

describe("<layer-manager>", () => {
    let layerManager: LayerManager;

    async function makeManager(model: AnyModel<LayerManagerModel>) {
        const container = document.createElement("div");
        layerManagerRender.render({
            model, el: container, experimental: {
                invoke: () => new Promise(() => [model, []]),
            }
        });
        const element = container.firstElementChild as LayerManager;
        document.body.appendChild(element);
        await element.updateComplete;
        return element;
    }

    beforeEach(async () => {
        layerManager = await makeManager(new FakeAnyModel<LayerManagerModel>({
            visible: true,
            children: [],
        }));
    });

    afterEach(() => {
        Array.from(document.querySelectorAll("layer-manager")).forEach((el) => {
            el.remove();
        })
    });

    it("can be instantiated.", async () => {
        expect(layerManager.shadowRoot?.querySelector(".all-layers-text")).toBeDefined();
    });

    it("sets model properties on property change.", async () => {
        const setSpy = spyOn(FakeAnyModel.prototype, "set");
        const saveSpy = spyOn(FakeAnyModel.prototype, "save_changes");
        layerManager.visible = false;
        await layerManager.updateComplete;
        expect(setSpy).toHaveBeenCalledOnceWith("visible", false);
        expect(saveSpy).toHaveBeenCalledTimes(1);
    });
});