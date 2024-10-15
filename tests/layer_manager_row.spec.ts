import '../js/layer_manager_row';
import { default as rowRender, LayerManagerRow, LayerManagerRowModel } from '../js/layer_manager_row';

describe('<layer-manager-row>', () => {
    async function makeRow(model: LayerManagerRowModel) {
        const container = document.createElement('div');
        rowRender(model, container);
        const element = container.firstElementChild as LayerManagerRow;
        document.body.appendChild(element);
        await element.updateComplete;
        return element;
    }

    it('can be instantiated', async () => {
        const row = await makeRow({
            name: 'Test Layer',
            visible: true,
            opacity: 1,
            is_loading: false,
        });
        expect(row.querySelector('layer-name')?.textContent).toContain('Test Row');
    });
});