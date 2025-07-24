import {
    css,
    html,
    LitElement,
    nothing,
    PropertyValues,
    TemplateResult
} from "lit";
import { property } from "lit/decorators.js";
import { legacyStyles } from "./ipywidgets_styles";
import { materialStyles } from "./styles";

export interface Node {
    label?: string;
    children?: Array<Node>;
    expanded?: boolean;
    topLevel?: boolean;
}

export class TreeNode extends LitElement {
    static get componentName() {
        return `tree-node`;
    }

    static override styles = [
        legacyStyles,
        materialStyles,
        css`
            .node {
                align-items: center;
                cursor: pointer;
                display: flex;
            }

            .node-text {
                height: auto;
                line-height: 24px;
            }

            .node:hover {
                background-color: var(--jp-layout-color2);
                margin-left: -100%;
                padding-left: 100%;
            }

            .icon {
                font-size: 13px;
                width: 20px;
            }

            ul {
                list-style: none;
                padding-left: 20px;
                margin: 0;
            }
        `,
    ];

    @property() node: Node = {};
    @property({ type: Boolean, reflect: true }) expanded: boolean = false;

    override updated(changedProperties: PropertyValues<TreeNode>): void {
        super.updated(changedProperties);
        if (changedProperties.has("node") && this.node) {
            if ("expanded" in this.node) {
                this.expanded = this.node.expanded ?? false;
            }
        }
    }

    override render(): TemplateResult {
        return html`
            <div
                class="node ${this.expanded ? "expanded" : ""}"
                @click="${this.toggleExpand}"
            >
                ${this.renderBullet()} ${this.renderIcon()}
                <span class="legacy-text node-text">${this.node.label}</span>
            </div>
            ${this.renderChildren()}
        `;
    }

    private toggleExpand(): void {
        this.expanded = !this.expanded;
    }

    private hasChildren(): boolean {
        return !!this.node.children?.length;
    }

    private renderChildren(): TemplateResult | typeof nothing {
        if (this.expanded && this.hasChildren()) {
            return html`<ul>${this.node.children?.map(this.renderChild)}</ul>`;
        }
        return nothing;
    }

    private renderChild(child: Node): TemplateResult {
        return html`<li><tree-node .node="${child}"></tree-node></li>`;
    }

    private renderBullet(): TemplateResult | typeof nothing {
        if (this.node.topLevel) {
            if (this.expanded) {
                return html`
                    <span class="icon material-symbols-outlined"
                        >indeterminate_check_box</span
                    >
                `;
            }
            return html`<span class="icon material-symbols-outlined">add_box</span>`;
        } else if (this.hasChildren()) {
            if (this.expanded) {
                return html`<span class="icon material-symbols-outlined">remove</span>`;
            }
            return html`<span class="icon material-symbols-outlined">add</span>`;
        }
        return html`<span class="icon"></span>`;
    }

    private renderIcon(): TemplateResult | typeof nothing {
        if (this.node.topLevel) {
            return html`<span class="icon material-symbols-outlined"
                >inventory_2</span
            >`;
        } else if (this.hasChildren()) {
            if (this.expanded) {
                return html`
                    <span class="icon material-symbols-outlined">folder_open</span>
                `;
            }
            return html`<span class="icon material-symbols-outlined">folder</span>`;
        }
        return html`<span class="icon material-symbols-outlined">draft</span>`;
    }
}

// Without this check, there's a component registry issue when developing locally.
if (!customElements.get(TreeNode.componentName)) {
    customElements.define(TreeNode.componentName, TreeNode);
}