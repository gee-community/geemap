import { LitElement, PropertyValues } from "lit";

import { reverseMap } from "./utils";

export abstract class LitWidget<
    ModelType,
    SubclassType extends LitWidget<any, any>
> extends LitElement {
    private _model: any | undefined = undefined; // AnyModel<ModelType>

    abstract modelNameToViewName(): Map<
        keyof ModelType,
        keyof SubclassType | null
    >;

    onCustomMessage?(_msg: any): void {}

    viewNameToModelName(): Map<keyof SubclassType | null, keyof ModelType> {
        return reverseMap(this.modelNameToViewName());
    }

    set model(model: any) {
        // TODO(naschmitz): model should be of type AnyModel<ModelType>. AnyModel
        // requires a type that conforms to a non-exported member of anywidget.
        this._model = model;
        for (const [modelKey, widgetKey] of this.modelNameToViewName()) {
            if (widgetKey) {
                // Get initial values from the Python model.
                (this as any)[widgetKey] = model.get(modelKey);
                // Listen for updates to the model.
                model.on(`change:${String(modelKey)}`, () => {
                    (this as any)[widgetKey] = model.get(modelKey);
                });
            }
        }
        model.on("msg:custom", (msg: any) => {
            this.onCustomMessage?.(msg);
        });
    }

    get model(): any {
        // TODO(naschmitz): model should be of type AnyModel<ModelType>. AnyModel
        // requires a type that conforms to a non-exported member of anywidget.
        return this._model;
    }

    override updated(changedProperties: PropertyValues<SubclassType>): void {
        // Update the model properties so they're reflected in Python.
        const viewToModelMap = this.viewNameToModelName();
        for (const [viewProp, _] of changedProperties) {
            const castViewProp = viewProp as keyof SubclassType;
            if (viewToModelMap.has(castViewProp)) {
                const modelProp = viewToModelMap.get(castViewProp);
                this._model?.set(
                    modelProp as any,
                    this[castViewProp as keyof this] as any
                );
            }
        }
        this._model?.save_changes();
    }
}
