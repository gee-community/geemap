import { AnyModel } from "@anywidget/types";
import "../js/layer_manager_row";
import { default as rowRender, LayerManagerRow, LayerManagerRowModel } from "../js/layer_manager_row";
import { FakeAnyModel } from "./fake_anywidget";

describe("<layer-manager-row>", () => {
    let row: LayerManagerRow;

    async function makeRow(model: AnyModel<LayerManagerRowModel>) {
        const container = document.createElement("div");
        rowRender.render({
            model, el: container, experimental: {
                invoke: () => new Promise(() => [model, []]),
            }
        });
        const element = container.firstElementChild as LayerManagerRow;
        document.body.appendChild(element);
        await element.updateComplete;
        return element;
    }

    beforeEach(async () => {
        row = await makeRow(new FakeAnyModel<LayerManagerRowModel>({
            name: "Test Layer",
            visible: true,
            opacity: 1,
            is_loading: false,
        }));
    });

    afterEach(() => {
        Array.from(document.querySelectorAll("layer-manager-row")).forEach((el) => {
            el.remove();
        })
    });

    it("can be instantiated.", () => {
        expect(row.shadowRoot?.querySelector(".layer-name")?.textContent).toContain("Test Layer");
    });

    it("sets model properties on property change.", async () => {
        const setSpy = spyOn(FakeAnyModel.prototype, "set");
        const saveSpy = spyOn(FakeAnyModel.prototype, "save_changes");
        row.opacity = 0.5;
        await row.updateComplete;
        expect(setSpy).toHaveBeenCalledOnceWith("opacity", 0.5);
        expect(saveSpy).toHaveBeenCalledTimes(1);
    });

    it("emits model events when clicked.", async () => {
        // Settings button emits an event.
        const sendSpy = spyOn(FakeAnyModel.prototype, "send");
        (row.shadowRoot?.querySelector(".settings-button") as HTMLButtonElement).click();
        expect(FakeAnyModel.prototype.send).toHaveBeenCalledOnceWith({
            type: "click",
            id: "settings"
        });

        sendSpy.calls.reset();

        // Deletion button emits an event.
        (row.shadowRoot?.querySelector(".delete-button") as HTMLButtonElement).click();
        await row.updateComplete;
        (row.shadowRoot?.querySelector(".confirm-deletion-button") as HTMLButtonElement).click();
        expect(sendSpy).toHaveBeenCalledOnceWith({
            type: "click",
            id: "delete"
        });
    });
});