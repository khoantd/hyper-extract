/**
 * Critical Nodes panel — data-dense sidebar for OntoSight graph views.
 * Fetches /api/rankings and lets users focus nodes in the graph.
 */
(function () {
  const PANEL_ID = "ontosight-critical-panel";
  const STORAGE_KEY = "ontosight:critical-panel-collapsed";

  const ICONS = {
  chevronRight:
    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m9 18 6-6-6-6"/></svg>',
  chevronLeft:
    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m15 18-6-6 6-6"/></svg>',
  hub:
    '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="3"/><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>',
};

  let panelState = {
    rankings: [],
    metric: "composite",
    totalNodes: null,
    collapsed: false,
    activeNodeId: null,
  };

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function formatMetric(metric) {
    const labels = {
      composite: "Composite ranking",
      degree: "By connections",
      betweenness: "By bridge score",
    };
    return labels[metric] || metric;
  }

  function countCritical(rankings) {
    return rankings.filter((r) => r.tier === "critical").length;
  }

  function isCollapsed() {
    try {
      return sessionStorage.getItem(STORAGE_KEY) === "true";
    } catch (_) {
      return false;
    }
  }

  function setCollapsed(value) {
    panelState.collapsed = value;
    try {
      sessionStorage.setItem(STORAGE_KEY, value ? "true" : "false");
    } catch (_) {}
  }

  function getOrCreatePanel() {
    let panel = document.getElementById(PANEL_ID);
    if (!panel) {
      panel = document.createElement("aside");
      panel.id = PANEL_ID;
      document.body.appendChild(panel);
    }
    return panel;
  }

  function renderTierBadge(tier) {
    const safe = escapeHtml(tier || "low");
    return `<span class="cn-tier cn-tier--${safe}"><span class="cn-tier__dot"></span>${safe}</span>`;
  }

  function renderRow(r, index) {
    const tier = r.tier || "low";
    const label = r.label || r.node_id || "";
    const degree = r.degree ?? 0;
    const active =
      panelState.activeNodeId && panelState.activeNodeId === r.node_id
        ? " cn-row--active"
        : "";
    const bridge = r.is_articulation
      ? '<span class="cn-row__bridge">Bridge</span>'
      : "";

    return `<button type="button" class="cn-row${active}" data-node-id="${escapeHtml(r.node_id)}" aria-label="${escapeHtml(label)} — ${degree} connections, ${tier} tier">
      <span class="cn-row__rank">${index + 1}</span>
      <span class="cn-row__name-wrap">
        <span class="cn-row__name" title="${escapeHtml(label)}">${escapeHtml(label)}</span>
        ${bridge}
      </span>
      <span class="cn-row__degree" aria-label="${degree} connections">${degree}</span>
      ${renderTierBadge(tier)}
    </button>`;
  }

  function bindRowHandlers(panel) {
    panel.querySelectorAll(".cn-row").forEach((btn) => {
      btn.addEventListener("click", () => {
        const id = btn.getAttribute("data-node-id");
        if (id) focusNode(id);
      });
      btn.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          const id = btn.getAttribute("data-node-id");
          if (id) focusNode(id);
        }
      });
    });
  }

  function renderLoading(panel) {
    panel.className = "cn-panel";
    panel.setAttribute("aria-label", "Critical nodes");
    panel.setAttribute("aria-busy", "true");
    panel.innerHTML = `
      <div class="cn-loading">
        <div class="cn-skeleton cn-skeleton--title"></div>
        <div class="cn-skeleton cn-skeleton--meta"></div>
        <div class="cn-skeleton cn-skeleton--row"></div>
        <div class="cn-skeleton cn-skeleton--row"></div>
        <div class="cn-skeleton cn-skeleton--row"></div>
      </div>
    `;
  }

  function renderCollapsed(panel) {
    const criticalCount = countCritical(panelState.rankings);
    panel.className = "cn-panel cn-panel--collapsed";
    panel.setAttribute("aria-label", "Show critical nodes panel");
    panel.setAttribute("aria-expanded", "false");
    panel.removeAttribute("aria-busy");

    panel.innerHTML = `
      <button type="button" class="cn-collapsed-btn" aria-label="Expand critical nodes panel, ${criticalCount} critical nodes">
        <span class="cn-collapsed-btn__icon">${ICONS.hub}</span>
        <span class="cn-collapsed-btn__count">${criticalCount}</span>
      </button>
    `;

    panel.querySelector(".cn-collapsed-btn").addEventListener("click", () => {
      setCollapsed(false);
      renderExpanded(panel);
    });
    panel.querySelector(".cn-collapsed-btn").addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        setCollapsed(false);
        renderExpanded(panel);
      }
    });
  }

  function renderExpanded(panel) {
    const { rankings, metric, totalNodes } = panelState;
    const nodeCount = totalNodes != null ? totalNodes : rankings.length;
    const metricLabel = formatMetric(metric || "composite");

    panel.className = "cn-panel";
    panel.setAttribute("aria-label", "Critical nodes");
    panel.setAttribute("aria-expanded", "true");
    panel.removeAttribute("aria-busy");

    const rows = rankings.map((r, i) => renderRow(r, i)).join("");

    panel.innerHTML = `
      <div class="cn-header">
        <div class="cn-header__text">
          <div class="cn-header__title">Critical / Hub Nodes</div>
          <div class="cn-header__meta">${nodeCount} nodes · ${escapeHtml(metricLabel)}</div>
        </div>
        <button type="button" class="cn-collapse-btn" aria-label="Collapse critical nodes panel">
          ${ICONS.chevronRight}
        </button>
      </div>
      <div class="cn-colhdr" role="row">
        <span class="cn-colhdr__rank" role="columnheader">#</span>
        <span role="columnheader">Node</span>
        <span class="cn-colhdr__connections" role="columnheader">Conn.</span>
        <span role="columnheader">Tier</span>
      </div>
      <div class="cn-body" role="table" aria-label="Critical and hub nodes">
        ${rows}
      </div>
    `;

    panel.querySelector(".cn-collapse-btn").addEventListener("click", () => {
      setCollapsed(true);
      renderCollapsed(panel);
    });
    panel.querySelector(".cn-collapse-btn").addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        setCollapsed(true);
        renderCollapsed(panel);
      }
    });

    bindRowHandlers(panel);
  }

  function renderPanel(payload) {
    panelState.rankings = payload.rankings || [];
    panelState.metric = payload.metric || "composite";
    panelState.totalNodes = payload.total_nodes ?? null;
    panelState.collapsed = isCollapsed();

    const panel = getOrCreatePanel();
    if (panelState.collapsed) {
      renderCollapsed(panel);
    } else {
      renderExpanded(panel);
    }
  }

  function updateActiveRow(nodeId) {
    panelState.activeNodeId = nodeId;
    const panel = document.getElementById(PANEL_ID);
    if (!panel || panelState.collapsed) return;

    panel.querySelectorAll(".cn-row").forEach((btn) => {
      const id = btn.getAttribute("data-node-id");
      btn.classList.toggle("cn-row--active", id === nodeId);
    });
  }

  function focusNode(nodeId) {
    panelState.activeNodeId = nodeId;
    updateActiveRow(nodeId);

    window.dispatchEvent(
      new CustomEvent("ontosight:focus-node", { detail: { nodeId } }),
    );
    fetch(`/api/data?ids=${encodeURIComponent(nodeId)}`)
      .then((r) => r.json())
      .then((data) => {
        window.dispatchEvent(
          new CustomEvent("ontosight:graph-data", { detail: data }),
        );
      })
      .catch(() => {});
  }

  function init() {
    const panel = getOrCreatePanel();
    renderLoading(panel);

    fetch("/api/rankings")
      .then((r) => (r.ok ? r.json() : null))
      .then((payload) => {
        if (payload && payload.rankings && payload.rankings.length) {
          renderPanel(payload);
        } else {
          panel.remove();
        }
      })
      .catch(() => {
        panel.remove();
      });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  window.addEventListener("ontosight:graph-data", (event) => {
    const graph = window.__ontosightGraph;
    const data = event.detail;
    if (!graph || graph.destroyed || !data || !data.nodes) return;
    try {
      const nodes = data.nodes.map(({ x, y, ...rest }) => rest);
      const edges = (data.edges || []).map(({ x, y, ...rest }) => rest);
      graph.setData({ nodes, edges });
      graph.render();
      const focusId = nodes.find((n) => n.highlighted)?.id || nodes[0]?.id;
      if (focusId && graph.focusElement) graph.focusElement(focusId);
    } catch (_) {}
  });

  window.addEventListener("ontosight:focus-node", (event) => {
    const nodeId = event.detail && event.detail.nodeId;
    if (nodeId) updateActiveRow(nodeId);

    const graph = window.__ontosightGraph;
    if (graph && !graph.destroyed && nodeId) {
      try {
        if (graph.focusElement) graph.focusElement(nodeId);
        const state = {};
        state[nodeId] = ["selected", "highlighted"];
        graph.setElementState(state);
      } catch (_) {}
    }
  });
})();
