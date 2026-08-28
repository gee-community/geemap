import "../js/raster_layer_editor";
import { RasterLayerEditor } from "../js/raster_layer_editor";

describe("<raster-layer-editor>", () => {
    let editor: RasterLayerEditor;

    async function makeEditor(visParams: Record<string, any>) {
        const element = document.createElement(
            RasterLayerEditor.componentName
        ) as RasterLayerEditor;
        element.bandNames = [
            "B1",
            "B2",
            "B3",
            "B4",
            "B5",
            "B7",
        ];
        element.colormaps = ["Custom", "viridis"];
        element.visParams = visParams;
        document.body.appendChild(element);
        await element.updateComplete;
        return element;
    }

    afterEach(() => {
        Array.from(document.querySelectorAll("raster-layer-editor")).forEach(
            (el) => {
                el.remove();
            }
        );
    });

    it("initializes bands, min, and max from vis_params", async () => {
        editor = await makeEditor({
            bands: ["B4", "B3", "B2"],
            min: 20,
            max: 200,
            gamma: 1.5,
        });

        expect(editor.selectedBands).toEqual(["B4", "B3", "B2"]);
        expect(editor.minValue).toBe(20);
        expect(editor.maxValue).toBe(200);
        expect(editor.gamma).toBe(1.5);

        const minInput = editor.shadowRoot?.querySelector("#min") as HTMLInputElement;
        const maxInput = editor.shadowRoot?.querySelector("#max") as HTMLInputElement;
        expect(minInput.value).toBe("20");
        expect(maxInput.value).toBe("200");
    });

    it("uses the palette from vis_params for single-band layers", async () => {
        editor = await makeEditor({
            min: 0,
            max: 4000,
            palette: ["006633", "E5FFCC", "662A00", "D8D8D8", "F5F5F5"],
        });

        expect(editor.minValue).toBe(0);
        expect(editor.maxValue).toBe(4000);
        expect(editor.colorRamp).toBe("palette");
        expect(editor.initialPalette).toBe(
            "006633, E5FFCC, 662A00, D8D8D8, F5F5F5"
        );
    });
});
