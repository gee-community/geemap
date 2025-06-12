import type { RenderProps } from '@anywidget/types';
import { css, html, nothing, TemplateResult } from 'lit';
import { property } from 'lit/decorators.js';

import { legacyStyles } from './ipywidgets_styles';
import { LitWidget } from "./lit_widget";
import type { Node } from './tree_node';

import './container';
import './tree_node';

export interface InspectorModel {
    hide_close_button: boolean;
    expand_points: boolean;
    expand_pixels: boolean;
    expand_objects: boolean;
    point_info: { [key: string]: any };
    pixel_info: { [key: string]: any };
    object_info: { [key: string]: any };
}

export class Inspector extends LitWidget<InspectorModel, Inspector> {
    static get componentName(): string {
        return `inspector-widget`;
    }

    static override styles = [
        legacyStyles,
        css`
            .checkbox-container {
                align-items: center;
                display: flex;
                gap: 8px;
                height: 32px;
            }

            .spacer {
                width: 8px;
            }

            .object-browser {
                max-height: 300px;
                overflow: auto;
                width: 290px;
            }

            input[type='checkbox'] {
                vertical-align: middle;
            }
        `,
    ];

    @property({ type: Boolean }) hideCloseButton: boolean = false;
    @property({ type: Boolean }) expandPoints: boolean = false;
    @property({ type: Boolean }) expandPixels: boolean = true;
    @property({ type: Boolean }) expandObjects: boolean = false;
    @property() pointInfo: Node = {};
    @property() pixelInfo: Node = {};
    @property() objectInfo: Node = {};

    modelNameToViewName(): Map<keyof InspectorModel, keyof Inspector | null> {
        return new Map([
            ['hide_close_button', 'hideCloseButton'],
            ['expand_points', 'expandPoints'],
            ['expand_pixels', 'expandPixels'],
            ['expand_objects', 'expandObjects'],
            ['point_info', 'pointInfo'],
            ['pixel_info', 'pixelInfo'],
            ['object_info', 'objectInfo'],
        ]);
    }

    override render() {
        return html`
            <widget-container
                icon="point_scan"
                title="Inspector"
                .hideCloseButton="${this.hideCloseButton}"
                @close-clicked="${this.onCloseButtonClicked}"
            >
                <div class="checkbox-container">
                    <span class="legacy-text">Expand</span>
                    <div>
                        <input
                            type="checkbox"
                            .checked="${this.expandPoints}"
                            @change="${this.onPointCheckboxEvent}"
                        />
                        <span class="legacy-text">Point</span>
                    </div>
                    <div>
                        <input
                            type="checkbox"
                            .checked="${this.expandPixels}"
                            @change="${this.onPixelCheckboxEvent}"
                        />
                        <span class="legacy-text">Pixels</span>
                    </div>
                    <div>
                        <input
                            type="checkbox"
                            .checked="${this.expandObjects}"
                            @change="${this.onFeatureCheckboxEvent}"
                        />
                        <span class="legacy-text">Objects</span>
                    </div>
                </div>
                <div class="object-browser">
                    ${this.renderNode(this.pointInfo)}
                    ${this.renderNode(this.pixelInfo)}
                    ${this.renderNode(this.objectInfo)}
                </div>
            </widget-container>
        `;
    }

    private renderNode(node: Node): TemplateResult | typeof nothing {
        if (node.children?.length) {
            return html`<tree-node .node="${node}"></tree-node> `;
        }
        return nothing;
    }

    private onPointCheckboxEvent(event: Event) {
        const target = event.target as HTMLInputElement;
        this.expandPoints = target.checked;
    }

    private onPixelCheckboxEvent(event: Event) {
        const target = event.target as HTMLInputElement;
        this.expandPixels = target.checked;
    }

    private onFeatureCheckboxEvent(event: Event) {
        const target = event.target as HTMLInputElement;
        this.expandObjects = target.checked;
    }

    private onCloseButtonClicked(_: Event) {
        this.model?.send({ "type": "click", "id": "close" });
    }
}

// Without this check, there's a component registry issue when developing locally.
if (!customElements.get(Inspector.componentName)) {
    customElements.define(Inspector.componentName, Inspector);
}

async function render({ model, el }: RenderProps<InspectorModel>) {
    const widget = document.createElement(Inspector.componentName) as Inspector;
    widget.model = model;
    el.appendChild(widget);
}

export default { render };