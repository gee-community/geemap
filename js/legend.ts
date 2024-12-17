import type { RenderProps } from "@anywidget/types";

import { css, html } from "lit";
import { property } from "lit/decorators.js";
import { styleMap } from "lit/directives/style-map.js";

import { legacyStyles } from "./ipywidgets_styles";
import { LitWidget } from "./lit_widget";
import { materialStyles } from "./styles";

import './container';

function zip<T>(a: T[], b: T[]) {
    const maxLength = Math.min(a.length, b.length);
    return a.slice(0, maxLength).map((el, i) => [el, b[i]]);
}

export interface LegendData {
    [key: string]: [color: string];
}

export interface LegendModel {
    title: string;
    legend_keys: string[];
    legend_colors: string[];
    add_header: boolean;
    show_close_button: boolean;
}

export class Legend extends LitWidget<LegendModel, Legend> {
    static get componentName(): string {
        return `legend-widget`;
    }

    static styles = [
        legacyStyles,
        materialStyles,
        css`
            .legend {
                padding: 4px;
                max-height: 200px;
                max-width: 300px;
                overflow: auto;
            }

            widget-container .legend {
                padding: 0px !important;
            }

            .legend .legend-title {
                text-align: left;
                margin-bottom: 2px;
                margin-left: 2px;
                font-weight: bold;
                font-size: 90%;
            }

            .legend .legend-scale ul {
                margin: 0;
                margin-bottom: 5px;
                padding: 0;
                float: left;
                list-style: none;
            }

            .legend .legend-scale ul li {
                font-size: 80%;
                list-style: none;
                margin-left: 1px;
                line-height: 18px;
                margin-bottom: 2px;
            }

            .legend ul.legend-labels li span {
                display: block;
                float: left;
                height: 16px;
                width: 30px;
                margin-right: 5px;
                margin-left: 2px;
                border: 1px solid #999;
            }

            .legend .legend-source {
                font-size: 70%;
                color: #999;
                clear: both;
            }

            .legend a {
                color: #777;

            }`,
    ];

    @property({ type: String }) title = "";
    @property({ type: Array }) legendKeys: string[] = [];
    @property({ type: Array }) legendColors: string[] = [];
    @property({ type: Boolean }) addHeader: boolean = true;
    @property({ type: Boolean }) showCloseButton: boolean = true;

    modelNameToViewName(): Map<keyof LegendModel, keyof Legend | null> {
        return new Map([
            ["title", "title"],
            ["legend_keys", "legendKeys"],
            ["legend_colors", "legendColors"],
            ["add_header", "addHeader"],
            ["show_close_button", "showCloseButton"],
        ]);
    }

    render() {
        return this.addHeader ? html`
            <widget-container
                .hideCloseButton="${!this.showCloseButton}"
                .title="${this.title}"
                @close-clicked="${this.onCloseButtonClicked}">
                ${this.renderLegend('')}
            </widget-container>` : this.renderLegend(this.title);
    }

    private onCloseButtonClicked(_: Event) {
        this.model?.send({ "type": "click", "id": "close" });
    }

    private renderLegend(title: string) {
        const legend = zip<string>(this.legendKeys, this.legendColors)
            .map(([key, color]) =>
                html`<li>
                    <span style="${styleMap({ background: color })}">
                    </span>${key}
                </li>`
            );
        return html`<div class='legend'>
                        <div class='legend-title'>${title}</div>
                        <div class='legend-scale'>
                            <ul class='legend-labels'>
                                ${legend}
                            </ul>
                        </div>
                    </div>`
    }
}

// Without this check, there's a component registry issue when developing locally.
if (!customElements.get(Legend.componentName)) {
    customElements.define(Legend.componentName, Legend);
}

async function render({ model, el }: RenderProps<LegendModel>) {
    const manager = document.createElement(
        Legend.componentName
    ) as Legend;
    manager.model = model;
    el.appendChild(manager);
}

export default { render };
