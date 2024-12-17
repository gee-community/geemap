import { AnyModel } from "@anywidget/types";
import { default as legendRender, Legend, LegendModel } from "../js/legend";
import { FakeAnyModel } from "./fake_anywidget";

import "../js/legend";
import { Container } from "../js/container";

describe("<legend>", () => {
    let legend: Legend;

    async function makeLegend(model: AnyModel<LegendModel>) {
        const container = document.createElement("div");
        legendRender.render({
            model, el: container, experimental: {
                invoke: () => new Promise(() => [model, []]),
            }
        });
        const element = container.firstElementChild as Legend;
        document.body.appendChild(element);
        await element.updateComplete;
        return element;
    }

    beforeEach(async () => {
        legend = await makeLegend(new FakeAnyModel<LegendModel>({
            title: "My Legend",
            legend_keys: ["fire", "grass", "water"],
            legend_colors: ["#ff0000", "#00ff00", "#0000ff"],
            add_header: true,
            show_close_button: true,
        }));
    });

    afterEach(() => {
        Array.from(document.querySelectorAll("legend-widget")).forEach((el) => {
            el.remove();
        })
    });

    it("can be instantiated.", () => {
        expect(legend.shadowRoot?.querySelector("widget-container")).toBeDefined();
    });

    it("renders a header with title and close button", () => {
        const header = legend.shadowRoot?.querySelector("widget-container")!! as Container
        expect(header.title).toBe("My Legend");
        expect(header.hideCloseButton).toBeFalse();
    });


    it("does not render a header when add_header is false", async () => {
        legend.addHeader = false
        await legend.updateComplete;
        expect(legend.shadowRoot?.querySelector("widget-container")).toBeNull();
        expect(legend.shadowRoot?.textContent).toContain("My Legend");
    });

    it("renders the legend", async () => {
        const legendItems = legend.shadowRoot?.querySelectorAll('li')!;
        expect(Array.from(legendItems)
            .map((el) => el.textContent?.trim()))
            .toEqual(["fire", "grass", "water"]);
        expect(Array.from(legendItems)
            .map((el) => el.querySelector('span')?.style.background))
            .toEqual(["rgb(255, 0, 0)", "rgb(0, 255, 0)", "rgb(0, 0, 255)"]);
    });

    it("handles mismatched key/color size", async () => {
        legend.legendKeys = ["fire", "grass", "water", "electricity"]
        const legendItems = legend.shadowRoot?.querySelectorAll('li')!;
        expect(Array.from(legendItems)
            .map((el) => el.textContent?.trim()))
            .toEqual(["fire", "grass", "water"]);
    });
});