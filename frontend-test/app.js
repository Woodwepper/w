const STORAGE_KEYS = {
  apiBase: "factoryLab.apiBase",
  selectedWorldId: "factoryLab.selectedWorldId",
};

const state = {
  apiBase: localStorage.getItem(STORAGE_KEYS.apiBase) || "http://127.0.0.1:8000",
  selectedWorldId: numberOrNull(localStorage.getItem(STORAGE_KEYS.selectedWorldId)),
  selectedFactoryId: null,
  selectedModuleId: null,
  worlds: [],
  world: null,
  catalog: {
    machines: [],
    modules: [],
    recipes: [],
    su_sources: [],
    factory_levels: [],
  },
  activeCatalogTab: "machines",
  logItems: [],
};

const catalogEndpoints = {
  machines: "machines",
  modules: "modules",
  recipes: "recipes",
  su_sources: "su-sources",
  factory_levels: "factory-levels",
};

function $(selector) {
  return document.querySelector(selector);
}

function $all(selector) {
  return Array.from(document.querySelectorAll(selector));
}

function numberOrNull(value) {
  if (value === null || value === undefined || value === "") {
    return null;
  }
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function normalizeApiBase(value) {
  return String(value || "http://127.0.0.1:8000").trim().replace(/\/+$/, "");
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function safeArray(value) {
  return Array.isArray(value) ? value : [];
}

function safeObject(value) {
  return value && typeof value === "object" && !Array.isArray(value) ? value : {};
}

function formatJson(value) {
  return JSON.stringify(value, null, 2);
}

function titleCase(value) {
  return String(value || "")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function itemPairs(items) {
  const entries = Object.entries(safeObject(items));
  if (entries.length === 0) {
    return '<span class="mini-token">empty</span>';
  }
  return entries
    .map(([itemId, amount]) => {
      return `<span class="mini-token">${escapeHtml(itemId)}: ${escapeHtml(amount)}</span>`;
    })
    .join("");
}

function statusBadge(status) {
  const normalized = String(status || "idle");
  return `<span class="badge ${escapeHtml(normalized)}">${escapeHtml(normalized)}</span>`;
}

async function api(path, options = {}) {
  const url = `${state.apiBase}${path}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });

  const text = await response.text();
  let data = {};
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = { detail: text };
    }
  }

  if (!response.ok) {
    throw new Error(formatApiError(response.status, data));
  }

  return data;
}

function formatApiError(status, data) {
  const detail = data && data.detail !== undefined ? data.detail : data;
  if (Array.isArray(detail)) {
    return `${status}: ${detail.map((item) => item.msg || JSON.stringify(item)).join("; ")}`;
  }
  if (typeof detail === "object") {
    return `${status}: ${JSON.stringify(detail)}`;
  }
  return `${status}: ${detail || "Request failed"}`;
}

function postJson(path, body) {
  return api(path, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

function patchJson(path, body) {
  return api(path, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

function deleteRequest(path) {
  return api(path, {
    method: "DELETE",
  });
}

function log(message, type = "info") {
  const time = new Date().toLocaleTimeString();
  state.logItems.unshift({ time, message, type });
  state.logItems = state.logItems.slice(0, 80);
  renderLog();
}

function renderLog() {
  const target = $("#actionLog");
  if (!target) {
    return;
  }
  if (state.logItems.length === 0) {
    target.innerHTML = '<div class="empty">No actions yet</div>';
    return;
  }
  target.innerHTML = state.logItems
    .map((entry) => {
      return `
        <div class="log-entry ${escapeHtml(entry.type)}">
          <span class="log-time">${escapeHtml(entry.time)}</span>
          <span class="log-message">${escapeHtml(entry.message)}</span>
        </div>
      `;
    })
    .join("");
}

async function runAction(label, action) {
  try {
    await action();
    await refreshAll(false);
    log(`${label} complete`, "success");
  } catch (error) {
    log(`${label} failed: ${error.message}`, "error");
  }
}

async function refreshAll(writeLog = true) {
  try {
    await loadWorlds();
    await loadSelectedWorld();
    await loadCatalog();
    render();
    if (writeLog) {
      log("Refresh complete", "success");
    }
  } catch (error) {
    log(`Refresh failed: ${error.message}`, "error");
    render();
  }
}

async function loadWorlds() {
  const data = await api("/api/worlds");
  state.worlds = safeArray(data.worlds);

  if (
    state.selectedWorldId !== null &&
    !state.worlds.some((world) => Number(world.id) === Number(state.selectedWorldId))
  ) {
    state.selectedWorldId = null;
  }

  if (state.selectedWorldId === null && state.worlds.length > 0) {
    state.selectedWorldId = Number(state.worlds[0].id);
  }

  persistSelectedWorld();
}

async function loadSelectedWorld() {
  if (state.selectedWorldId === null) {
    state.world = null;
    return;
  }
  state.world = await api(`/api/worlds/${state.selectedWorldId}`);

  const factories = safeArray(state.world.factories);
  if (
    state.selectedFactoryId !== null &&
    !factories.some((factory) => Number(factory.id) === Number(state.selectedFactoryId))
  ) {
    state.selectedFactoryId = null;
    state.selectedModuleId = null;
  }

  if (state.selectedFactoryId === null && factories.length > 0) {
    state.selectedFactoryId = Number(factories[0].id);
  }
}

async function loadCatalog() {
  if (state.selectedWorldId === null) {
    state.catalog = {
      machines: [],
      modules: [],
      recipes: [],
      su_sources: [],
      factory_levels: [],
    };
    return;
  }

  const entries = await Promise.all(
    Object.entries(catalogEndpoints).map(async ([key, endpoint]) => {
      const data = await api(`/api/worlds/${state.selectedWorldId}/catalog/${endpoint}`);
      return [key, data[key] || []];
    })
  );

  state.catalog = Object.fromEntries(entries);
}

function persistApiBase() {
  localStorage.setItem(STORAGE_KEYS.apiBase, state.apiBase);
}

function persistSelectedWorld() {
  if (state.selectedWorldId === null) {
    localStorage.removeItem(STORAGE_KEYS.selectedWorldId);
    return;
  }
  localStorage.setItem(STORAGE_KEYS.selectedWorldId, String(state.selectedWorldId));
}

function requireWorldId() {
  if (state.selectedWorldId === null) {
    throw new Error("Create or select a world first");
  }
  return state.selectedWorldId;
}

function selectedWorld() {
  return state.world;
}

function factories() {
  return safeArray(selectedWorld()?.factories);
}

function suSources() {
  return safeArray(selectedWorld()?.su_sources);
}

function powerNetworks() {
  return safeArray(selectedWorld()?.power_networks);
}

function findFactory(factoryId) {
  return factories().find((factory) => Number(factory.id) === Number(factoryId)) || null;
}

function findModule(factory, moduleId) {
  return safeArray(factory?.modules).find((module) => Number(module.id) === Number(moduleId)) || null;
}

function findSelectedFactory() {
  return findFactory(state.selectedFactoryId);
}

function moduleDefinition(moduleType) {
  return state.catalog.modules.find((definition) => definition.id === moduleType) || null;
}

function machineDefinition(machineType) {
  return state.catalog.machines.find((definition) => definition.id === machineType) || null;
}

function recipeDefinition(recipeId) {
  return state.catalog.recipes.find((definition) => definition.id === recipeId) || null;
}

function sourceStressOutput(source) {
  if (!source || source.enabled === false) {
    return 0;
  }
  const definition = state.catalog.su_sources.find((item) => item.id === source.source_type);
  return Number(definition?.su_output || 0);
}

function machineStressRequired(machine) {
  if (!machine) {
    return 0;
  }
  const definition = machineDefinition(machine.machine_type);
  return Number(definition?.su_cost || 0);
}

function moduleStressRequired(module) {
  return safeArray(module?.installed_machines).reduce((total, machine) => {
    return total + machineStressRequired(machine);
  }, 0);
}

function factoryStressRequired(factory) {
  return safeArray(factory?.modules).reduce((total, module) => {
    return total + moduleStressRequired(module);
  }, 0);
}

function worldStressSnapshot() {
  const produced = suSources().reduce((total, source) => total + sourceStressOutput(source), 0);
  const consumed = factories().reduce((total, factory) => total + factoryStressRequired(factory), 0);
  const remaining = produced - consumed;
  const world = selectedWorld();

  return {
    produced,
    consumed,
    remaining,
    api_produced: Number(world?.su_produced || 0),
    api_required: Number(world?.su_required ?? world?.su_requiered ?? 0),
    api_available: Number(world?.su_available || 0),
  };
}

function networkStressSnapshot(network) {
  const sourceIds = new Set(safeArray(network?.source_ids).map((sourceId) => Number(sourceId)));
  const produced = suSources().reduce((total, source) => {
    return sourceIds.has(Number(source.id)) ? total + sourceStressOutput(source) : total;
  }, 0);

  const consumed = safeArray(network?.consumers).reduce((total, consumer) => {
    if (consumer.consumer_type !== "factory") {
      return total;
    }
    return total + factoryStressRequired(findFactory(consumer.consumer_id));
  }, 0);

  return {
    produced,
    consumed,
    remaining: produced - consumed,
  };
}

function stressBalanceClass(remaining) {
  if (remaining < 0) {
    return "bad";
  }
  if (remaining === 0) {
    return "warn";
  }
  return "good";
}

function renderStressMeter(label, current, total) {
  const safeTotal = Math.max(Number(total || 0), 0);
  const safeCurrent = Math.max(Number(current || 0), 0);
  const percent = safeTotal <= 0 ? 0 : Math.min(100, Math.round((safeCurrent / safeTotal) * 100));
  const balanceClass = safeCurrent > safeTotal || (safeCurrent > 0 && safeTotal <= 0) ? "bad" : "good";

  return `
    <div class="stress-meter ${balanceClass}">
      <div class="stress-meter-head">
        <span>${escapeHtml(label)}</span>
        <strong>${escapeHtml(safeCurrent)} / ${escapeHtml(safeTotal)} SU</strong>
      </div>
      <div class="stress-track">
        <div class="stress-fill" style="width: ${escapeHtml(percent)}%"></div>
      </div>
    </div>
  `;
}

function renderStressBadge(label, value, className = "") {
  return `<span class="mini-token stress-token ${escapeHtml(className)}">${escapeHtml(label)} ${escapeHtml(value)} SU</span>`;
}

function render() {
  renderWorlds();
  renderInventory();
  renderCatalog();
  renderStats();
  renderBoard();
  renderFactoryDetail();
  renderSummary();
  renderFormOptions();
  renderLog();
}

function renderWorlds() {
  $("#worldCount").textContent = String(state.worlds.length);
  const target = $("#worldsList");
  if (state.worlds.length === 0) {
    target.innerHTML = '<div class="empty">No worlds</div>';
    return;
  }

  target.innerHTML = state.worlds
    .map((world) => {
      const active = Number(world.id) === Number(state.selectedWorldId) ? "active" : "";
      return `
        <button class="world-button ${active}" type="button" data-world-id="${escapeHtml(world.id)}">
          <span>${escapeHtml(world.name || `World ${world.id}`)}</span>
          <span class="pill">#${escapeHtml(world.id)}</span>
        </button>
      `;
    })
    .join("");

  $all("[data-world-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      state.selectedWorldId = Number(button.dataset.worldId);
      state.selectedFactoryId = null;
      state.selectedModuleId = null;
      persistSelectedWorld();
      await refreshAll();
    });
  });
}

function renderInventory() {
  const inventory = safeObject(selectedWorld()?.inventory);
  const entries = Object.entries(inventory);
  const target = $("#inventoryList");

  if (entries.length === 0) {
    target.innerHTML = '<div class="empty">Empty</div>';
    return;
  }

  target.innerHTML = entries
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([itemId, amount]) => {
      return `
        <div class="inventory-item">
          <strong>${escapeHtml(itemId)}</strong>
          <span>${escapeHtml(amount)}</span>
        </div>
      `;
    })
    .join("");
}

function renderCatalog() {
  const target = $("#catalogList");
  const items = safeArray(state.catalog[state.activeCatalogTab]);

  $all("[data-catalog-tab]").forEach((button) => {
    button.classList.toggle("active", button.dataset.catalogTab === state.activeCatalogTab);
  });

  if (items.length === 0) {
    target.innerHTML = '<div class="empty">No catalog data</div>';
    return;
  }

  target.innerHTML = items.map(renderCatalogCard).join("");
}

function renderCatalogCard(item) {
  if (state.activeCatalogTab === "machines") {
    return `
      <div class="catalog-card">
        <strong>${escapeHtml(item.name || item.id)}</strong>
        <span>${escapeHtml(item.id)} - ${escapeHtml(item.su_cost || 0)} SU</span>
        <div class="catalog-meta">Recipes: ${escapeHtml(safeArray(item.allowed_recipes).length)}</div>
      </div>
    `;
  }

  if (state.activeCatalogTab === "modules") {
    return `
      <div class="catalog-card">
        <strong>${escapeHtml(item.name || item.id)}</strong>
        <span>${escapeHtml(item.id)}</span>
        <div class="catalog-meta">Machines: ${escapeHtml(safeArray(item.allowed_machine_types).join(", ") || "none")}</div>
      </div>
    `;
  }

  if (state.activeCatalogTab === "recipes") {
    return `
      <div class="catalog-card">
        <strong>${escapeHtml(item.name || item.id)}</strong>
        <span>${escapeHtml(item.id)} - ${escapeHtml(item.duration || 0)}s</span>
        <div class="catalog-meta">In: ${escapeHtml(JSON.stringify(safeObject(item.input_items)))}</div>
        <div class="catalog-meta">Out: ${escapeHtml(JSON.stringify(safeObject(item.output_items)))}</div>
      </div>
    `;
  }

  if (state.activeCatalogTab === "factory_levels") {
    return `
      <div class="catalog-card">
        <strong>Factory Level ${escapeHtml(item.level)}</strong>
        <span>${escapeHtml(item.module_slots)} modules, ${escapeHtml(item.machine_slots_per_module)} machines/module</span>
        <div class="catalog-meta">Cost: ${escapeHtml(JSON.stringify(safeObject(item.upgrade_cost)))}</div>
      </div>
    `;
  }

  return `
    <div class="catalog-card">
      <strong>${escapeHtml(item.name || item.id)}</strong>
      <span>${escapeHtml(item.id)} - ${escapeHtml(item.su_output || 0)} SU</span>
      <div class="catalog-meta">Cost: ${escapeHtml(JSON.stringify(safeObject(item.build_cost)))}</div>
    </div>
  `;
}

function renderStats() {
  const world = selectedWorld();
  const stress = worldStressSnapshot();
  const values = [
    { label: "Time", value: world?.simulated_time ?? 0 },
    { label: "Factories", value: factories().length },
    { label: "Sources", value: suSources().length },
    { label: "Networks", value: powerNetworks().length },
    { label: "SU Produced", value: stress.produced, note: `API ${stress.api_produced}` },
    { label: "SU Used", value: stress.consumed, note: `API ${stress.api_required}` },
    {
      label: "SU Left",
      value: stress.remaining,
      note: `API ${stress.api_available}`,
      className: stressBalanceClass(stress.remaining),
    },
  ];

  $("#worldStats").innerHTML = values
    .map((item) => {
      return `
        <div class="stat-card ${escapeHtml(item.className || "")}">
          <span>${escapeHtml(item.label)}</span>
          <strong>${escapeHtml(item.value)}</strong>
          ${item.note ? `<small>${escapeHtml(item.note)}</small>` : ""}
        </div>
      `;
    })
    .join("");

  $("#selectedWorldLabel").textContent = world ? `${world.name} #${world.id}` : "No world";
}

function renderBoard() {
  const board = $("#board");
  const factoryCards = factories().map(renderFactoryCard).join("") || '<div class="empty">No factories</div>';
  const sourceCards = suSources().map(renderSourceCard).join("") || '<div class="empty">No sources</div>';
  const networkCards = powerNetworks().map(renderNetworkCard).join("") || '<div class="empty">No networks</div>';

  board.innerHTML = `
    <div class="board-column">
      <h3>Factories</h3>
      ${factoryCards}
    </div>
    <div class="board-column">
      <h3>SU Sources</h3>
      ${sourceCards}
    </div>
    <div class="board-column">
      <h3>Power Networks</h3>
      ${networkCards}
    </div>
  `;

  $all(".factory-card").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedFactoryId = Number(button.dataset.factoryId);
      state.selectedModuleId = null;
      render();
    });
  });
}

function renderFactoryCard(factory) {
  const selected = Number(factory.id) === Number(state.selectedFactoryId) ? "selected" : "";
  const stress = factoryStressRequired(factory);
  const worldStress = worldStressSnapshot();
  return `
    <button class="entity-card factory-card ${selected}" type="button" data-factory-id="${escapeHtml(factory.id)}">
      <div class="entity-head">
        <div class="entity-name">
          <strong>${escapeHtml(factory.name || `Factory ${factory.id}`)}</strong>
          <span>#${escapeHtml(factory.id)} level ${escapeHtml(factory.level || 1)} priority ${escapeHtml(factory.priority ?? 100)}</span>
        </div>
        ${statusBadge(factory.status)}
      </div>
      <div class="entity-meta">Modules: ${escapeHtml(safeArray(factory.modules).length)}</div>
      ${renderStressMeter("Factory stress", stress, worldStress.produced)}
      <div class="resource-pair">${itemPairs(factory.output_items)}</div>
    </button>
  `;
}

function renderSourceCard(source) {
  const definition = state.catalog.su_sources.find((item) => item.id === source.source_type);
  const stressOutput = sourceStressOutput(source);
  return `
    <div class="entity-card">
      <div class="entity-head">
        <div class="entity-name">
          <strong>${escapeHtml(source.name || source.source_type)}</strong>
          <span>#${escapeHtml(source.id)} ${escapeHtml(source.source_type)}</span>
        </div>
        ${statusBadge(source.enabled === false ? "inactive" : source.status || "active")}
      </div>
      <div class="entity-meta">Position ${escapeHtml(source.x ?? 0)}, ${escapeHtml(source.y ?? 0)}</div>
      <div class="resource-pair">
        ${renderStressBadge("Produces", stressOutput, "good")}
        <span class="mini-token">${escapeHtml(definition?.id || source.source_type)}</span>
      </div>
    </div>
  `;
}

function renderNetworkCard(network) {
  const stress = networkStressSnapshot(network);
  const consumers = safeArray(network.consumers)
    .map((consumer) => `${consumer.consumer_type}#${consumer.consumer_id}`)
    .join(", ");

  return `
    <div class="entity-card">
      <div class="entity-head">
        <div class="entity-name">
          <strong>${escapeHtml(network.name || `Network ${network.id}`)}</strong>
          <span>#${escapeHtml(network.id)}</span>
        </div>
        <span class="badge powered">network</span>
      </div>
      ${renderStressMeter("Network load", stress.consumed, stress.produced)}
      <div class="resource-pair">
        ${renderStressBadge("Left", stress.remaining, stressBalanceClass(stress.remaining))}
      </div>
      <div class="entity-meta">Sources: ${escapeHtml(safeArray(network.source_ids).join(", ") || "none")}</div>
      <div class="entity-meta">Consumers: ${escapeHtml(consumers || "none")}</div>
    </div>
  `;
}

function renderFactoryDetail() {
  const factory = findSelectedFactory();
  const target = $("#factoryDetail");

  if (!factory) {
    $("#selectedFactoryLabel").textContent = "None";
    target.innerHTML = '<div class="empty">Select a factory</div>';
    return;
  }

  $("#selectedFactoryLabel").textContent = `${factory.name} #${factory.id}`;

  const factoryStress = factoryStressRequired(factory);
  const worldStress = worldStressSnapshot();
  const modulesHtml = safeArray(factory.modules).map(renderModuleRow).join("") || '<div class="empty">No modules</div>';

  target.innerHTML = `
    <div class="factory-detail">
      <div class="factory-overview">
        <div class="stat-card"><span>Status</span><strong>${escapeHtml(factory.status || "idle")}</strong></div>
        <div class="stat-card"><span>Level</span><strong>${escapeHtml(factory.level || 1)}</strong></div>
        <div class="stat-card"><span>Priority</span><strong>${escapeHtml(factory.priority ?? 100)}</strong></div>
        <div class="stat-card"><span>Modules</span><strong>${escapeHtml(safeArray(factory.modules).length)}</strong></div>
        <div class="stat-card ${escapeHtml(stressBalanceClass(worldStress.produced - factoryStress))}">
          <span>Factory SU</span>
          <strong>${escapeHtml(factoryStress)}</strong>
          <small>of ${escapeHtml(worldStress.produced)} produced</small>
        </div>
      </div>
      ${renderStressMeter("Selected factory load", factoryStress, worldStress.produced)}
      <div>
        <h3>Inputs</h3>
        <div class="resource-pair">${itemPairs(factory.input_items)}</div>
      </div>
      <div>
        <h3>Outputs</h3>
        <div class="resource-pair">${itemPairs(factory.output_items)}</div>
      </div>
      <div class="module-list">${modulesHtml}</div>
    </div>
  `;

  $all(".module-row").forEach((row) => {
    row.addEventListener("click", () => {
      state.selectedModuleId = Number(row.dataset.moduleId);
      render();
    });
  });
}

function renderModuleRow(module) {
  const selected = Number(module.id) === Number(state.selectedModuleId) ? "selected" : "";
  const definition = moduleDefinition(module.module_type);
  const machines = safeArray(module.installed_machines);
  const moduleStress = moduleStressRequired(module);
  const factoryStress = factoryStressRequired(findSelectedFactory());
  const machineHtml = machines.map(renderMachineChip).join("") || '<div class="empty">No machines</div>';

  return `
    <div class="module-row ${selected}" data-module-id="${escapeHtml(module.id)}">
      <div class="module-toolbar">
        <div class="entity-name">
          <strong>${escapeHtml(definition?.name || module.module_type)}</strong>
          <span>#${escapeHtml(module.id)} recipe ${escapeHtml(module.active_recipe || "none")}</span>
        </div>
        ${statusBadge(module.status)}
      </div>
      <div class="resource-pair">
        ${renderStressBadge("Module uses", moduleStress, moduleStress > 0 ? "warn" : "")}
        <span class="mini-token">${escapeHtml(machines.length)} machines</span>
      </div>
      ${renderStressMeter("Module share", moduleStress, factoryStress)}
      <div class="machine-list">${machineHtml}</div>
    </div>
  `;
}

function renderMachineChip(machine) {
  const definition = machineDefinition(machine.machine_type);
  const progress = Number(machine.progress || 0).toFixed(2);
  const stress = machineStressRequired(machine);
  return `
    <div class="machine-chip">
      <strong>${escapeHtml(definition?.name || machine.machine_type)}</strong>
      <span>#${escapeHtml(machine.id)} level ${escapeHtml(machine.level || 1)}</span>
      <span>Stress ${escapeHtml(stress)} SU</span>
      <span>Progress ${escapeHtml(progress)}</span>
      ${statusBadge(machine.status)}
    </div>
  `;
}

function renderSummary() {
  const world = selectedWorld();
  if (!world) {
    $("#worldSummary").textContent = "{}";
    return;
  }

  const stress = worldStressSnapshot();
  const summary = {
    id: world.id,
    name: world.name,
    simulated_time: world.simulated_time,
    inventory: world.inventory,
    stress_configured: {
      produced: stress.produced,
      consumed: stress.consumed,
      remaining: stress.remaining,
    },
    stress_last_tick: {
      produced: stress.api_produced,
      required: stress.api_required,
      available: stress.api_available,
    },
    su_produced: world.su_produced,
    su_required: world.su_required ?? world.su_requiered,
    su_available: world.su_available,
    factories: factories().map((factory) => ({
      id: factory.id,
      name: factory.name,
      status: factory.status,
      level: factory.level,
      priority: factory.priority,
      stress_required: factoryStressRequired(factory),
      input_items: factory.input_items,
      output_items: factory.output_items,
      modules: safeArray(factory.modules).map((module) => ({
        id: module.id,
        module_type: module.module_type,
        active_recipe: module.active_recipe,
        status: module.status,
        stress_required: moduleStressRequired(module),
        machines: safeArray(module.installed_machines).map((machine) => ({
          id: machine.id,
          machine_type: machine.machine_type,
          level: machine.level,
          stress_required: machineStressRequired(machine),
          progress: machine.progress,
          status: machine.status,
        })),
      })),
    })),
    su_sources: world.su_sources,
    power_networks: world.power_networks,
  };

  $("#worldSummary").textContent = formatJson(summary);
}

function renderFormOptions() {
  const factoryOptions = factories().map((factory) => ({
    value: factory.id,
    label: `${factory.name || "Factory"} #${factory.id}`,
  }));
  const networkOptions = powerNetworks().map((network) => ({
    value: network.id,
    label: `${network.name || "Network"} #${network.id}`,
  }));
  const sourceOptions = suSources().map((source) => ({
    value: source.id,
    label: `${source.name || source.source_type} #${source.id}`,
  }));
  const moduleTypeOptions = state.catalog.modules.map((module) => ({
    value: module.id,
    label: module.name || module.id,
  }));
  const suTypeOptions = state.catalog.su_sources.map((source) => ({
    value: source.id,
    label: `${source.name || source.id} (${source.su_output || 0} SU)`,
  }));

  [
    "moduleFactorySelect",
    "recipeFactorySelect",
    "machineFactorySelect",
    "inputFactorySelect",
    "collectFactorySelect",
    "connectFactorySelect",
  ].forEach((selectId) => {
    setSelectOptions(selectId, factoryOptions, "No factories", false, state.selectedFactoryId);
  });

  ["connectSourceNetworkSelect", "connectFactoryNetworkSelect"].forEach((selectId) => {
    setSelectOptions(selectId, networkOptions, "No networks");
  });

  setSelectOptions("connectSourceSelect", sourceOptions, "No sources");
  setSelectOptions("moduleTypeSelect", moduleTypeOptions, "No module types");
  setSelectOptions("suTypeSelect", suTypeOptions, "No SU sources");

  updateCreateModuleRecipeOptions();
  updateRecipeModuleOptions();
  updateSetRecipeOptions();
  updateMachineModuleOptions();
  updateMachineTypeOptions();
}

function setSelectOptions(selectId, options, emptyText, allowBlank = false, preferredValue = null) {
  const select = $(`#${selectId}`);
  if (!select) {
    return;
  }

  const currentValue = preferredValue !== null && preferredValue !== undefined ? String(preferredValue) : select.value;
  const normalized = safeArray(options);
  let html = "";

  if (allowBlank) {
    html += `<option value="">${escapeHtml(emptyText || "None")}</option>`;
  }

  if (normalized.length === 0) {
    html += `<option value="">${escapeHtml(emptyText || "None")}</option>`;
  } else {
    html += normalized
      .map((option) => `<option value="${escapeHtml(option.value)}">${escapeHtml(option.label)}</option>`)
      .join("");
  }

  select.innerHTML = html;

  if (normalized.some((option) => String(option.value) === currentValue)) {
    select.value = currentValue;
  } else if (allowBlank || normalized.length === 0) {
    select.value = "";
  } else {
    select.value = String(normalized[0].value);
  }
}

function updateCreateModuleRecipeOptions() {
  const moduleType = $("#moduleTypeSelect")?.value;
  const definition = moduleDefinition(moduleType);
  const recipeOptions = safeArray(definition?.allowed_recipes).map((recipeId) => {
    const recipe = recipeDefinition(recipeId);
    return {
      value: recipeId,
      label: recipe?.name || recipeId,
    };
  });
  setSelectOptions("moduleRecipeSelect", recipeOptions, "No recipe", true);
}

function updateRecipeModuleOptions() {
  const factory = findFactory($("#recipeFactorySelect")?.value);
  const moduleOptions = safeArray(factory?.modules).map((module) => ({
    value: module.id,
    label: `${module.module_type} #${module.id}`,
  }));
  setSelectOptions("recipeModuleSelect", moduleOptions, "No modules", false, state.selectedModuleId);
}

function updateSetRecipeOptions() {
  const factory = findFactory($("#recipeFactorySelect")?.value);
  const module = findModule(factory, $("#recipeModuleSelect")?.value);
  const definition = moduleDefinition(module?.module_type);
  const recipeOptions = safeArray(definition?.allowed_recipes).map((recipeId) => {
    const recipe = recipeDefinition(recipeId);
    return {
      value: recipeId,
      label: recipe?.name || recipeId,
    };
  });
  setSelectOptions("recipeSelect", recipeOptions, "No recipes");
}

function updateMachineModuleOptions() {
  const factory = findFactory($("#machineFactorySelect")?.value);
  const moduleOptions = safeArray(factory?.modules).map((module) => ({
    value: module.id,
    label: `${module.module_type} #${module.id}`,
  }));
  setSelectOptions("machineModuleSelect", moduleOptions, "No modules", false, state.selectedModuleId);
}

function updateMachineTypeOptions() {
  const factory = findFactory($("#machineFactorySelect")?.value);
  const module = findModule(factory, $("#machineModuleSelect")?.value);
  const definition = moduleDefinition(module?.module_type);
  const allowedTypes = safeArray(definition?.allowed_machine_types);
  const machineOptions = state.catalog.machines
    .filter((machine) => allowedTypes.length === 0 || allowedTypes.includes(machine.id))
    .map((machine) => ({
      value: machine.id,
      label: `${machine.name || machine.id} (${machine.su_cost || 0} SU)`,
    }));
  setSelectOptions("machineTypeSelect", machineOptions, "No machines");
}

async function createWorld() {
  const data = await postJson("/api/worlds", { name: "Factory Lab Test World" });
  state.selectedWorldId = Number(data.id);
  state.selectedFactoryId = null;
  state.selectedModuleId = null;
  persistSelectedWorld();
}

async function tickWorld(seconds) {
  const worldId = requireWorldId();
  await postJson(`/api/worlds/${worldId}/tick`, { seconds });
}

async function addInventoryItem() {
  const worldId = requireWorldId();
  const itemId = $("#inventoryItemInput").value.trim();
  const amount = Number($("#inventoryAmountInput").value);
  await postJson(`/api/worlds/${worldId}/inventory/test-add`, { item_id: itemId, amount });
}

async function createFactory() {
  const worldId = requireWorldId();
  const body = {
    name: $("#factoryNameInput").value.trim() || "Factory",
    x: Number($("#factoryXInput").value || 0),
    y: Number($("#factoryYInput").value || 0),
    icon: $("#factoryIconInput").value.trim() || "factory",
    visual_theme: $("#factoryThemeInput").value.trim() || "andesite",
    priority: Number($("#factoryPriorityInput").value || 100),
  };
  const factory = await postJson(`/api/worlds/${worldId}/factories`, body);
  state.selectedFactoryId = Number(factory.id);
  state.selectedModuleId = null;
}

async function createModule() {
  const worldId = requireWorldId();
  const factoryId = $("#moduleFactorySelect").value;
  const activeRecipe = $("#moduleRecipeSelect").value || null;
  const factory = await postJson(`/api/worlds/${worldId}/factories/${factoryId}/modules`, {
    module_type: $("#moduleTypeSelect").value,
    active_recipe: activeRecipe,
  });
  const lastModule = safeArray(factory.modules).at(-1);
  state.selectedFactoryId = Number(factory.id);
  state.selectedModuleId = lastModule ? Number(lastModule.id) : null;
}

async function setModuleRecipe() {
  const worldId = requireWorldId();
  const factoryId = $("#recipeFactorySelect").value;
  const moduleId = $("#recipeModuleSelect").value;
  const recipeId = $("#recipeSelect").value;
  await postJson(`/api/worlds/${worldId}/factories/${factoryId}/modules/${moduleId}/recipe`, {
    recipe_id: recipeId,
  });
  state.selectedFactoryId = Number(factoryId);
  state.selectedModuleId = Number(moduleId);
}

async function clearModuleRecipe() {
  const worldId = requireWorldId();
  const factoryId = $("#recipeFactorySelect").value;
  const moduleId = $("#recipeModuleSelect").value;
  await deleteRequest(`/api/worlds/${worldId}/factories/${factoryId}/modules/${moduleId}/recipe`);
  state.selectedFactoryId = Number(factoryId);
  state.selectedModuleId = Number(moduleId);
}

async function buildInstallMachine() {
  const worldId = requireWorldId();
  const factoryId = $("#machineFactorySelect").value;
  const moduleId = $("#machineModuleSelect").value;
  const body = {
    machine_type: $("#machineTypeSelect").value,
    level: Number($("#machineLevelInput").value || 1),
    metadata: {},
  };
  await postJson(
    `/api/worlds/${worldId}/factories/${factoryId}/modules/${moduleId}/machines/build-install`,
    body
  );
  state.selectedFactoryId = Number(factoryId);
  state.selectedModuleId = Number(moduleId);
}

async function addFactoryInput() {
  const worldId = requireWorldId();
  const factoryId = $("#inputFactorySelect").value;
  await postJson(`/api/worlds/${worldId}/factories/${factoryId}/inputs`, {
    item_id: $("#factoryInputItemInput").value.trim(),
    amount: Number($("#factoryInputAmountInput").value),
  });
  state.selectedFactoryId = Number(factoryId);
}

async function collectFactoryOutput() {
  const worldId = requireWorldId();
  const factoryId = $("#collectFactorySelect").value;
  await postJson(`/api/worlds/${worldId}/factories/${factoryId}/collect-output`, {
    item_id: $("#collectItemInput").value.trim(),
    amount: Number($("#collectAmountInput").value),
  });
  state.selectedFactoryId = Number(factoryId);
}

async function createSuSource() {
  const worldId = requireWorldId();
  await postJson(`/api/worlds/${worldId}/su-sources`, {
    source_type: $("#suTypeSelect").value,
    name: $("#suNameInput").value.trim() || "SU Source",
    x: Number($("#suXInput").value || 0),
    y: Number($("#suYInput").value || 0),
  });
}

async function createPowerNetwork() {
  const worldId = requireWorldId();
  await postJson(`/api/worlds/${worldId}/power-networks`, {
    name: $("#networkNameInput").value.trim() || "Power Network",
  });
}

async function connectSourceToNetwork() {
  const worldId = requireWorldId();
  const networkId = $("#connectSourceNetworkSelect").value;
  await postJson(`/api/worlds/${worldId}/power-networks/${networkId}/sources`, {
    source_id: Number($("#connectSourceSelect").value),
  });
}

async function connectFactoryToNetwork() {
  const worldId = requireWorldId();
  const networkId = $("#connectFactoryNetworkSelect").value;
  const factoryId = Number($("#connectFactorySelect").value);
  await postJson(`/api/worlds/${worldId}/power-networks/${networkId}/consumers`, {
    consumer_type: "factory",
    consumer_id: factoryId,
  });
  state.selectedFactoryId = factoryId;
}

async function quickSetup() {
  let worldId = state.selectedWorldId;
  if (worldId === null) {
    const world = await postJson("/api/worlds", { name: "Factory Lab Quick World" });
    state.selectedWorldId = Number(world.id);
    worldId = state.selectedWorldId;
    persistSelectedWorld();
    await refreshAll(false);
    log(`Created world #${worldId}`, "success");
  }

  const inventoryItems = [
    ["andesite_alloy", 50],
    ["iron_sheet", 50],
    ["shaft", 50],
    ["machine_parts", 20],
  ];

  for (const [itemId, amount] of inventoryItems) {
    await postJson(`/api/worlds/${worldId}/inventory/test-add`, { item_id: itemId, amount });
    await refreshAll(false);
  }
  log("Seeded build inventory", "success");

  const factory = await postJson(`/api/worlds/${worldId}/factories`, {
    name: "Ironworks",
    x: 0,
    y: 0,
    icon: "factory",
    visual_theme: "andesite",
    priority: 10,
  });
  state.selectedFactoryId = Number(factory.id);
  await refreshAll(false);

  const factoryWithModule = await postJson(`/api/worlds/${worldId}/factories/${factory.id}/modules`, {
    module_type: "pressing_line",
    active_recipe: "press_iron_sheet",
  });
  const module = safeArray(factoryWithModule.modules).at(-1);
  if (!module) {
    throw new Error("Quick setup could not create pressing_line module");
  }
  state.selectedModuleId = Number(module.id);
  await refreshAll(false);

  for (let index = 0; index < 2; index += 1) {
    await postJson(
      `/api/worlds/${worldId}/factories/${factory.id}/modules/${module.id}/machines/build-install`,
      { machine_type: "mechanical_press", level: 1, metadata: {} }
    );
    await refreshAll(false);
  }

  await postJson(`/api/worlds/${worldId}/factories/${factory.id}/inputs`, {
    item_id: "iron_ingot",
    amount: 20,
  });
  await refreshAll(false);

  const source = await postJson(`/api/worlds/${worldId}/su-sources`, {
    source_type: "water_wheel",
    name: "Water Wheel",
    x: 6,
    y: 0,
  });
  await refreshAll(false);

  const network = await postJson(`/api/worlds/${worldId}/power-networks`, {
    name: "Main Grid",
  });
  await refreshAll(false);

  await postJson(`/api/worlds/${worldId}/power-networks/${network.id}/sources`, {
    source_id: source.id,
  });
  await refreshAll(false);

  await postJson(`/api/worlds/${worldId}/power-networks/${network.id}/consumers`, {
    consumer_type: "factory",
    consumer_id: factory.id,
  });
  await refreshAll(false);

  await postJson(`/api/worlds/${worldId}/tick`, { seconds: 10 });
  await refreshAll(false);

  const refreshedFactory = findFactory(factory.id);
  const ironInput = refreshedFactory?.input_items?.iron_ingot ?? 0;
  const ironSheet = refreshedFactory?.output_items?.iron_sheet ?? 0;
  log(`Quick setup result: iron_ingot ${ironInput}, iron_sheet ${ironSheet}`, "success");
}

function bindEvents() {
  $("#apiBaseInput").value = state.apiBase;

  $("#saveApiBaseBtn").addEventListener("click", () => {
    state.apiBase = normalizeApiBase($("#apiBaseInput").value);
    $("#apiBaseInput").value = state.apiBase;
    persistApiBase();
    log(`API base set to ${state.apiBase}`, "success");
  });

  $("#createWorldBtn").addEventListener("click", () => runAction("Create world", createWorld));
  $("#refreshBtn").addEventListener("click", () => refreshAll());
  $("#quickSetupBtn").addEventListener("click", () => runAction("Quick setup", quickSetup));
  $("#tick1Btn").addEventListener("click", () => runAction("Tick 1s", () => tickWorld(1)));
  $("#tick10Btn").addEventListener("click", () => runAction("Tick 10s", () => tickWorld(10)));
  $("#clearLogBtn").addEventListener("click", () => {
    state.logItems = [];
    renderLog();
  });

  $all("[data-catalog-tab]").forEach((button) => {
    button.addEventListener("click", () => {
      state.activeCatalogTab = button.dataset.catalogTab;
      renderCatalog();
    });
  });

  bindForm("addInventoryForm", "Add inventory", addInventoryItem);
  bindForm("createFactoryForm", "Create factory", createFactory);
  bindForm("createModuleForm", "Create module", createModule);
  bindForm("setRecipeForm", "Set recipe", setModuleRecipe);
  bindForm("buildMachineForm", "Build machine", buildInstallMachine);
  bindForm("factoryInputForm", "Add factory input", addFactoryInput);
  bindForm("collectOutputForm", "Collect output", collectFactoryOutput);
  bindForm("createSUSourceForm", "Create SU source", createSuSource);
  bindForm("createNetworkForm", "Create network", createPowerNetwork);
  bindForm("connectSourceForm", "Connect source", connectSourceToNetwork);
  bindForm("connectFactoryForm", "Connect factory", connectFactoryToNetwork);

  $("#clearRecipeBtn").addEventListener("click", () => runAction("Clear recipe", clearModuleRecipe));

  $("#moduleTypeSelect").addEventListener("change", updateCreateModuleRecipeOptions);
  $("#recipeFactorySelect").addEventListener("change", () => {
    updateRecipeModuleOptions();
    updateSetRecipeOptions();
  });
  $("#recipeModuleSelect").addEventListener("change", updateSetRecipeOptions);
  $("#machineFactorySelect").addEventListener("change", () => {
    updateMachineModuleOptions();
    updateMachineTypeOptions();
  });
  $("#machineModuleSelect").addEventListener("change", updateMachineTypeOptions);
}

function bindForm(formId, label, handler) {
  $(`#${formId}`).addEventListener("submit", (event) => {
    event.preventDefault();
    runAction(label, handler);
  });
}

async function init() {
  bindEvents();
  render();
  log("Frontend ready", "info");
  await refreshAll(false);
}

document.addEventListener("DOMContentLoaded", init);
