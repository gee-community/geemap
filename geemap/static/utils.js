// js/utils.ts
async function unpackModels(modelIds, manager) {
  return Promise.all(
    modelIds.map((id) => manager.get_model(id.slice("IPY_MODEL_".length)))
  );
}
function loadFonts() {
  if (!document.querySelector(".custom-fonts")) {
    const styleElement = document.createElement("style");
    styleElement.classList.add("custom-fonts");
    styleElement.textContent = '@import "https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined";';
    document.body.appendChild(styleElement);
  }
}
async function updateChildren(container, model) {
  const children = model.get("children");
  const child_models = await unpackModels(children, model.widget_manager);
  const child_views = await Promise.all(
    child_models.map((model2) => model2.widget_manager.create_view(model2))
  );
  container.innerHTML = ``;
  for (const child_view of child_views) {
    container.appendChild(child_view.el);
  }
}
export {
  loadFonts,
  updateChildren
};
