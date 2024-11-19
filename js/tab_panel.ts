import { html, css, nothing, LitElement, PropertyValues } from "lit";
import { property, queryAll, queryAssignedElements } from "lit/decorators.js";
import { legacyStyles } from "./ipywidgets_styles";
import { classMap } from "lit/directives/class-map.js";
import { materialStyles } from "./styles";
import { styleMap } from "lit/directives/style-map.js";

function convertToId(name: string | undefined): string {
    return (name || "").trim().replace(" ", "-").toLowerCase();
}

/** The various modes. */
export enum TabMode {
    ALWAYS_SHOW,
    HIDE_ON_SECOND_CLICK,
}

/** The tab configuration, as a string or Material Icon. */
export interface Tab {
    name: string | undefined,
    icon: string | undefined,
    width: number | undefined,
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
        materialStyles,
        css`
            ::slotted(*) {
                display: none;
            }

            ::slotted(.show-tab) {
                display: block;
            }

            .container {
                padding: 0;
                width: 100%;
            }

            .tab-container {
                align-items: center;
                display: flex;
                flex-direction: row;
                justify-content: flex-end;
            }

            .tab-container button {
                border-radius: 5px;
                font-size: 16px;
                height: 28px;
                margin-right: 2px;
                user-select: none;
                width: 28px;
            }

            .tab-container button:first-child {
                margin-left: 0;
            }

            .tab-container button:last-child {
                margin-right: 0;
            }
        `,
    ];

    @property({ type: Array })
    tabs: Tab[] = [];

    @property({ type: Number })
    index = 0;

    @property({ type: Number })
    mode: TabMode = TabMode.HIDE_ON_SECOND_CLICK;

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
        if (changedProperties.has("index") && changedProperties.get("index") != null) {
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
            const id = convertToId(this.tabs[i].name);
            element.setAttribute("id", `tabpanel-${id}-${i}`);
            element.setAttribute("role", "tabpanel");
            element.setAttribute("aria-labelledby", `tab-${id}-${i}`);
        });
        this.tabContentElements[this.index]?.classList.add("show-tab");
    }

    private renderTabs() {
        return this.tabs.map((tab: Tab, i: number) => {
            const id = convertToId(this.tabs[i].name);
            return html`<button
                            id="tab-${id}-${i}"
                            class="${classMap({
                "legacy-button": true,
                "active": i === this.index,
            })}"
                            style="${styleMap({
                width: tab.width ? `${tab.width}px` : null,
            })}"
                            type="button"
                            role="tab"
                            aria-selected="${i === this.index ? true : false}"
                            aria-controls="tabpanel-${id}-${i}"
                            @click=${() => {
                    this.onTabClick(i);
                }}>
                            ${tab.icon ? html`<span class="material-symbols-outlined">${tab.icon}</span>` : nothing}
                            <span>${tab.name}</span>
                        </button>`;
        });
    }

    private onTabClick(index: number) {
        switch (this.mode) {
            case TabMode.HIDE_ON_SECOND_CLICK:
                // Hide the tab panel if clicked twice.
                this.index = this.index === index ? -1 : index;
                break;
            case TabMode.ALWAYS_SHOW:
            default:
                this.index = index;
        }
        this.dispatchEvent(new CustomEvent("tab-clicked", {
            detail: index,
        }));
    }
}

// Without this check, there's a component registry issue when developing locally.
if (!customElements.get(TabPanel.componentName)) {
    customElements.define(TabPanel.componentName, TabPanel);
}
