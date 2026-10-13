/* ==========================================================================
   SIDDHAM — THE SOUTH ASIA INSCRIPTIONS ARCHIVE (IN00001–IN00215)
   Interactive Client Application, IAST-to-Devanagari Transliterator,
   Map Visualizer, Analytics Engine & Multi-Mode Epigraphic Reader
   ========================================================================== */

(function () {
  "use strict";

  const ARCHIVE = window.SIDDHAM_ARCHIVE || { inscriptions: [], glossary: [], metre_guide: {} };
  const INSCRIPTIONS = ARCHIVE.inscriptions || [];
  const INSCRIPTION_BY_ID = new Map(INSCRIPTIONS.map((item) => [item.id, item]));

  // Application State
  const state = {
    activeTab: "explorer",
    searchQuery: "",
    selectedDynasty: "ALL",
    selectedObjectCat: "ALL",
    selectedMaterialCat: "ALL",
    selectedMetre: "ALL",
    sortBy: "id_asc",
    viewMode: "grid", // 'grid' | 'table'
    onlyBookmarked: false,
    bookmarks: new Set(JSON.parse(localStorage.getItem("siddham_bookmarks") || "[]")),
    pageSize: 36,
    currentPage: 1,
    // Reader Modal State
    currentItem: null,
    editionMode: "smooth", // 'smooth' | 'diplomatic' | 'verses'
    scriptMode: "dual", // 'iast' | 'deva' | 'dual'
    // Comparator State
    compareLeftId: "IN00001",
    compareRightId: "IN00094",
    // Map instance
    map: null,
    mapMarkers: [],
  };

  // ========================================================================
  // 1. DIACRITIC NORMALIZATION & IAST -> DEVANAGARI TRANSLITERATION ENGINE
  // ========================================================================
  function normalizeForSearch(str) {
    if (!str) return "";
    return str
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/ḷ/g, "l")
      .replace(/ṃ/g, "m")
      .replace(/ḥ/g, "h");
  }

  // Pre-compute search index string for fast filtering
  INSCRIPTIONS.forEach((item) => {
    const rawSearch = [
      item.id,
      item.object_id,
      item.title,
      item.ruler,
      item.dynasty,
      item.repository,
      item.orig_place,
      item.place_label,
      item.material,
      item.object_type,
      item.script_desc,
      item.provenance,
      (item.metres || []).join(" "),
      item.full_text,
    ].join(" ");
    item._searchNorm = normalizeForSearch(rawSearch);
  });

  const VOWELS_STANDALONE = {
    a: "अ", ā: "आ", i: "इ", ī: "ई", u: "उ", ū: "ऊ",
    ṛ: "ऋ", ṝ: "ॠ", ḷ: "ऌ", e: "ए", ai: "ऐ", o: "ओ", au: "औ",
  };

  const VOWEL_MATRAS = {
    a: "", ā: "ा", i: "ि", ī: "ी", u: "ु", ū: "ू",
    ṛ: "ृ", ṝ: "ॄ", ḷ: "ॢ", e: "े", ai: "ै", o: "ो", au: "ौ",
  };

  const CONSONANTS = {
    kh: "ख", gh: "घ", ch: "छ", jh: "झ", ṭh: "ठ", ḍh: "ढ",
    th: "थ", dh: "ध", ph: "फ", bh: "भ",
    k: "क", g: "ग", ṅ: "ङ", c: "च", j: "ज", ñ: "ञ",
    ṭ: "ट", ḍ: "ड", ṇ: "ण", t: "त", d: "द", n: "न",
    p: "प", b: "ब", m: "म", y: "य", r: "र", l: "ल", ḷ: "ळ",
    v: "व", ś: "श", ṣ: "ष", s: "स", h: "ह",
  };

  function transliterateWordToDeva(word) {
    let out = "";
    let i = 0;
    const s = word
      .replace(/M/g, "ṃ")
      .replace(/H/g, "ḥ")
      .replace(/N/g, "n")
      .replace(/T/g, "t")
      .toLowerCase();

    const len = s.length;
    while (i < len) {
      const two = s.slice(i, i + 2);
      const one = s[i];

      // Punctuation / symbols
      if (two === "||") {
        out += "॥";
        i += 2;
        continue;
      }
      if (one === "|") {
        out += "।";
        i += 1;
        continue;
      }
      if (one === "'") {
        out += "ऽ";
        i += 1;
        continue;
      }
      if (one === "ṃ") {
        out += "ं";
        i += 1;
        continue;
      }
      if (one === "ḥ") {
        out += "ः";
        i += 1;
        continue;
      }
      if (one === "-") {
        out += "-";
        i += 1;
        continue;
      }

      // Check consonant (2-char aspirated first, then 1-char)
      let cons = null;
      let consLen = 0;
      if (CONSONANTS[two]) {
        cons = CONSONANTS[two];
        consLen = 2;
      } else if (CONSONANTS[one]) {
        cons = CONSONANTS[one];
        consLen = 1;
      }

      if (cons) {
        i += consLen;
        // Look ahead for vowel matra
        const vTwo = s.slice(i, i + 2);
        const vOne = s[i];
        if (vTwo === "ai" || vTwo === "au") {
          out += cons + VOWEL_MATRAS[vTwo];
          i += 2;
        } else if (vOne !== undefined && VOWEL_MATRAS[vOne] !== undefined) {
          out += cons + VOWEL_MATRAS[vOne];
          i += 1;
        } else {
          out += cons + "्";
        }
        continue;
      }

      // Standalone vowel
      if (two === "ai" || two === "au") {
        out += VOWELS_STANDALONE[two];
        i += 2;
        continue;
      }
      if (VOWELS_STANDALONE[one]) {
        out += VOWELS_STANDALONE[one];
        i += 1;
        continue;
      }

      // Fallback character
      out += word[i];
      i += 1;
    }
    return out;
  }

  function iastToDevanagari(text) {
    if (!text) return "";
    // Preserve bracketed English apparatus like […6 char illegible…] or [L1]
    return text.replace(/(\[[^\]]*?(?:char|lost|illegible|unknown|Surface|L\d+)[^\]]*?\])|([A-Za-zāīūṛṝḷṃḥṅñṭḍṇśṣĀĪŪṚṜḶṂḤṄÑṬḌṆŚṢ'|]+)/g, (match, bracketed, iastToken) => {
      if (bracketed) return bracketed;
      if (iastToken) return transliterateWordToDeva(iastToken);
      return match;
    });
  }

  function escapeHtml(str) {
    if (str === null || str === undefined) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function formatCrossRefsHtml(str) {
    const esc = escapeHtml(str);
    return esc.replace(/%?(IN\d{5})/g, (m, id) => {
      if (INSCRIPTION_BY_ID.has(id)) {
        return `<span class="xref-link" data-xref="${id}" title="Open ${id}">${id}</span>`;
      }
      return id;
    });
  }

  // ========================================================================
  // 2. FILTERING, SORTING & EXPLORER RENDERING
  // ========================================================================
  function getFilteredInscriptions() {
    const qNorm = normalizeForSearch(state.searchQuery.trim());

    const filtered = INSCRIPTIONS.filter((item) => {
      if (state.onlyBookmarked && !state.bookmarks.has(item.id)) return false;
      if (state.selectedDynasty !== "ALL" && item.dynasty !== state.selectedDynasty) return false;
      if (state.selectedObjectCat !== "ALL" && item.object_category !== state.selectedObjectCat) return false;
      if (state.selectedMaterialCat !== "ALL" && item.material_category !== state.selectedMaterialCat) return false;
      if (state.selectedMetre !== "ALL" && !(item.metres || []).includes(state.selectedMetre)) return false;
      if (qNorm && !item._searchNorm.includes(qNorm)) return false;
      return true;
    });

    filtered.sort((a, b) => {
      switch (state.sortBy) {
        case "id_desc":
          return b.id.localeCompare(a.id);
        case "title_asc":
          return a.title.localeCompare(b.title);
        case "lines_desc":
          return b.line_count - a.line_count;
        case "verses_desc":
          return b.verse_count - a.verse_count;
        case "dynasty":
          return a.dynasty.localeCompare(b.dynasty) || a.id.localeCompare(b.id);
        case "id_asc":
        default:
          return a.id.localeCompare(b.id);
      }
    });

    return filtered;
  }

  function initFilterControls() {
    // Populate Dynasty Pills
    const dynastyCounts = new Map();
    const objCatCounts = new Map();
    const matCatCounts = new Map();
    const metreCounts = new Map();

    INSCRIPTIONS.forEach((it) => {
      dynastyCounts.set(it.dynasty, {
        count: (dynastyCounts.get(it.dynasty)?.count || 0) + 1,
        color: it.dynasty_color,
      });
      objCatCounts.set(it.object_category, (objCatCounts.get(it.object_category) || 0) + 1);
      matCatCounts.set(it.material_category, (matCatCounts.get(it.material_category) || 0) + 1);
      (it.metres || []).forEach((m) => {
        metreCounts.set(m, (metreCounts.get(m) || 0) + 1);
      });
    });

    const pillsContainer = document.getElementById("dynastyPills");
    if (pillsContainer) {
      let pillsHtml = `
        <button class="dynasty-pill active" data-dynasty="ALL">
          <span class="dot" style="background: #f59e0b"></span>
          All Dynasties &amp; Polities
          <span class="count">${INSCRIPTIONS.length}</span>
        </button>
      `;
      Array.from(dynastyCounts.entries())
        .sort((a, b) => b[1].count - a[1].count)
        .forEach(([dyn, info]) => {
          pillsHtml += `
            <button class="dynasty-pill" data-dynasty="${escapeHtml(dyn)}">
              <span class="dot" style="background: ${info.color}"></span>
              ${escapeHtml(dyn)}
              <span class="count">${info.count}</span>
            </button>
          `;
        });
      pillsContainer.innerHTML = pillsHtml;

      pillsContainer.addEventListener("click", (e) => {
        const btn = e.target.closest(".dynasty-pill");
        if (!btn) return;
        state.selectedDynasty = btn.dataset.dynasty;
        state.currentPage = 1;
        syncDynastyPillUI();
        renderExplorer();
      });
    }

    // Populate Dropdown Selects
    const objSelect = document.getElementById("filterObjectCat");
    if (objSelect) {
      Array.from(objCatCounts.entries())
        .sort((a, b) => b[1] - a[1])
        .forEach(([cat, count]) => {
          const opt = document.createElement("option");
          opt.value = cat;
          opt.textContent = `${cat} (${count})`;
          objSelect.appendChild(opt);
        });
    }

    const matSelect = document.getElementById("filterMaterialCat");
    if (matSelect) {
      Array.from(matCatCounts.entries())
        .sort((a, b) => b[1] - a[1])
        .forEach(([cat, count]) => {
          const opt = document.createElement("option");
          opt.value = cat;
          opt.textContent = `${cat} (${count})`;
          matSelect.appendChild(opt);
        });
    }

    const metreSelect = document.getElementById("filterMetre");
    if (metreSelect) {
      Array.from(metreCounts.entries())
        .sort((a, b) => b[1] - a[1])
        .forEach(([m, count]) => {
          const opt = document.createElement("option");
          opt.value = m;
          opt.textContent = `${m} (${count})`;
          metreSelect.appendChild(opt);
        });
    }
  }

  function syncDynastyPillUI() {
    document.querySelectorAll(".dynasty-pill").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.dynasty === state.selectedDynasty);
    });
  }

  function renderExplorer() {
    const filtered = getFilteredInscriptions();
    const total = filtered.length;
    const visible = filtered.slice(0, state.currentPage * state.pageSize);

    const countEl = document.getElementById("resultsCountText");
    if (countEl) {
      countEl.innerHTML = `Showing <strong>${visible.length}</strong> of <strong>${total}</strong> matching inscriptions (Total Archive: ${INSCRIPTIONS.length} XML &amp; PDF records)`;
    }

    const container = document.getElementById("explorerContainer");
    const loadMoreWrap = document.getElementById("loadMoreWrapper");
    if (!container) return;

    if (total === 0) {
      container.innerHTML = `
        <div style="text-align:center; padding: 3.5rem 1.5rem; background: var(--bg-card); border-radius: 16px; border: 1px solid var(--border-subtle);">
          <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🔍</div>
          <h3 style="font-family: var(--font-serif); font-size: 1.5rem; margin-bottom: 0.4rem;">No Matching Inscriptions Found</h3>
          <p style="color: var(--text-muted); margin-bottom: 1rem;">Try clearing one of your active filters or searching without diacritics (e.g. "samudragupta", "sanchi", "copper").</p>
          <button class="btn btn-primary" id="emptyResetBtn">Reset All Filters</button>
        </div>
      `;
      const resetBtn = document.getElementById("emptyResetBtn");
      if (resetBtn) resetBtn.addEventListener("click", resetFilters);
      if (loadMoreWrap) loadMoreWrap.style.display = "none";
      return;
    }

    if (state.viewMode === "grid") {
      container.className = "cards-grid";
      container.innerHTML = visible.map((item) => renderCardHtml(item)).join("");
    } else {
      container.className = "data-table-wrapper";
      container.innerHTML = renderTableHtml(visible);
    }

    if (loadMoreWrap) {
      if (visible.length < total) {
        loadMoreWrap.style.display = "block";
        document.getElementById("loadMoreBtn").textContent = `Show More Inscriptions (${total - visible.length} remaining)`;
      } else {
        loadMoreWrap.style.display = "none";
      }
    }
  }

  function renderCardHtml(item) {
    const isBookmarked = state.bookmarks.has(item.id);
    const snippet = item.full_text
      ? item.full_text.slice(0, 145) + (item.full_text.length > 145 ? "…" : "")
      : "Fragmentary / untranscribed surface.";

    const metrePills = (item.metres || [])
      .slice(0, 3)
      .map((m) => `<span class="mini-pill metre">♫ ${escapeHtml(m)}</span>`)
      .join("");

    return `
      <article class="insc-card" data-id="${escapeHtml(item.id)}">
        <div class="card-ribbon" style="background: ${item.dynasty_color}"></div>
        <div class="card-body">
          <div class="card-top-row">
            <div>
              <span class="id-badge">${escapeHtml(item.id)}</span>
              <span class="obj-badge">• ${escapeHtml(item.object_id)}</span>
            </div>
            <span class="dynasty-tag" style="background: ${item.dynasty_color}">${escapeHtml(item.dynasty)}</span>
          </div>

          <h3 class="card-title" data-action="read" data-id="${escapeHtml(item.id)}">
            ${escapeHtml(item.title)}
          </h3>

          <div class="card-meta-grid">
            <div class="meta-item">
              <span class="meta-label">Ruler / Figure</span>
              <span class="meta-val" title="${escapeHtml(item.ruler)}">${escapeHtml(item.ruler)}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">Provenance / Site</span>
              <span class="meta-val" title="${escapeHtml(item.place_label)}">${escapeHtml(item.place_label)}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">Object &amp; Material</span>
              <span class="meta-val" title="${escapeHtml(item.object_type)} (${escapeHtml(item.material)})">${escapeHtml(item.object_type)} • ${escapeHtml(item.material_category)}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">Dimensions &amp; Scope</span>
              <span class="meta-val">${escapeHtml(item.dimensions)} (${item.line_count}L, ${item.verse_count}V)</span>
            </div>
          </div>

          <div class="card-snippet">${escapeHtml(snippet)}</div>

          <div class="card-tags">
            <span class="mini-pill">🏛️ ${escapeHtml(item.repository.slice(0, 34))}</span>
            ${metrePills}
          </div>
        </div>

        <div class="card-footer">
          <div style="display:flex; gap: 0.4rem; flex-wrap: wrap;">
            <button class="btn btn-primary btn-sm" data-action="read" data-id="${escapeHtml(item.id)}">
              📖 Read &amp; Understand
            </button>
            <a class="btn btn-emerald btn-sm" href="${escapeHtml(item.pdf_file)}" download="${escapeHtml(item.id)}_${escapeHtml(item.title.replace(/[^a-zA-Z0-9]+/g, "_"))}.pdf">
              📥 Download PDF
            </a>
          </div>
          <div style="display:flex; gap: 0.35rem;">
            <a class="btn btn-secondary btn-sm" href="${escapeHtml(item.xml_file)}" target="_blank" title="Open Original TEI XML">
              XML
            </a>
            <button class="btn btn-secondary btn-sm" data-action="bookmark" data-id="${escapeHtml(item.id)}" title="Bookmark Inscription">
              ${isBookmarked ? "★" : "☆"}
            </button>
          </div>
        </div>
      </article>
    `;
  }

  function renderTableHtml(items) {
    const rows = items
      .map(
        (item) => `
      <tr>
        <td>
          <span class="id-badge">${escapeHtml(item.id)}</span>
          <div class="obj-badge" style="margin-top:3px;">${escapeHtml(item.object_id)}</div>
        </td>
        <td>
          <strong style="color:var(--text-primary); cursor:pointer;" data-action="read" data-id="${escapeHtml(item.id)}">${escapeHtml(item.title)}</strong>
          <div style="font-size:0.76rem; color:var(--text-muted);">${escapeHtml(item.ruler)}</div>
        </td>
        <td>
          <span class="dynasty-tag" style="background:${item.dynasty_color}; font-size:0.68rem;">${escapeHtml(item.dynasty)}</span>
          <div style="font-size:0.74rem; color:var(--text-muted); margin-top:3px;">${escapeHtml(item.period)}</div>
        </td>
        <td>
          <div>${escapeHtml(item.object_type)}</div>
          <div style="font-size:0.75rem; color:var(--text-muted);">${escapeHtml(item.material)} (${escapeHtml(item.dimensions)})</div>
        </td>
        <td>
          <div>${escapeHtml(item.place_label)}</div>
          <div style="font-size:0.74rem; color:var(--text-muted);">${escapeHtml(item.repository.slice(0, 38))}</div>
        </td>
        <td>
          <div>${item.line_count} lines</div>
          <div style="font-size:0.74rem; color:var(--text-muted);">${item.verse_count} verses</div>
        </td>
        <td>
          <div style="display:flex; gap:0.35rem;">
            <button class="btn btn-primary btn-sm" data-action="read" data-id="${escapeHtml(item.id)}">📖 Read</button>
            <a class="btn btn-emerald btn-sm" href="${escapeHtml(item.pdf_file)}" download>📥 PDF</a>
            <a class="btn btn-secondary btn-sm" href="${escapeHtml(item.xml_file)}" target="_blank">XML</a>
          </div>
        </td>
      </tr>
    `
      )
      .join("");

    return `
      <table class="epigraphic-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Inscription Title &amp; Ruler</th>
            <th>Dynasty &amp; Period</th>
            <th>Object &amp; Material</th>
            <th>Provenance &amp; Repository</th>
            <th>Scope</th>
            <th>Actions / Downloads</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    `;
  }

  function resetFilters() {
    state.searchQuery = "";
    state.selectedDynasty = "ALL";
    state.selectedObjectCat = "ALL";
    state.selectedMaterialCat = "ALL";
    state.selectedMetre = "ALL";
    state.sortBy = "id_asc";
    state.onlyBookmarked = false;
    state.currentPage = 1;

    document.getElementById("searchInput").value = "";
    document.getElementById("filterObjectCat").value = "ALL";
    document.getElementById("filterMaterialCat").value = "ALL";
    document.getElementById("filterMetre").value = "ALL";
    document.getElementById("sortSelect").value = "id_asc";
    const bmBtn = document.getElementById("bookmarkFilterBtn");
    if (bmBtn) bmBtn.classList.remove("active");

    syncDynastyPillUI();
    renderExplorer();
  }

  // ========================================================================
  // 3. MULTI-MODE INTERACTIVE EPIGRAPHIC READER MODAL
  // ========================================================================
  function openReaderModal(id) {
    const item = INSCRIPTION_BY_ID.get(id);
    if (!item) return;
    state.currentItem = item;

    const modal = document.getElementById("readerModal");
    modal.classList.add("open");
    document.body.style.overflow = "hidden";

    renderReaderModalContent();
  }

  function closeReaderModal() {
    const modal = document.getElementById("readerModal");
    modal.classList.remove("open");
    document.body.style.overflow = "";
    state.currentItem = null;
  }

  function navigateReader(delta) {
    if (!state.currentItem) return;
    const list = getFilteredInscriptions();
    const idx = list.findIndex((x) => x.id === state.currentItem.id);
    if (idx === -1) return;
    const nextIdx = (idx + delta + list.length) % list.length;
    openReaderModal(list[nextIdx].id);
  }

  function renderTokensHtml(tokens) {
    return (tokens || [])
      .map((tok) => {
        switch (tok.type) {
          case "lb":
            return `<span class="dip-line-badge" title="Inscription Line ${escapeHtml(tok.n)}">L${escapeHtml(tok.n)}</span>`;
          case "pb":
            return `<span class="dip-surface-badge">══ Surface / Plate: ${escapeHtml(tok.n)} ══</span>`;
          case "pada_break":
            return ` <span style="color:var(--accent-gold); font-weight:700;">│</span> `;
          case "text":
            return escapeHtml(tok.text);
          case "supplied":
            return `<span class="tok-supplied" title="Restored / Supplied text (Reason: ${escapeHtml(tok.reason)}, Certainty: ${escapeHtml(tok.cert)})">${escapeHtml(tok.text)}</span>`;
          case "unclear":
            return `<span class="tok-unclear" title="Damaged / Unclear reading (Certainty: ${escapeHtml(tok.cert)})">${escapeHtml(tok.text)}</span>`;
          case "gap": {
            const met = tok.met ? ` • Metre: ${escapeHtml(tok.met)}` : "";
            return `<span class="tok-gap" title="Lacuna / Gap (${escapeHtml(tok.reason)}${met})">${escapeHtml(tok.label)}</span>`;
          }
          case "choice_corr":
            return `<span class="tok-corr" title="Editorial Correction — Original scribal reading (sic): ${escapeHtml(tok.sic)}">${escapeHtml(tok.corr)} <small>(sic: ${escapeHtml(tok.sic)})</small></span>`;
          case "add":
          case "del":
          case "surplus":
          case "sic":
          case "num":
          case "symbol":
            return `<span style="color:var(--accent-purple); font-weight:600;">${escapeHtml(tok.text || tok.symbol || "")}</span>`;
          case "space":
            return `&nbsp;&nbsp;&nbsp;`;
          default:
            return "";
        }
      })
      .join("");
  }

  function renderReaderModalContent() {
    const item = state.currentItem;
    if (!item) return;

    // Header
    document.getElementById("modalHeaderTitle").textContent = `${item.id}: ${item.title}`;
    document.getElementById("modalHeaderSub").innerHTML = `
      <span class="dynasty-tag" style="background:${item.dynasty_color}; margin-right:0.5rem;">${escapeHtml(item.dynasty)}</span>
      <span><strong>Ruler:</strong> ${escapeHtml(item.ruler)}</span> &nbsp;•&nbsp;
      <span><strong>Object ID:</strong> ${escapeHtml(item.object_id)}</span> &nbsp;•&nbsp;
      <span><strong>Period:</strong> ${escapeHtml(item.period)}</span> &nbsp;•&nbsp;
      <span><strong>Editor:</strong> ${escapeHtml(item.editor)}</span>
    `;

    // Download links in modal toolbar
    const pdfBtn = document.getElementById("modalDownloadPdfBtn");
    pdfBtn.href = item.pdf_file;
    pdfBtn.setAttribute("download", `${item.id}_${item.title.replace(/[^a-zA-Z0-9]+/g, "_")}.pdf`);

    const xmlBtn = document.getElementById("modalDownloadXmlBtn");
    xmlBtn.href = item.xml_file;

    // Left Sidebar Metadata & Visual Proportions
    const wNum = parseFloat(item.width) || 25;
    const hNum = parseFloat(item.height) || 25;
    const maxDim = Math.max(wNum, hNum, 1);
    const boxW = Math.max(28, Math.round((wNum / maxDim) * 120));
    const boxH = Math.max(28, Math.round((hNum / maxDim) * 120));

    const glossaryHtml =
      item.glossary && item.glossary.length
        ? item.glossary
            .map(
              (g) => `
          <div style="margin-bottom:0.5rem; font-size:0.8rem;">
            <strong style="color:var(--accent-gold-light);">${escapeHtml(g.term)}</strong>:
            <span style="color:var(--text-secondary);">${escapeHtml(g.desc)}</span>
          </div>`
            )
            .join("")
        : `<p style="font-size:0.8rem; color:var(--text-muted);">Standard Sanskrit epigraphic vocabulary.</p>`;

    const crossRefHtml =
      item.cross_refs && item.cross_refs.length
        ? item.cross_refs
            .map((ref) => `<button class="btn btn-secondary btn-sm xref-link" data-xref="${escapeHtml(ref)}">🔗 ${escapeHtml(ref)}</button>`)
            .join(" ")
        : `<span style="font-size:0.8rem; color:var(--text-muted);">None cited</span>`;

    document.getElementById("modalMetaColumn").innerHTML = `
      <div class="meta-box">
        <h4>🏛️ Custody &amp; Provenance</h4>
        <div style="font-size:0.83rem; display:flex; flex-direction:column; gap:0.45rem;">
          <div><strong>Repository:</strong> ${formatCrossRefsHtml(item.repository)}</div>
          <div><strong>Origin / Findspot:</strong> ${escapeHtml(item.place_label)} (${escapeHtml(item.orig_place_raw)})</div>
          <div><strong>Provenance Notes:</strong> ${formatCrossRefsHtml(item.provenance)}</div>
        </div>
      </div>

      <div class="meta-box">
        <h4>📐 Physical Support &amp; Scale</h4>
        <div style="display:flex; align-items:center; gap:1rem; margin-bottom:0.75rem;">
          <div style="width:130px; height:130px; background:var(--bg-secondary); border-radius:10px; display:flex; align-items:center; justify-content:center; border:1px dashed var(--border-subtle); flex-shrink:0;">
            <div style="width:${boxW}px; height:${boxH}px; background:linear-gradient(135deg, ${item.dynasty_color}, #f59e0b); border-radius:4px; display:flex; align-items:center; justify-content:center; color:#fff; font-size:0.68rem; font-weight:700; text-align:center; padding:2px; box-shadow:0 4px 12px rgba(0,0,0,0.4);">
              ${escapeHtml(item.dimensions)}
            </div>
          </div>
          <div style="font-size:0.8rem; display:flex; flex-direction:column; gap:0.3rem;">
            <div><strong>Material:</strong> ${escapeHtml(item.material)}</div>
            <div><strong>Object Type:</strong> ${escapeHtml(item.object_type)}</div>
            <div><strong>Dimensions:</strong> ${escapeHtml(item.dimensions)}</div>
            <div><strong>Layout Area:</strong> ${escapeHtml(item.layout_dimensions)}</div>
            <div><strong>Char Height:</strong> ${escapeHtml(item.char_height)}</div>
          </div>
        </div>
        <div style="font-size:0.81rem; color:var(--text-secondary);">
          <p style="margin-bottom:0.4rem;"><strong>Support:</strong> ${formatCrossRefsHtml(item.support_desc)}</p>
          <p style="margin-bottom:0.4rem;"><strong>Layout:</strong> ${formatCrossRefsHtml(item.layout_desc)}</p>
          <p style="margin-bottom:0.4rem;"><strong>Script:</strong> ${formatCrossRefsHtml(item.script_desc)}</p>
          <p><strong>Decoration:</strong> ${formatCrossRefsHtml(item.deco_desc)}</p>
        </div>
      </div>

      <div class="meta-box">
        <h4>📘 Key Sanskrit Terms Detected</h4>
        ${glossaryHtml}
      </div>

      <div class="meta-box">
        <h4>🔗 Related Inscriptions</h4>
        <div style="display:flex; flex-wrap:wrap; gap:0.4rem;">${crossRefHtml}</div>
      </div>
    `;

    renderReaderEditionBlocks();
  }

  function renderReaderEditionBlocks() {
    const item = state.currentItem;
    if (!item) return;

    const editionCol = document.getElementById("modalEditionColumn");
    let blocks = item.blocks || [];
    if (state.editionMode === "verses") {
      blocks = blocks.filter((b) => b.kind === "verse");
    }

    const blocksHtml =
      blocks.length === 0
        ? `<div class="edition-block"><em>No matching text blocks in this mode. Switch to "Smooth Edition" or "Critical Diplomatic" to view all lines.</em></div>`
        : blocks
            .map((b, idx) => {
              const secBanner = b.section
                ? `<div style="font-size:0.76rem; text-transform:uppercase; letter-spacing:0.07em; color:var(--accent-gold); margin-bottom:0.35rem; font-weight:700;">Part: ${escapeHtml(b.section)}</div>`
                : "";

              if (state.editionMode === "diplomatic") {
                const dipHtml = renderTokensHtml(b.tokens);
                const vBadge =
                  b.kind === "verse"
                    ? `<div class="verse-header-bar">
                        <span class="verse-badge">Verse ${escapeHtml(b.n || idx + 1)} • Metre: ${escapeHtml(b.met)}</span>
                        <span style="font-size:0.75rem; color:var(--text-muted);">${escapeHtml(b.met_desc || "")}</span>
                      </div>`
                    : "";
                const devaLine =
                  state.scriptMode !== "iast"
                    ? `<div class="sanskrit-deva">${escapeHtml(
                        iastToDevanagari(
                          b.kind === "verse" ? b.padas.map((p) => p.smooth).join(" । ") : b.smooth
                        )
                      )}</div>`
                    : "";
                return `
                  <div class="edition-block">
                    ${secBanner}
                    ${vBadge}
                    <div class="sanskrit-smooth" style="font-size:1.05rem;">${dipHtml}</div>
                    ${devaLine}
                  </div>
                `;
              }

              // Smooth or Verses Mode
              if (b.kind === "verse") {
                const iastLines = b.padas
                  .filter((p) => p.smooth)
                  .map((p) => `<div>${escapeHtml(p.smooth)}</div>`)
                  .join("");
                const devaLines = b.padas
                  .filter((p) => p.smooth)
                  .map((p) => `<div>${escapeHtml(iastToDevanagari(p.smooth))}</div>`)
                  .join("");

                return `
                  <div class="edition-block">
                    ${secBanner}
                    <div class="verse-header-bar">
                      <span class="verse-badge">♫ Verse ${escapeHtml(b.n || idx + 1)} — ${escapeHtml(b.met)}</span>
                      <span style="font-size:0.75rem; color:var(--text-muted);">${escapeHtml(b.met_desc || "")}</span>
                    </div>
                    ${state.scriptMode !== "deva" ? `<div class="sanskrit-smooth">${iastLines}</div>` : ""}
                    ${state.scriptMode !== "iast" ? `<div class="sanskrit-deva">${devaLines}</div>` : ""}
                  </div>
                `;
              } else {
                return `
                  <div class="edition-block">
                    ${secBanner}
                    <div style="font-size:0.73rem; text-transform:uppercase; color:var(--text-muted); margin-bottom:0.3rem; font-weight:700;">Prose Passage</div>
                    ${state.scriptMode !== "deva" ? `<div class="sanskrit-smooth">${escapeHtml(b.smooth)}</div>` : ""}
                    ${state.scriptMode !== "iast" ? `<div class="sanskrit-deva">${escapeHtml(iastToDevanagari(b.smooth))}</div>` : ""}
                  </div>
                `;
              }
            })
            .join("");

    editionCol.innerHTML = `
      <div class="summary-callout">
        <strong>💡 Easy-Reading Executive Summary:</strong> ${escapeHtml(item.summary)}
      </div>

      <div class="legend-strip">
        <span><strong>Notation Key:</strong></span>
        <span><span class="tok-supplied">[abc]</span> Restored text</span>
        <span><span class="tok-unclear">abc</span> Unclear / damaged</span>
        <span><span class="tok-gap">[…gap…]</span> Illegible / lost</span>
        <span><span class="dip-line-badge">L1</span> Inscription Line</span>
        <span><span class="tok-corr">corr (sic)</span> Scribal correction</span>
      </div>

      ${blocksHtml}
    `;
  }

  // ========================================================================
  // 4. INTERACTIVE SOUTH ASIA EPIGRAPHIC MAP (LEAFLET.JS — ZERO API KEY)
  // ========================================================================
  function createOfflineVectorLayer() {
    const group = L.layerGroup();
    // Simplified South Asian Subcontinent Polygon (works 100% offline)
    const subcontinentOutline = [
      [37.0, 68.0], [36.5, 71.5], [35.5, 74.5], [34.5, 78.5], [31.0, 81.0],
      [29.5, 84.0], [28.0, 88.5], [27.5, 92.0], [27.8, 96.5], [24.0, 95.0],
      [21.5, 92.5], [22.0, 89.0], [21.5, 87.0], [19.8, 85.8], [17.7, 83.3],
      [15.9, 80.5], [13.1, 80.3], [10.3, 79.8], [8.08, 77.55], [9.9, 76.2],
      [12.9, 74.8], [15.4, 73.8], [19.0, 72.8], [21.5, 72.6], [20.7, 70.4],
      [22.3, 69.0], [23.8, 68.2], [24.8, 67.0], [25.2, 62.5], [29.0, 66.0],
      [33.5, 68.5], [37.0, 68.0]
    ];
    const sriLankaOutline = [
      [9.8, 80.2], [8.6, 81.2], [6.8, 81.8], [5.9, 80.5], [6.9, 79.8], [8.5, 79.9], [9.8, 80.2]
    ];
    L.polygon(subcontinentOutline, {
      color: "#f59e0b",
      weight: 2,
      fillColor: "#1e293b",
      fillOpacity: 0.85,
    }).addTo(group);
    L.polygon(sriLankaOutline, {
      color: "#f59e0b",
      weight: 1.5,
      fillColor: "#1e293b",
      fillOpacity: 0.85,
    }).addTo(group);
    return group;
  }

  function createAncientRiversOverlay() {
    const rivers = L.layerGroup();
    const riverStyle = { color: "#38bdf8", weight: 2.2, opacity: 0.72, dashArray: "4, 4" };

    // Ganga (Ganges)
    L.polyline([[30.9, 79.1], [29.9, 78.2], [26.4, 80.3], [25.4, 81.8], [25.3, 83.0], [25.6, 85.1], [25.0, 87.9], [23.8, 89.8], [22.3, 90.6]], riverStyle)
      .bindTooltip("Gaṅgā River", { sticky: true }).addTo(rivers);
    // Yamuna
    L.polyline([[31.0, 78.4], [28.6, 77.2], [27.5, 77.7], [27.2, 78.0], [25.4, 81.8]], riverStyle)
      .bindTooltip("Yamunā River", { sticky: true }).addTo(rivers);
    // Sindhu (Indus)
    L.polyline([[34.2, 77.5], [35.5, 74.6], [32.9, 71.5], [29.0, 70.5], [25.4, 68.3], [24.0, 67.5]], riverStyle)
      .bindTooltip("Sindhu (Indus) River", { sticky: true }).addTo(rivers);
    // Narmada
    L.polyline([[22.7, 81.7], [23.1, 79.9], [22.5, 76.9], [21.7, 73.0]], riverStyle)
      .bindTooltip("Narmadā River", { sticky: true }).addTo(rivers);
    // Godavari
    L.polyline([[19.9, 73.5], [19.1, 77.3], [18.7, 79.9], [16.7, 82.2]], riverStyle)
      .bindTooltip("Godāvarī River", { sticky: true }).addTo(rivers);

    return rivers;
  }

  function initOrUpdateMap() {
    const mapEl = document.getElementById("epigraphicMap");
    if (!mapEl || typeof L === "undefined") return;

    if (!state.map) {
      state.map = L.map("epigraphicMap", {
        center: [24.2, 80.5],
        zoom: 5,
        scrollWheelZoom: true,
      });

      // Zero-API-Key Public Tile Layers (work seamlessly on file:// and http://)
      const esriTopo = L.tileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
        {
          attribution: "Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ, TomTom, Intermap, iPC, USGS, FAO, NPS, NRCAN, GeoBase",
          maxZoom: 18,
        }
      );

      const esriStreet = L.tileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
        {
          attribution: "Tiles &copy; Esri &mdash; Source: Esri, DeLorme, NAVTEQ, USGS, Intermap, iPC",
          maxZoom: 18,
        }
      );

      const esriSatellite = L.tileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        {
          attribution: "Tiles &copy; Esri &mdash; Source: Esri, Maxar, Earthstar Geographics, and the GIS User Community",
          maxZoom: 18,
        }
      );

      const esriRelief = L.tileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Shaded_Relief/MapServer/tile/{z}/{y}/{x}",
        {
          attribution: "Tiles &copy; Esri &mdash; Source: Esri",
          maxZoom: 13,
        }
      );

      const offlineVector = createOfflineVectorLayer();
      const ancientRivers = createAncientRiversOverlay();

      // Add default no-key Esri Topographic layer + Ancient Rivers overlay
      esriTopo.addTo(state.map);
      ancientRivers.addTo(state.map);

      // Add Interactive Layer Switcher in top-right corner of map
      L.control
        .layers(
          {
            "🗺️ Heritage Topographic (No API Key)": esriTopo,
            "🏛️ Street & Sites Map (No API Key)": esriStreet,
            "🛰️ Satellite Terrain (No API Key)": esriSatellite,
            "⛰️ Physical Shaded Relief (No API Key)": esriRelief,
            "🧭 Built-in Offline Vector Basemap": offlineVector,
          },
          {
            "🌊 Ancient Sacred Rivers (Gaṅgā, Yamunā, Sindhu, Narmadā)": ancientRivers,
          },
          { collapsed: true }
        )
        .addTo(state.map);
    }

    setTimeout(() => {
      state.map.invalidateSize();
    }, 150);

    // Group inscriptions by coordinate site
    const siteGroups = new Map();
    INSCRIPTIONS.forEach((item) => {
      if (item.lat === null || item.lon === null) return;
      const key = `${item.lat.toFixed(3)},${item.lon.toFixed(3)}`;
      if (!siteGroups.has(key)) {
        siteGroups.set(key, {
          lat: item.lat,
          lon: item.lon,
          label: item.place_label,
          color: item.dynasty_color,
          items: [],
        });
      }
      siteGroups.get(key).items.push(item);
    });

    // Clear existing markers
    state.mapMarkers.forEach((m) => state.map.removeLayer(m));
    state.mapMarkers = [];

    const sitesArray = Array.from(siteGroups.values()).sort((a, b) => b.items.length - a.items.length);

    sitesArray.forEach((site) => {
      const radius = Math.min(20, 7 + Math.sqrt(site.items.length) * 3);
      const marker = L.circleMarker([site.lat, site.lon], {
        radius,
        fillColor: site.color,
        color: "#ffffff",
        weight: 2,
        opacity: 1,
        fillOpacity: 0.88,
      }).addTo(state.map);

      const listHtml = site.items
        .slice(0, 8)
        .map(
          (it) => `
          <div style="padding:4px 0; border-bottom:1px solid #e2e8f0; display:flex; justify-content:space-between; align-items:center; gap:8px;">
            <div>
              <strong>${escapeHtml(it.id)}</strong>: ${escapeHtml(it.title)}
            </div>
            <div style="white-space:nowrap;">
              <a href="${escapeHtml(it.pdf_file)}" download style="color:#059669; font-weight:700; text-decoration:none; margin-right:6px;">PDF</a>
              <a href="#" data-action="read" data-id="${escapeHtml(it.id)}" style="color:#ea580c; font-weight:700; text-decoration:none;">Read</a>
            </div>
          </div>`
        )
        .join("");

      const moreNote =
        site.items.length > 8 ? `<div style="font-size:11px; color:#64748b; margin-top:4px;">+ ${site.items.length - 8} more inscriptions at this site</div>` : "";

      marker.bindPopup(`
        <div style="min-width:260px; font-family: system-ui, sans-serif; color:#0f172a;">
          <h4 style="margin:0 0 4px; font-size:14px; color:#1e1b4b;">📍 ${escapeHtml(site.label)}</h4>
          <div style="font-size:12px; color:#475569; margin-bottom:6px;"><strong>${site.items.length}</strong> Inscription(s) Recorded (${site.lat.toFixed(2)}°N, ${site.lon.toFixed(2)}°E)</div>
          <div style="max-height:190px; overflow-y:auto; font-size:12px;">${listHtml}</div>
          ${moreNote}
        </div>
      `);

      state.mapMarkers.push(marker);
    });

    // Populate Sidebar List
    const siteListEl = document.getElementById("mapSiteList");
    if (siteListEl) {
      siteListEl.innerHTML = sitesArray
        .map(
          (site) => `
        <div class="map-site-item" data-lat="${site.lat}" data-lon="${site.lon}">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <strong style="font-size:0.86rem; color:var(--text-primary);">📍 ${escapeHtml(site.label)}</strong>
            <span class="id-badge">${site.items.length}</span>
          </div>
          <div style="font-size:0.75rem; color:var(--text-muted); margin-top:0.2rem;">
            ${escapeHtml(site.items.map((x) => x.id).slice(0, 5).join(", "))}${site.items.length > 5 ? "…" : ""}
          </div>
        </div>
      `
        )
        .join("");
    }
  }

  // ========================================================================
  // 5. VISUAL ANALYTICS & CHARTS
  // ========================================================================
  function renderAnalytics() {
    const dynMap = new Map();
    const objMap = new Map();
    const matMap = new Map();
    const metMap = new Map();

    INSCRIPTIONS.forEach((it) => {
      dynMap.set(it.dynasty, {
        count: (dynMap.get(it.dynasty)?.count || 0) + 1,
        color: it.dynasty_color,
      });
      objMap.set(it.object_category, (objMap.get(it.object_category) || 0) + 1);
      matMap.set(it.material_category, (matMap.get(it.material_category) || 0) + 1);
      (it.metres || []).forEach((m) => metMap.set(m, (metMap.get(m) || 0) + 1));
    });

    const dynContainer = document.getElementById("chartDynasties");
    if (dynContainer) {
      const max = Math.max(...Array.from(dynMap.values()).map((x) => x.count), 1);
      dynContainer.innerHTML = Array.from(dynMap.entries())
        .sort((a, b) => b[1].count - a[1].count)
        .map(
          ([name, info]) => `
          <div class="bar-row" data-filter-dynasty="${escapeHtml(name)}">
            <div class="bar-label-line">
              <span>${escapeHtml(name)}</span>
              <span>${info.count} inscriptions (${Math.round((info.count / INSCRIPTIONS.length) * 100)}%)</span>
            </div>
            <div class="bar-track">
              <div class="bar-fill" style="width:${(info.count / max) * 100}%; background:${info.color};"></div>
            </div>
          </div>`
        )
        .join("");
    }

    const objContainer = document.getElementById("chartObjects");
    if (objContainer) {
      const max = Math.max(...Array.from(objMap.values()), 1);
      const palette = ["#f59e0b", "#10b981", "#8b5cf6", "#0ea5e9", "#ec4899", "#eab308", "#ef4444"];
      objContainer.innerHTML = Array.from(objMap.entries())
        .sort((a, b) => b[1] - a[1])
        .map(
          ([name, count], idx) => `
          <div class="bar-row" data-filter-obj="${escapeHtml(name)}">
            <div class="bar-label-line">
              <span>${escapeHtml(name)}</span>
              <span>${count} records</span>
            </div>
            <div class="bar-track">
              <div class="bar-fill" style="width:${(count / max) * 100}%; background:${palette[idx % palette.length]};"></div>
            </div>
          </div>`
        )
        .join("");
    }

    const matContainer = document.getElementById("chartMaterials");
    if (matContainer) {
      const max = Math.max(...Array.from(matMap.values()), 1);
      const palette = ["#ea580c", "#d97706", "#14b8a6", "#6366f1", "#f43f5e"];
      matContainer.innerHTML = Array.from(matMap.entries())
        .sort((a, b) => b[1] - a[1])
        .map(
          ([name, count], idx) => `
          <div class="bar-row" data-filter-mat="${escapeHtml(name)}">
            <div class="bar-label-line">
              <span>${escapeHtml(name)}</span>
              <span>${count} artifacts</span>
            </div>
            <div class="bar-track">
              <div class="bar-fill" style="width:${(count / max) * 100}%; background:${palette[idx % palette.length]};"></div>
            </div>
          </div>`
        )
        .join("");
    }

    const metContainer = document.getElementById("chartMetres");
    if (metContainer) {
      const topMetres = Array.from(metMap.entries())
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10);
      const max = Math.max(...topMetres.map((x) => x[1]), 1);
      metContainer.innerHTML = topMetres
        .map(
          ([name, count]) => `
          <div class="bar-row" data-filter-metre="${escapeHtml(name)}">
            <div class="bar-label-line">
              <span>♫ ${escapeHtml(name)}</span>
              <span>${count} inscriptions</span>
            </div>
            <div class="bar-track">
              <div class="bar-fill" style="width:${(count / max) * 100}%; background:linear-gradient(90deg, #8b5cf6, #ec4899);"></div>
            </div>
          </div>`
        )
        .join("");
    }
  }

  // ========================================================================
  // 6. SIDE-BY-SIDE INSCRIPTION COMPARATOR
  // ========================================================================
  function initComparator() {
    const selLeft = document.getElementById("compareSelectLeft");
    const selRight = document.getElementById("compareSelectRight");
    if (!selLeft || !selRight) return;

    const optsHtml = INSCRIPTIONS.map(
      (it) => `<option value="${escapeHtml(it.id)}">${escapeHtml(it.id)} — ${escapeHtml(it.title)}</option>`
    ).join("");
    selLeft.innerHTML = optsHtml;
    selRight.innerHTML = optsHtml;

    selLeft.value = state.compareLeftId;
    selRight.value = state.compareRightId;

    selLeft.addEventListener("change", () => {
      state.compareLeftId = selLeft.value;
      renderComparisonPanes();
    });
    selRight.addEventListener("change", () => {
      state.compareRightId = selRight.value;
      renderComparisonPanes();
    });

    renderComparisonPanes();
  }

  function renderComparisonPanes() {
    renderSingleComparePane("comparePaneLeft", state.compareLeftId);
    renderSingleComparePane("comparePaneRight", state.compareRightId);
  }

  function renderSingleComparePane(containerId, inscId) {
    const el = document.getElementById(containerId);
    const item = INSCRIPTION_BY_ID.get(inscId);
    if (!el || !item) return;

    el.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:0.5rem; margin-bottom:0.75rem;">
        <div>
          <span class="id-badge">${escapeHtml(item.id)}</span>
          <span class="dynasty-tag" style="background:${item.dynasty_color}; margin-left:0.4rem;">${escapeHtml(item.dynasty)}</span>
          <h3 style="font-family:var(--font-serif); font-size:1.35rem; margin-top:0.4rem;">${escapeHtml(item.title)}</h3>
        </div>
        <div style="display:flex; gap:0.4rem;">
          <a class="btn btn-emerald btn-sm" href="${escapeHtml(item.pdf_file)}" download>📥 PDF</a>
          <button class="btn btn-primary btn-sm" data-action="read" data-id="${escapeHtml(item.id)}">📖 Full Reader</button>
        </div>
      </div>

      <div class="card-meta-grid" style="margin-bottom:0.9rem;">
        <div class="meta-item"><span class="meta-label">Ruler</span><span class="meta-val">${escapeHtml(item.ruler)}</span></div>
        <div class="meta-item"><span class="meta-label">Origin</span><span class="meta-val">${escapeHtml(item.place_label)}</span></div>
        <div class="meta-item"><span class="meta-label">Material &amp; Object</span><span class="meta-val">${escapeHtml(item.material)} (${escapeHtml(item.object_type)})</span></div>
        <div class="meta-item"><span class="meta-label">Dimensions &amp; Scope</span><span class="meta-val">${escapeHtml(item.dimensions)} • ${item.line_count}L / ${item.verse_count}V</span></div>
        <div class="meta-item"><span class="meta-label">Repository</span><span class="meta-val">${escapeHtml(item.repository)}</span></div>
        <div class="meta-item"><span class="meta-label">Metres</span><span class="meta-val">${escapeHtml((item.metres || []).join(", ") || "Prose")}</span></div>
      </div>

      <div style="font-size:0.84rem; color:var(--text-secondary); margin-bottom:0.85rem;">
        <strong>Summary:</strong> ${escapeHtml(item.summary)}
      </div>

      <div style="max-height:420px; overflow-y:auto; padding:0.9rem; background:var(--bg-secondary); border-radius:12px; border:1px solid var(--border-subtle);">
        <div style="font-size:0.75rem; text-transform:uppercase; color:var(--accent-gold-light); font-weight:700; margin-bottom:0.4rem;">Sanskrit Edition Text (IAST + Devanagari)</div>
        <div class="sanskrit-smooth" style="font-size:0.98rem; white-space:pre-line;">${escapeHtml(item.full_text)}</div>
        <hr style="border:none; border-top:1px dashed var(--border-subtle); margin:0.75rem 0;" />
        <div class="sanskrit-deva" style="font-size:0.95rem; white-space:pre-line;">${escapeHtml(iastToDevanagari(item.full_text))}</div>
      </div>
    `;
  }

  // ========================================================================
  // 7. SANSKRIT GLOSSARY & READING GUIDE TAB
  // ========================================================================
  function renderGlossaryTab() {
    const gContainer = document.getElementById("glossaryCardsContainer");
    if (gContainer && ARCHIVE.glossary) {
      gContainer.innerHTML = ARCHIVE.glossary
        .map((g) => {
          const matchCount = INSCRIPTIONS.filter((it) => it._searchNorm.includes(normalizeForSearch(g.key))).length;
          return `
            <div class="glossary-card" data-glossary-search="${escapeHtml(g.key)}">
              <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.4rem;">
                <h4 style="font-family:var(--font-serif); font-size:1.22rem; color:var(--accent-gold-light);">${escapeHtml(g.term)}</h4>
                <span class="id-badge">${matchCount} records</span>
              </div>
              <div style="font-family:var(--font-deva); font-size:0.95rem; color:var(--text-secondary); margin-bottom:0.35rem;">
                ${escapeHtml(transliterateWordToDeva(g.key))}
              </div>
              <p style="font-size:0.84rem; color:var(--text-secondary);">${escapeHtml(g.desc)}</p>
              <div style="margin-top:0.6rem; font-size:0.76rem; color:var(--accent-gold); font-weight:600;">
                Click to view all ${matchCount} inscriptions with this term →
              </div>
            </div>
          `;
        })
        .join("");
    }

    const mContainer = document.getElementById("metreGuideContainer");
    if (mContainer && ARCHIVE.metre_guide) {
      mContainer.innerHTML = Object.entries(ARCHIVE.metre_guide)
        .map(
          ([k, desc]) => `
          <div class="glossary-card" data-metre-select="${escapeHtml(k)}">
            <h4 style="font-family:var(--font-serif); font-size:1.18rem; color:#c4b5fd; margin-bottom:0.35rem;">♫ ${escapeHtml(k)}</h4>
            <p style="font-size:0.84rem; color:var(--text-secondary);">${escapeHtml(desc)}</p>
          </div>`
        )
        .join("");
    }
  }

  // ========================================================================
  // 8. TAB SWITCHING & GLOBAL EVENT LISTENERS
  // ========================================================================
  function switchTab(tabName) {
    state.activeTab = tabName;
    document.querySelectorAll(".nav-tab").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.tab === tabName);
    });
    document.querySelectorAll(".tab-panel").forEach((panel) => {
      panel.classList.toggle("active", panel.id === `tab-${tabName}`);
    });

    if (tabName === "map") {
      initOrUpdateMap();
    } else if (tabName === "analytics") {
      renderAnalytics();
    }
  }

  function exportFilteredCsv() {
    const rows = getFilteredInscriptions();
    const headers = ["ID", "Object_ID", "Title", "Ruler", "Dynasty", "Period", "Material", "Object_Type", "Dimensions", "Origin", "Repository", "Lines", "Verses", "PDF_File"];
    const csvLines = [
      headers.join(","),
      ...rows.map((r) =>
        [
          r.id,
          r.object_id,
          `"${(r.title || "").replace(/"/g, '""')}"`,
          `"${(r.ruler || "").replace(/"/g, '""')}"`,
          `"${(r.dynasty || "").replace(/"/g, '""')}"`,
          `"${(r.period || "").replace(/"/g, '""')}"`,
          `"${(r.material || "").replace(/"/g, '""')}"`,
          `"${(r.object_type || "").replace(/"/g, '""')}"`,
          `"${(r.dimensions || "").replace(/"/g, '""')}"`,
          `"${(r.place_label || "").replace(/"/g, '""')}"`,
          `"${(r.repository || "").replace(/"/g, '""')}"`,
          r.line_count,
          r.verse_count,
          r.pdf_file,
        ].join(",")
      ),
    ];

    const blob = new Blob(["\uFEFF" + csvLines.join("\n")], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "Siddham_Filtered_Inscriptions_Catalogue.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  function bindEvents() {
    // Nav Tabs
    document.querySelectorAll(".nav-tab").forEach((btn) => {
      btn.addEventListener("click", () => switchTab(btn.dataset.tab));
    });

    // Hero Quick Action Buttons
    document.querySelectorAll("[data-goto-tab]").forEach((btn) => {
      btn.addEventListener("click", () => switchTab(btn.dataset.gotoTab));
    });

    // Random Inscription Spotlight
    const randomBtn = document.getElementById("randomSpotlightBtn");
    if (randomBtn) {
      randomBtn.addEventListener("click", () => {
        const rand = INSCRIPTIONS[Math.floor(Math.random() * INSCRIPTIONS.length)];
        if (rand) openReaderModal(rand.id);
      });
    }

    // Theme Toggle
    const themeBtn = document.getElementById("themeToggleBtn");
    if (themeBtn) {
      themeBtn.addEventListener("click", () => {
        const isLight = document.documentElement.getAttribute("data-theme") === "light";
        if (isLight) {
          document.documentElement.removeAttribute("data-theme");
          themeBtn.textContent = "☀️ Sandstone Light";
        } else {
          document.documentElement.setAttribute("data-theme", "light");
          themeBtn.textContent = "🌙 Royal Dark";
        }
      });
    }

    // Search & Filters
    const searchInput = document.getElementById("searchInput");
    if (searchInput) {
      searchInput.addEventListener("input", () => {
        state.searchQuery = searchInput.value;
        state.currentPage = 1;
        renderExplorer();
      });
    }

    document.getElementById("filterObjectCat")?.addEventListener("change", (e) => {
      state.selectedObjectCat = e.target.value;
      state.currentPage = 1;
      renderExplorer();
    });
    document.getElementById("filterMaterialCat")?.addEventListener("change", (e) => {
      state.selectedMaterialCat = e.target.value;
      state.currentPage = 1;
      renderExplorer();
    });
    document.getElementById("filterMetre")?.addEventListener("change", (e) => {
      state.selectedMetre = e.target.value;
      state.currentPage = 1;
      renderExplorer();
    });
    document.getElementById("sortSelect")?.addEventListener("change", (e) => {
      state.sortBy = e.target.value;
      renderExplorer();
    });
    document.getElementById("resetFiltersBtn")?.addEventListener("click", resetFilters);

    // View Toggles (Grid / Table / Bookmarks / Export CSV)
    document.getElementById("viewGridBtn")?.addEventListener("click", () => {
      state.viewMode = "grid";
      document.getElementById("viewGridBtn").classList.add("active");
      document.getElementById("viewTableBtn").classList.remove("active");
      renderExplorer();
    });
    document.getElementById("viewTableBtn")?.addEventListener("click", () => {
      state.viewMode = "table";
      document.getElementById("viewTableBtn").classList.add("active");
      document.getElementById("viewGridBtn").classList.remove("active");
      renderExplorer();
    });
    document.getElementById("bookmarkFilterBtn")?.addEventListener("click", (e) => {
      state.onlyBookmarked = !state.onlyBookmarked;
      e.currentTarget.classList.toggle("active", state.onlyBookmarked);
      state.currentPage = 1;
      renderExplorer();
    });
    document.getElementById("exportCsvBtn")?.addEventListener("click", exportFilteredCsv);

    // Load More
    document.getElementById("loadMoreBtn")?.addEventListener("click", () => {
      state.currentPage += 1;
      renderExplorer();
    });

    // Delegated Clicks (Cards, Read, Bookmark, Cross-refs, Analytics bars, Glossary cards)
    document.addEventListener("click", (e) => {
      const readEl = e.target.closest("[data-action='read']");
      if (readEl) {
        e.preventDefault();
        openReaderModal(readEl.dataset.id);
        return;
      }

      const bmEl = e.target.closest("[data-action='bookmark']");
      if (bmEl) {
        const id = bmEl.dataset.id;
        if (state.bookmarks.has(id)) {
          state.bookmarks.delete(id);
        } else {
          state.bookmarks.add(id);
        }
        localStorage.setItem("siddham_bookmarks", JSON.stringify(Array.from(state.bookmarks)));
        renderExplorer();
        return;
      }

      const xrefEl = e.target.closest("[data-xref]");
      if (xrefEl) {
        openReaderModal(xrefEl.dataset.xref);
        return;
      }

      const siteEl = e.target.closest(".map-site-item");
      if (siteEl && state.map) {
        const lat = parseFloat(siteEl.dataset.lat);
        const lon = parseFloat(siteEl.dataset.lon);
        state.map.flyTo([lat, lon], 8, { duration: 0.8 });
        return;
      }

      const barDyn = e.target.closest("[data-filter-dynasty]");
      if (barDyn) {
        state.selectedDynasty = barDyn.dataset.filterDynasty;
        syncDynastyPillUI();
        switchTab("explorer");
        renderExplorer();
        return;
      }

      const barObj = e.target.closest("[data-filter-obj]");
      if (barObj) {
        state.selectedObjectCat = barObj.dataset.filterObj;
        document.getElementById("filterObjectCat").value = state.selectedObjectCat;
        switchTab("explorer");
        renderExplorer();
        return;
      }

      const barMat = e.target.closest("[data-filter-mat]");
      if (barMat) {
        state.selectedMaterialCat = barMat.dataset.filterMat;
        document.getElementById("filterMaterialCat").value = state.selectedMaterialCat;
        switchTab("explorer");
        renderExplorer();
        return;
      }

      const barMet = e.target.closest("[data-filter-metre]");
      if (barMet) {
        state.selectedMetre = barMet.dataset.filterMetre;
        document.getElementById("filterMetre").value = state.selectedMetre;
        switchTab("explorer");
        renderExplorer();
        return;
      }

      const glCard = e.target.closest("[data-glossary-search]");
      if (glCard) {
        resetFilters();
        state.searchQuery = glCard.dataset.glossarySearch;
        document.getElementById("searchInput").value = state.searchQuery;
        switchTab("explorer");
        renderExplorer();
        return;
      }
    });

    // Modal Controls
    document.getElementById("modalCloseBtn")?.addEventListener("click", closeReaderModal);
    document.getElementById("readerModal")?.addEventListener("click", (e) => {
      if (e.target.id === "readerModal") closeReaderModal();
    });
    document.getElementById("modalPrevBtn")?.addEventListener("click", () => navigateReader(-1));
    document.getElementById("modalNextBtn")?.addEventListener("click", () => navigateReader(1));
    document.getElementById("modalPrintBtn")?.addEventListener("click", () => window.print());

    // Modal Edition Mode Segmented Control
    document.querySelectorAll("[data-edition-mode]").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.editionMode = btn.dataset.editionMode;
        document.querySelectorAll("[data-edition-mode]").forEach((b) => b.classList.toggle("active", b === btn));
        renderReaderEditionBlocks();
      });
    });

    // Modal Script Mode Segmented Control
    document.querySelectorAll("[data-script-mode]").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.scriptMode = btn.dataset.scriptMode;
        document.querySelectorAll("[data-script-mode]").forEach((b) => b.classList.toggle("active", b === btn));
        renderReaderEditionBlocks();
      });
    });

    // Keyboard navigation for Modal
    document.addEventListener("keydown", (e) => {
      if (!state.currentItem) return;
      if (e.key === "Escape") closeReaderModal();
      if (e.key === "ArrowLeft") navigateReader(-1);
      if (e.key === "ArrowRight") navigateReader(1);
    });
  }

  // Initialize Portal
  document.addEventListener("DOMContentLoaded", () => {
    initFilterControls();
    renderExplorer();
    initComparator();
    renderGlossaryTab();
    bindEvents();
  });
})();
