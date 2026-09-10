/* eslint-disable no-undef */
(() => {
  const LEAGUES = {
    AL: { id: 103, label: "American League" },
    NL: { id: 104, label: "National League" },
  };

  const DIVISIONS = {
    AL: {
      East: { id: 201, label: "American League East" },
      Central: { id: 202, label: "American League Central" },
      West: { id: 200, label: "American League West" },
    },
    NL: {
      East: { id: 204, label: "National League East" },
      Central: { id: 205, label: "National League Central" },
      West: { id: 203, label: "National League West" },
    },
  };

  const DEFAULT_CONFIG = {
    type: "custom:mlb-standings-card",
    mode: "division",
    league: "AL",
    division: "East",
    title: "MLB Standings",
  };

  const escapeHtml = (value) =>
    String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");

  const formatPct = (value) => {
    if (value === null || value === undefined || Number.isNaN(Number(value))) {
      return "-";
    }
    return Number(value).toFixed(3);
  };

  const leagueKeyFromValue = (value) => {
    const normalized = String(value ?? "AL").trim().toUpperCase();
    return normalized === "NL" ? "NL" : "AL";
  };

  const divisionKeyFromValue = (leagueKey, value) => {
    const normalized = String(value ?? "East").trim().toLowerCase();
    const options = DIVISIONS[leagueKey];
    const match = Object.keys(options).find((key) => key.toLowerCase() === normalized || options[key].label.toLowerCase() === normalized);
    return match || "East";
  };

  const getLeagueLabel = (leagueKey) => LEAGUES[leagueKey].label;
  const getDivisionLabel = (leagueKey, divisionKey) => DIVISIONS[leagueKey][divisionKey].label;
  const getLeagueId = (leagueKey) => LEAGUES[leagueKey].id;
  const getDivisionId = (leagueKey, divisionKey) => DIVISIONS[leagueKey][divisionKey].id;

  const getDivisionKeys = (leagueKey) => Object.keys(DIVISIONS[leagueKey] ?? {});

  const findSummaryEntity = (hass, leagueKey, mode, divisionKey) => {
    const leagueId = getLeagueId(leagueKey);
    const divisionId = getDivisionId(leagueKey, divisionKey);
    const states = Object.values(hass?.states ?? {});

    if (mode === "postseason") {
      return states.find(
        (state) =>
          state?.entity_id?.startsWith("sensor.") &&
          state.attributes?.league_id === leagueId &&
          Array.isArray(state.attributes?.bracket),
      );
    }

    return states.find(
      (state) =>
        state?.entity_id?.startsWith("sensor.") &&
        state.attributes?.league_id === leagueId &&
        state.attributes?.division_id === divisionId &&
        Array.isArray(state.attributes?.standings),
    );
  };

  class MlbStandingsCard extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({ mode: "open" });
      this._config = { ...DEFAULT_CONFIG };
      this._hass = null;
      this._data = null;
      this._error = null;
      this.shadowRoot.addEventListener("click", (event) => {
        const button = event.target.closest("button[data-action]");
        if (!button) {
          return;
        }

        this._applyQuickAction(button.dataset.action, button.dataset.value);
      });
    }

    static getStubConfig() {
      return { ...DEFAULT_CONFIG };
    }

    static getConfigElement() {
      return document.createElement("mlb-standings-card-editor");
    }

    setConfig(config) {
      if (!config) {
        throw new Error("Invalid configuration");
      }
      this._config = {
        ...DEFAULT_CONFIG,
        ...config,
        type: "custom:mlb-standings-card",
      };
      this._syncData();
      this._render();
    }

    set hass(hass) {
      this._hass = hass;
      this._syncData();
      this._render();
    }

    getCardSize() {
      if (!this._data) {
        return 4;
      }
      const rows = this._config.mode === "postseason" ? this._data.bracket.length : this._data.rows.length;
      return Math.max(4, Math.min(10, rows + 3));
    }

    _syncData() {
      if (!this._hass) {
        this._data = null;
        return;
      }

      const leagueKey = leagueKeyFromValue(this._config.league);
      const divisionKey = divisionKeyFromValue(leagueKey, this._config.division);
      const source = findSummaryEntity(this._hass, leagueKey, this._config.mode, divisionKey);

      if (!source) {
        this._data = null;
        this._error = `Could not find the MLB summary sensor for ${getLeagueLabel(leagueKey)}${this._config.mode === "division" ? ` / ${getDivisionLabel(leagueKey, divisionKey)}` : ""}.`;
        return;
      }

      this._error = null;
      if (this._config.mode === "postseason") {
        this._data = {
          title: this._config.title?.trim() || `${getLeagueLabel(leagueKey)} Postseason`,
          subtitle: `${getLeagueLabel(leagueKey)} playoff bracket`,
          source,
          leagueKey,
          divisionKey,
          bracket: Array.isArray(source.attributes?.bracket) ? source.attributes.bracket : [],
        };
        return;
      }

      this._data = {
        title: this._config.title?.trim() || `${getDivisionLabel(leagueKey, divisionKey)} Standings`,
        subtitle: `${getLeagueLabel(leagueKey)} division table`,
        source,
        leagueKey,
        divisionKey,
        rows: Array.isArray(source.attributes?.standings) ? source.attributes.standings : [],
      };
    }

    _render() {
      if (!this.shadowRoot) {
        return;
      }

      const card = document.createElement("ha-card");
      card.style.overflow = "hidden";
      card.innerHTML = this._renderContent();
      this.shadowRoot.innerHTML = "";
      this.shadowRoot.appendChild(card);
    }

    _renderContent() {
      const mode = this._config.mode === "postseason" ? "postseason" : "division";
      const leagueKey = leagueKeyFromValue(this._config.league);
      const divisionKey = divisionKeyFromValue(leagueKey, this._config.division);
      const leagueLabel = getLeagueLabel(leagueKey);
      const divisionLabel = getDivisionLabel(leagueKey, divisionKey);
      const title = this._data?.title || this._config.title?.trim() || (mode === "postseason" ? `${leagueLabel} Postseason` : `${divisionLabel} Standings`);
      const subtitle = this._data?.subtitle || (mode === "postseason" ? `${leagueLabel} playoff bracket` : `${leagueLabel} division table`);
      const divisionKeys = getDivisionKeys(leagueKey);

      if (this._error) {
        return `
          <style>${CARD_STYLES}</style>
          <div class="shell shell-error">
            <div class="header">
              <div>
                <div class="eyebrow">MLB Standings</div>
                <div class="title">${escapeHtml(title)}</div>
                <div class="subtitle">${escapeHtml(subtitle)}</div>
              </div>
              <div class="actions">
                ${this._renderLeagueButtons(leagueKey, mode)}
                ${mode === "division" ? this._renderDivisionButtons(leagueKey, divisionKeys, divisionKey) : ""}
              </div>
            </div>
            <div class="empty">${escapeHtml(this._error)}</div>
          </div>
        `;
      }

      if (!this._data) {
        return `
          <style>${CARD_STYLES}</style>
          <div class="shell">
            <div class="header">
              <div>
                <div class="eyebrow">MLB Standings</div>
                <div class="title">${escapeHtml(title)}</div>
                <div class="subtitle">${escapeHtml(subtitle)}</div>
              </div>
              <div class="actions">
                ${this._renderLeagueButtons(leagueKey, mode)}
                ${mode === "division" ? this._renderDivisionButtons(leagueKey, divisionKeys, divisionKey) : ""}
              </div>
            </div>
            <div class="empty">No standings available.</div>
          </div>
        `;
      }

      if (mode === "postseason") {
        return `
          <style>${CARD_STYLES}</style>
          <div class="shell shell-postseason">
            <div class="header">
              <div>
                <div class="eyebrow">${escapeHtml(leagueLabel)}</div>
                <div class="title">${escapeHtml(title)}</div>
                <div class="subtitle">${escapeHtml(subtitle)}</div>
              </div>
              <div class="header-right">
                <div class="actions">
                  ${this._renderLeagueButtons(leagueKey, mode)}
                </div>
                <div class="badge">${this._data.bracket.length} teams</div>
              </div>
            </div>
            <div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Seed</th>
                    <th>Team</th>
                    <th>Division</th>
                    <th>W</th>
                    <th>L</th>
                    <th>PCT</th>
                    <th>Clinched</th>
                  </tr>
                </thead>
                <tbody>
                  ${this._data.bracket
                    .map(
                      (row) => `
                        <tr class="${row.clinched ? "clinched" : ""}">
                          <td><span class="seed">${escapeHtml(row.seed)}</span></td>
                          <td class="team">${escapeHtml(row.team)}</td>
                          <td>${escapeHtml(row.division)}</td>
                          <td>${escapeHtml(row.wins)}</td>
                          <td>${escapeHtml(row.losses)}</td>
                          <td>${escapeHtml(formatPct(row.winning_percentage))}</td>
                          <td>${row.clinched ? "Yes" : "No"}</td>
                        </tr>
                      `,
                    )
                    .join("")}
                </tbody>
              </table>
            </div>
          </div>
        `;
      }

      return `
        <style>${CARD_STYLES}</style>
        <div class="shell shell-division">
          <div class="header">
            <div>
              <div class="eyebrow">${escapeHtml(leagueLabel)}</div>
              <div class="title">${escapeHtml(title)}</div>
              <div class="subtitle">${escapeHtml(subtitle)}</div>
            </div>
            <div class="header-right">
              <div class="actions">
                ${this._renderLeagueButtons(leagueKey, mode)}
                ${this._renderDivisionButtons(leagueKey, divisionKeys, divisionKey)}
              </div>
              <div class="badge">${this._data.rows.length} teams</div>
            </div>
          </div>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Team</th>
                  <th>W</th>
                  <th>L</th>
                  <th>GB</th>
                  <th>PCT</th>
                  <th>Streak</th>
                </tr>
              </thead>
              <tbody>
                ${this._data.rows
                  .map(
                    (row) => `
                      <tr class="${row.leader ? "leader" : ""}">
                        <td><span class="seed">${escapeHtml(row.rank ?? "-")}</span></td>
                        <td class="team">${escapeHtml(row.team)}</td>
                        <td>${escapeHtml(row.wins)}</td>
                        <td>${escapeHtml(row.losses)}</td>
                        <td>${escapeHtml(row.games_back)}</td>
                        <td>${escapeHtml(formatPct(row.winning_percentage))}</td>
                        <td>${escapeHtml(row.streak || "-")}</td>
                      </tr>
                    `,
                  )
                  .join("")}
              </tbody>
            </table>
          </div>
        </div>
      `;
    }

    _renderLeagueButtons(activeLeagueKey, mode) {
      return Object.keys(LEAGUES)
        .map(
          (key) => `
            <button
              class="chip ${key === activeLeagueKey ? "chip-active" : ""}"
              data-action="league"
              data-value="${key}"
              type="button"
            >
              ${escapeHtml(key)}
            </button>
          `,
        )
        .join("");
    }

    _renderDivisionButtons(leagueKey, divisionKeys, activeDivisionKey) {
      return divisionKeys
        .map(
          (key) => `
            <button
              class="chip ${key === activeDivisionKey ? "chip-active" : ""}"
              data-action="division"
              data-value="${key}"
              type="button"
            >
              ${escapeHtml(key)}
            </button>
          `,
        )
        .join("");
    }

    _applyQuickAction(action, value) {
      if (action === "league") {
        const nextLeague = leagueKeyFromValue(value);
        const nextDivision = divisionKeyFromValue(nextLeague, this._config.division);
        this._config = {
          ...this._config,
          league: nextLeague,
          division: nextDivision,
        };
        this._syncData();
        this._render();
        return;
      }

      if (action === "division") {
        const leagueKey = leagueKeyFromValue(this._config.league);
        this._config = {
          ...this._config,
          division: divisionKeyFromValue(leagueKey, value),
        };
        this._syncData();
        this._render();
      }
    }
  }

  const CARD_STYLES = `
    .shell {
      --mlb-bg: color-mix(in srgb, var(--card-background-color, var(--ha-card-background, #fff)) 96%, #0f2d5c 4%);
      --mlb-border: color-mix(in srgb, var(--divider-color, #d0d5dd) 65%, transparent);
      --mlb-accent: color-mix(in srgb, var(--primary-color, #0f2d5c) 72%, #d61f26 28%);
      --mlb-text: var(--primary-text-color, #1f2937);
      --mlb-muted: var(--secondary-text-color, #667085);
      --mlb-chip: color-mix(in srgb, var(--mlb-accent) 14%, transparent);
      background:
        radial-gradient(circle at top right, color-mix(in srgb, var(--mlb-accent) 22%, transparent), transparent 36%),
        linear-gradient(180deg, color-mix(in srgb, var(--mlb-bg) 96%, white 4%), var(--mlb-bg));
      color: var(--mlb-text);
      border: 1px solid var(--mlb-border);
      border-radius: 18px;
      overflow: hidden;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
    }

    .shell-error {
      border-color: color-mix(in srgb, #d61f26 36%, var(--mlb-border));
    }

    .header {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;
      padding: 18px 18px 14px;
      border-bottom: 1px solid var(--mlb-border);
    }

    .eyebrow {
      text-transform: uppercase;
      letter-spacing: 0.14em;
      font-size: 0.68rem;
      color: var(--mlb-muted);
      margin-bottom: 4px;
      font-weight: 700;
    }

    .title {
      font-size: 1.05rem;
      font-weight: 800;
      line-height: 1.15;
    }

    .subtitle {
      margin-top: 4px;
      font-size: 0.84rem;
      color: var(--mlb-muted);
    }

    .badge {
      flex: 0 0 auto;
      align-self: center;
      padding: 6px 10px;
      border-radius: 999px;
      background: var(--mlb-chip);
      color: var(--mlb-accent);
      font-size: 0.78rem;
      font-weight: 700;
      white-space: nowrap;
    }

    .header-right {
      display: grid;
      justify-items: end;
      gap: 8px;
    }

    .actions {
      display: flex;
      flex-wrap: wrap;
      justify-content: flex-end;
      gap: 8px;
    }

    .chip {
      appearance: none;
      border: 1px solid var(--mlb-border);
      background: rgba(255, 255, 255, 0.18);
      color: var(--mlb-muted);
      border-radius: 999px;
      padding: 6px 10px;
      font-size: 0.78rem;
      font-weight: 700;
      cursor: pointer;
      transition: transform 120ms ease, background 120ms ease, color 120ms ease, border-color 120ms ease;
    }

    .chip:hover {
      transform: translateY(-1px);
      border-color: var(--mlb-accent);
      color: var(--mlb-accent);
    }

    .chip-active {
      background: var(--mlb-chip);
      border-color: var(--mlb-accent);
      color: var(--mlb-accent);
    }

    .table-wrap {
      overflow-x: auto;
      padding: 6px 0 2px;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      min-width: 100%;
    }

    thead th {
      text-align: left;
      font-size: 0.74rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      padding: 10px 18px 8px;
      color: var(--mlb-muted);
      white-space: nowrap;
    }

    tbody td {
      padding: 11px 18px;
      border-top: 1px solid color-mix(in srgb, var(--mlb-border) 75%, transparent);
      font-size: 0.92rem;
      vertical-align: middle;
    }

    tbody tr.leader {
      background: color-mix(in srgb, var(--mlb-chip) 54%, transparent);
    }

    tbody tr.clinched {
      background: color-mix(in srgb, var(--mlb-chip) 38%, transparent);
    }

    .seed {
      display: inline-flex;
      min-width: 2rem;
      align-items: center;
      justify-content: center;
      padding: 4px 8px;
      border-radius: 999px;
      background: var(--mlb-chip);
      color: var(--mlb-accent);
      font-size: 0.78rem;
      font-weight: 800;
    }

    .team {
      font-weight: 700;
    }

    .empty {
      padding: 18px;
      color: var(--mlb-muted);
      font-size: 0.92rem;
    }

    @media (max-width: 640px) {
      .header {
        padding: 16px 14px 12px;
      }

      thead th,
      tbody td {
        padding-left: 14px;
        padding-right: 14px;
      }
    }
  `;

  class MlbStandingsCardEditor extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({ mode: "open" });
      this._config = { ...DEFAULT_CONFIG };
    }

    set hass(hass) {
      this._hass = hass;
      this._render();
    }

    setConfig(config) {
      this._config = {
        ...DEFAULT_CONFIG,
        ...config,
        type: "custom:mlb-standings-card",
      };
      this._render();
    }

    _emitConfigChange(partial) {
      this._config = {
        ...this._config,
        ...partial,
      };
      this.dispatchEvent(
        new CustomEvent("config-changed", {
          detail: { config: this._config },
          bubbles: true,
          composed: true,
        }),
      );
      this._render();
    }

    _render() {
      if (!this.shadowRoot) {
        return;
      }

      const leagueKey = leagueKeyFromValue(this._config.league);
      const divisionKey = divisionKeyFromValue(leagueKey, this._config.division);
      const mode = this._config.mode === "postseason" ? "postseason" : "division";

      this.shadowRoot.innerHTML = `
        <style>
          .panel {
            display: grid;
            gap: 16px;
            padding: 18px;
            color: var(--primary-text-color, #1f2937);
          }

          .section {
            display: grid;
            gap: 8px;
          }

          .section-title {
            font-size: 0.8rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: var(--secondary-text-color, #667085);
          }

          label {
            display: grid;
            gap: 6px;
            font-size: 0.92rem;
            font-weight: 600;
          }

          input,
          select {
            border: 1px solid var(--divider-color, #d0d5dd);
            border-radius: 12px;
            padding: 12px 14px;
            background: var(--card-background-color, #fff);
            color: inherit;
            font: inherit;
          }

          input:focus,
          select:focus {
            outline: 2px solid color-mix(in srgb, var(--primary-color, #0f2d5c) 25%, transparent);
            border-color: var(--primary-color, #0f2d5c);
          }

          .row {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 12px;
          }

          .hint {
            color: var(--secondary-text-color, #667085);
            font-size: 0.84rem;
            line-height: 1.4;
          }

          .pill {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            width: fit-content;
            padding: 6px 10px;
            border-radius: 999px;
            background: color-mix(in srgb, var(--primary-color, #0f2d5c) 12%, transparent);
            color: var(--primary-color, #0f2d5c);
            font-size: 0.8rem;
            font-weight: 700;
          }

          .mode-note {
            padding: 12px 14px;
            border-radius: 14px;
            background: color-mix(in srgb, var(--primary-color, #0f2d5c) 8%, transparent);
            color: var(--secondary-text-color, #667085);
            font-size: 0.88rem;
            line-height: 1.45;
          }
        </style>
        <div class="panel">
          <div class="section">
            <div class="section-title">Card Settings</div>
            <label>
              Title
              <input id="title" type="text" value="${escapeHtml(this._config.title || "")}" placeholder="MLB Standings" />
            </label>
            <div class="row">
              <label>
                Mode
                <select id="mode">
                  <option value="division" ${mode === "division" ? "selected" : ""}>Division standings</option>
                  <option value="postseason" ${mode === "postseason" ? "selected" : ""}>Postseason bracket</option>
                </select>
              </label>
              <label>
                League
                <select id="league">
                  <option value="AL" ${leagueKey === "AL" ? "selected" : ""}>American League</option>
                  <option value="NL" ${leagueKey === "NL" ? "selected" : ""}>National League</option>
                </select>
              </label>
            </div>
            <label>
              Division
              <select id="division" ${mode === "postseason" ? "disabled" : ""}>
                ${Object.keys(DIVISIONS[leagueKey])
                  .map((key) => `<option value="${key}" ${key === divisionKey ? "selected" : ""}>${DIVISIONS[leagueKey][key].label}</option>`)
                  .join("")}
              </select>
            </label>
          </div>

          <div class="section">
            <div class="section-title">Preview Rules</div>
            <div class="pill">Auto-matches summary sensors</div>
            <div class="mode-note">
              The card looks for the MLB summary sensors created by the integration and matches them by league and division.
              Postseason mode uses the league playoff summary, while division mode uses the selected division summary.
            </div>
            <div class="hint">
              To use the card, add the JavaScript file as a Lovelace resource and then add a card with this type:
              <strong>custom:mlb-standings-card</strong>.
            </div>
          </div>
        </div>
      `;

      const titleInput = this.shadowRoot.getElementById("title");
      const modeSelect = this.shadowRoot.getElementById("mode");
      const leagueSelect = this.shadowRoot.getElementById("league");
      const divisionSelect = this.shadowRoot.getElementById("division");

      titleInput?.addEventListener("input", (event) => {
        this._emitConfigChange({ title: event.target.value });
      });

      modeSelect?.addEventListener("change", (event) => {
        const nextMode = event.target.value === "postseason" ? "postseason" : "division";
        this._emitConfigChange({ mode: nextMode });
      });

      leagueSelect?.addEventListener("change", (event) => {
        const nextLeague = leagueKeyFromValue(event.target.value);
        const nextDivision = divisionKeyFromValue(nextLeague, divisionSelect?.value || this._config.division);
        this._emitConfigChange({ league: nextLeague, division: nextDivision });
      });

      divisionSelect?.addEventListener("change", (event) => {
        this._emitConfigChange({ division: divisionKeyFromValue(leagueKey, event.target.value) });
      });
    }
  }

  if (!customElements.get("mlb-standings-card")) {
    customElements.define("mlb-standings-card", MlbStandingsCard);
  }

  if (!customElements.get("mlb-standings-card-editor")) {
    customElements.define("mlb-standings-card-editor", MlbStandingsCardEditor);
  }

  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "mlb-standings-card",
    name: "MLB Standings Card",
    preview: false,
    description: "Compact division standings and postseason bracket card for Home Assistant.",
  });
})();
