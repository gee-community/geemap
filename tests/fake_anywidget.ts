import type { AnyModel } from "@anywidget/types";
import type { IWidgetManager } from "@jupyter-widgets/base";

type ObjectHash = Record<string, any>;

export class FakeAnyModel<T extends ObjectHash> implements AnyModel {
    public widget_manager: IWidgetManager = new Object() as IWidgetManager;

    constructor(private model: T) { }

    get<K extends keyof T>(key: K) {
        return this.model[key];
    }
    set<K extends keyof T>(key: K, value: T[K]) {
        this.model[key] = value;
    }
    off() { }
    on() { }
    save_changes() { }
    send(_: Object) { };
}