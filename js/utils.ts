import type { AnyModel } from "@anywidget/types";
import { IWidgetManager, WidgetModel } from "@jupyter-widgets/base";

async function unpackModels(
    modelIds: Array<string>,
    manager: IWidgetManager
): Promise<Array<WidgetModel>> {
    return Promise.all(
        modelIds.map((id) => manager.get_model(id.slice("IPY_MODEL_".length)))
    );
}

export function loadFonts() {
    if (!document.querySelector(".custom-fonts")) {
        const styleElement = document.createElement("style");
        styleElement.classList.add("custom-fonts");
        styleElement.textContent =
            '@import "https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined";';
        document.body.appendChild(styleElement);
    }
}

export async function updateChildren(
    container: HTMLElement,
    model: AnyModel<any>
) {
    const children = model.get("children");
    const child_models = await unpackModels(children, model.widget_manager);
    const child_views = await Promise.all(
        child_models.map((model) => model.widget_manager.create_view(model))
    );
    container.innerHTML = ``;
    for (const child_view of child_views) {
        container.appendChild(child_view.el);
    }
}
