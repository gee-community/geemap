import { html, css, LitElement, PropertyValues } from "lit";
import { property, queryAll, queryAssignedElements } from "lit/decorators.js";
import { legacyStyles } from "./ipywidgets_styles";
import { classMap } from 'lit/directives/class-map.js';

function convertToId(name: string | undefined): string {
    return (name || "").trim().replace(" ", "-").toLowerCase();
}

/**
 * Defines the <tab-panel> element which accepts N children, with a zero-based
 * index determining which child to show, e.g.:
 * <tab-panel>
 *   <p>Show when index is 0</p>
 *   <p>Show when index is 1</p>
 *   <p>Show when index is 2</p>
 * </tab-panel>
 */
export class TabPanel extends LitElement {
    static get componentName() {
        return `tab-panel`;
    }

    static styles = [
        legacyStyles,
        css`
            .container {
                padding: 0;
                width: 100%;
            }

            button.tab {
                border: 1px solid #ddd;
                border-bottom: none;
                border-top-left-radius: 15px;
                border-top-right-radius: 15px;
                display: inline-block;
                min-width: 88px;
                padding: 0 10px;
            }

            button.active {
                background-color: var(--colab-primary-surface-color, --jp-layout-color2, white);
            }

            ::slotted(*) {
                display: none;
            }
    
            ::slotted(.show-tab) {
                display: block;
            }
        `,
    ];

    @property({ type: Array })
    tabNames: string[] = [];

    @property({ type: Number })
    index = 0;

    /**
     * The tab elements.
     */
    @queryAll(".tab") tabElements!: HTMLDivElement[];

    /**
     * The tab content element to show at a given index. Note that child
     * elements are set to display block or none based on the index, and
     * top-level text elements are ignored.
     */
    @queryAssignedElements() tabContentElements!: HTMLElement[];


    render() {
        return html`
            <div class="container">
                <div role="tablist" class="tab-container">
                    ${this.renderTabs()}
                </div>
                <slot @slotchange=${this.updateSlotChildren}></slot>
            </div>
        `;
    }

    override update(changedProperties: PropertyValues) {
        super.update(changedProperties);
        if (changedProperties.has("index")) {
            this.updateSlotChildren();
        }
    }

    private updateSlotChildren() {
        if (!this.tabContentElements) {
            return;
        }
        // Show the element at the current index.
        this.tabContentElements.forEach((element: HTMLElement, i: number) => {
            element.classList.remove("show-tab");

            // Also add accessibility attributes.
            const id = convertToId(this.tabNames[i]);
            element.setAttribute("id", `tabpanel-${id}-${i}`);
            element.setAttribute("role", "tabpanel");
            element.setAttribute("aria-labelledby", `tab-${id}-${i}`);
        });
        this.tabContentElements[this.index]?.classList.add("show-tab");
    }

    private renderTabs() {
        return this.tabNames.map((tabName: string, i: number) => {
            const id = convertToId(this.tabNames[i]);
            return html`<button
                            id="tab-${id}-${i}"
                            class="${classMap({
                                "legacy-button": true,
                                "tab": true,
                                "active": i === this.index, 
                            })}"
                            type="button"
                            role="tab"
                            aria-selected="${i === this.index ? true : false}"
                            aria-controls="tabpanel-${id}-${i}"
                            @click=${() => {
                                this.index = i;
                            }}>
                            <span>${tabName}</span>
                        </button>`;
        });
    }
}

// Without this check, there's a component registry issue when developing locally.
if (!customElements.get(TabPanel.componentName)) {
    customElements.define(TabPanel.componentName, TabPanel);
}
