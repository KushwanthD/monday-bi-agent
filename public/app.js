document.addEventListener('DOMContentLoaded', () => {
  const loginModal = document.getElementById('login-modal');
  const loginForm = document.getElementById('login-form');
  const loginUsername = document.getElementById('login-username');
  const loginPassword = document.getElementById('login-password');
  const loginLoading = document.getElementById('login-loading');
  const loadingStatusText = document.getElementById('loading-status-text');
  const loginErrorAlert = document.getElementById('login-error-alert');
  const loginErrorText = document.getElementById('login-error-text');
  const btnHeaderLogout = document.getElementById('btn-header-logout');

  const navBtns = document.querySelectorAll('.nav-btn');
  const viewPanels = document.querySelectorAll('.view-panel');

  const chatForm = document.getElementById('chat-form');
  const chatInput = document.getElementById('chat-input');
  const chatBox = document.getElementById('chat-box');
  const chips = document.querySelectorAll('.chip');
  
  const btnLeadership = document.getElementById('btn-generate-leadership');
  const modal = document.getElementById('briefing-modal');
  const btnCloseModal = document.getElementById('btn-close-modal');
  const briefingContent = document.getElementById('briefing-content');
  const btnCopyBriefing = document.getElementById('btn-copy-briefing');
  const btnPrintBriefing = document.getElementById('btn-print-briefing');

  const btnCopyViewBriefing = document.getElementById('btn-copy-view-briefing');
  const btnRefreshBriefing = document.getElementById('btn-refresh-briefing');

  const boardSelect = document.getElementById('board-select');
  const dynamicBoardTabs = document.getElementById('dynamic-board-tabs');
  const linkOpenMonday = document.getElementById('link-open-monday');

  const filterIndicator = document.getElementById('filter-indicator');
  const filterText = document.getElementById('filter-text');
  const btnClearFilter = document.getElementById('btn-clear-filter');

  // Multi-Criteria Table Filter Toolbar Elements
  const filterSearch = document.getElementById('filter-search');
  const filterSector = document.getElementById('filter-sector');
  const filterStatus = document.getElementById('filter-status');
  const filterStage = document.getElementById('filter-stage');
  const btnResetTableFilters = document.getElementById('btn-reset-table-filters');

  let loadedDeals = [];
  let loadedWorkOrders = [];
  let discoveredBoards = [];

  let activeBoardId = '';
  let activeGroupTitle = '';
  let currentBoardItems = [];

  // Client-Side Web Crypto SHA-256 Hashing Engine
  async function hashSHA256(text) {
    const encoder = new TextEncoder();
    const data = encoder.encode(text);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  }

  // Session Authentication Check
  function checkSessionAuth() {
    const token = sessionStorage.getItem('skylark_auth');
    if (token) {
      loginModal.classList.add('hidden');
      checkHealth();
      loadBoardData();
    } else {
      loginModal.classList.remove('hidden');
    }
  }

  checkSessionAuth();

  // Login Form Submit with SHA-256 Pre-Transmission Hashing & Cyberpunk Loading Screen
  loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = loginUsername.value.trim();
    const rawPassword = loginPassword.value;

    if (!username || !rawPassword) return;

    loginForm.style.display = 'none';
    loginErrorAlert.style.display = 'none';
    loginLoading.style.display = 'flex';
    loadingStatusText.textContent = '🔐 Hashing Password via Client SHA-256...';

    await new Promise(r => setTimeout(r, 400));

    // Compute Client-Side SHA-256 Hash
    const passHash = await hashSHA256(rawPassword);
    loadingStatusText.textContent = '🛡️ Transmitting SHA-256 Payload to WAF Server...';

    await new Promise(r => setTimeout(r, 400));

    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: username,
          password_hash: passHash
        })
      });
      const data = await res.json();

      if (res.ok && data.token) {
        loadingStatusText.textContent = '🚀 Authentication Verified! Launching Portal...';
        sessionStorage.setItem('skylark_auth', data.token);

        await new Promise(r => setTimeout(r, 600));

        loginLoading.style.display = 'none';
        loginForm.style.display = 'block';
        loginPassword.value = '';
        loginModal.classList.add('hidden');

        checkHealth();
        loadBoardData();
      } else {
        await new Promise(r => setTimeout(r, 400));
        loginLoading.style.display = 'none';
        loginForm.style.display = 'block';
        loginErrorAlert.style.display = 'block';
        loginErrorText.textContent = `❌ ${data.error || 'Invalid credentials'}`;
      }
    } catch (err) {
      loginLoading.style.display = 'none';
      loginForm.style.display = 'block';
      loginErrorAlert.style.display = 'block';
      loginErrorText.textContent = '❌ Server connection error during authentication.';
    }
  });

  // Header Logout Handler
  function handleLogout() {
    sessionStorage.removeItem('skylark_auth');
    loginModal.classList.remove('hidden');
    loginForm.style.display = 'block';
    loginLoading.style.display = 'none';
    loginErrorAlert.style.display = 'none';
  }

  if (btnHeaderLogout) btnHeaderLogout.addEventListener('click', handleLogout);

  // Automatic Real-Time Live Polling Sync (Every 15 Seconds)
  setInterval(() => {
    if (sessionStorage.getItem('skylark_auth')) {
      loadBoardData();
    }
  }, 15000);

  // Sidebar Navigation Switcher
  navBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetViewId = btn.getAttribute('data-view');
      
      navBtns.forEach(b => b.classList.remove('active'));
      viewPanels.forEach(p => p.classList.remove('active'));

      btn.classList.add('active');
      const targetPanel = document.getElementById(targetViewId);
      if (targetPanel) targetPanel.classList.add('active');

      // Update Page Headers
      if (targetViewId === 'view-chat') {
        document.getElementById('page-title').textContent = 'Executive Business Intelligence Console';
        document.getElementById('page-subtitle').textContent = 'Real-time cross-board analytics for Work Orders & Sales Pipeline';
      } else if (targetViewId === 'view-boards') {
        document.getElementById('page-title').textContent = 'Monday.com Boards Live Viewer';
        document.getElementById('page-subtitle').textContent = 'Normalized table view of Deals Funnel & Work Orders Tracker';
        applyTableFilters();
      } else if (targetViewId === 'view-briefing') {
        document.getElementById('page-title').textContent = 'Executive Leadership Briefings';
        document.getElementById('page-subtitle').textContent = 'Formatted updates ready for C-suite meetings and leadership reviews';
        loadBriefingView();
      } else if (targetViewId === 'view-security') {
        document.getElementById('page-title').textContent = 'Cybersecurity & OWASP WAF Audit';
        document.getElementById('page-subtitle').textContent = 'Tamper-evident SHA-256 audit logs, rate limiting metrics, and security controls';
        loadSecurityLogs();
      } else if (targetViewId === 'view-features') {
        document.getElementById('page-title').textContent = 'System Architecture & Features Guide';
        document.getElementById('page-subtitle').textContent = 'Comprehensive breakdown of BI analytics, OWASP security, and GraphQL discovery';
      }
    });
  });

  // Chat Form Submit
  chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = chatInput.value.trim();
    if (!query) return;

    appendMessage('user', query);
    chatInput.value = '';

    try {
      const res = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });
      const data = await res.json();

      if (res.ok) {
        appendMessage('agent', data.answer);
        if (data.metrics && Object.keys(data.metrics).length > 0) {
          updateKPIs(data.metrics);
        }
        if (data.caveats) {
          updateCaveats(data.caveats);
        }

        // Handle Chat Actions (Redirects, Filters, Exports)
        if (data.action === 'export') {
          const exportType = (data.action_payload && data.action_payload.type) || 'pdf';
          if (exportType === 'pdf') {
            setTimeout(() => window.print(), 800);
          } else if (exportType === 'csv') {
            exportTableToCSV();
          }
        } else if (data.action === 'redirect') {
          const targetView = data.action_payload.view;
          const targetBtn = document.querySelector(`.nav-btn[data-view="${targetView}"]`);
          if (targetBtn) setTimeout(() => targetBtn.click(), 1200);
        } else if (data.action === 'apply_filters_and_redirect') {
          const payload = data.action_payload;
          const targetBtn = document.querySelector(`.nav-btn[data-view="view-boards"]`);
          
          setTimeout(() => {
            if (targetBtn) targetBtn.click();

            if (payload.sector && filterSector) filterSector.value = payload.sector;
            if (payload.status && filterStatus) filterStatus.value = payload.status;
            if (payload.search && filterSearch) filterSearch.value = payload.search;

            applyTableFilters();
          }, 1500);
        }
      } else {
        appendMessage('agent', `⚠️ ${data.error || 'Server error occurred'}\n${data.details || ''}`);
      }
    } catch (err) {
      appendMessage('agent', `❌ Connection error: Could not reach BI Agent server.`);
    }
  });

  // CSV Export Utility Function
  function exportTableToCSV() {
    if (!currentBoardItems || currentBoardItems.length === 0) {
      alert("No table data available to export.");
      return;
    }
    const headers = ["ID", "Name", "Group", "State", "Updated At"];
    const rows = currentBoardItems.map(item => [
      `"${item.id || ''}"`,
      `"${(item.name || '').replace(/"/g, '""')}"`,
      `"${(item.group_title || '').replace(/"/g, '""')}"`,
      `"${(item.state || '').replace(/"/g, '""')}"`,
      `"${item.updated_at || ''}"`
    ]);
    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `monday_board_export_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  // Suggestion Chips Click
  chips.forEach(chip => {
    chip.addEventListener('click', () => {
      const promptText = chip.getAttribute('data-prompt');
      chatInput.value = promptText;
      chatForm.dispatchEvent(new Event('submit'));
    });
  });

  // Leadership Update Trigger (Modal)
  btnLeadership.addEventListener('click', async () => {
    modal.classList.add('show');
    briefingContent.textContent = '⚡ Generating Executive Leadership Update...';

    try {
      const res = await fetch('/api/leadership-update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      const data = await res.json();
      if (res.ok) {
        briefingContent.textContent = data.markdown;
      } else {
        briefingContent.textContent = `❌ Error: ${data.error}`;
      }
    } catch (err) {
      briefingContent.textContent = `❌ Connection Error generating briefing.`;
    }
  });

  btnCloseModal.addEventListener('click', () => modal.classList.remove('show'));

  btnCopyBriefing.addEventListener('click', () => {
    navigator.clipboard.writeText(briefingContent.textContent);
    btnCopyBriefing.textContent = '✓ Copied!';
    setTimeout(() => btnCopyBriefing.textContent = '📋 Copy Markdown', 2000);
  });

  btnPrintBriefing.addEventListener('click', () => {
    window.print();
  });

  // Briefing View Buttons
  if (btnCopyViewBriefing) {
    btnCopyViewBriefing.addEventListener('click', () => {
      const briefingText = document.getElementById('view-briefing-content').textContent;
      navigator.clipboard.writeText(briefingText);
      btnCopyViewBriefing.textContent = '✓ Copied!';
      setTimeout(() => btnCopyViewBriefing.textContent = '📋 Copy Markdown', 2000);
    });
  }

  if (btnRefreshBriefing) {
    btnRefreshBriefing.addEventListener('click', () => {
      loadBriefingView();
    });
  }

  // Clear Filter Button
  if (btnClearFilter) {
    btnClearFilter.addEventListener('click', () => {
      resetAllFilters();
    });
  }

  // Multi-Filter Toolbar Listeners
  if (filterSearch) filterSearch.addEventListener('input', () => applyTableFilters());
  if (filterSector) filterSector.addEventListener('change', () => applyTableFilters());
  if (filterStatus) filterStatus.addEventListener('change', () => applyTableFilters());
  if (filterStage) filterStage.addEventListener('change', () => applyTableFilters());
  
  if (btnResetTableFilters) {
    btnResetTableFilters.addEventListener('click', resetAllFilters);
  }

  // Board Selector Dropdown Listener
  if (boardSelect) {
    boardSelect.addEventListener('change', () => {
      activeBoardId = boardSelect.value;
      activeGroupTitle = '';
      updateCurrentBoardState();
      renderGroupTabs();
      populateDynamicFilterDropdowns();
      resetAllFilters();
    });
  }

  function resetAllFilters() {
    if (filterSearch) filterSearch.value = '';
    if (filterSector) filterSector.value = 'ALL';
    if (filterStatus) filterStatus.value = 'ALL';
    if (filterStage) filterStage.value = 'ALL';
    if (filterIndicator) filterIndicator.style.display = 'none';
    applyTableFilters();
  }

  // Render Board Selector Dropdown
  function renderBoardDropdown() {
    if (!boardSelect) return;

    if (!discoveredBoards || discoveredBoards.length === 0) {
      boardSelect.innerHTML = `<option value="">No Boards Available</option>`;
      return;
    }

    if (!activeBoardId) {
      activeBoardId = discoveredBoards[0].id;
    }

    let options = '';
    discoveredBoards.forEach(b => {
      options += `<option value="${b.id}" ${activeBoardId === b.id ? 'selected' : ''}>📌 ${escapeHTML(b.name)} (${b.items_count} Items)</option>`;
    });

    boardSelect.innerHTML = options;
  }

  // Update State for Selected Board
  function updateCurrentBoardState() {
    if (!discoveredBoards || discoveredBoards.length === 0) {
      currentBoardItems = [];
      return;
    }
    const selected = discoveredBoards.find(b => b.id === activeBoardId) || discoveredBoards[0];
    if (selected) {
      activeBoardId = selected.id;
      if (linkOpenMonday) linkOpenMonday.href = `https://kushwanth91782s-team.monday.com/boards/${selected.id}`;
      currentBoardItems = selected.items;
    } else {
      currentBoardItems = [];
    }
  }

  // Render ONLY Actual Monday.com Groups
  function renderGroupTabs() {
    if (!dynamicBoardTabs) return;

    let groupCounts = {};

    currentBoardItems.forEach(item => {
      const gTitle = item.group_title || 'Main Group';
      groupCounts[gTitle] = (groupCounts[gTitle] || 0) + 1;
    });

    const groupsList = Object.keys(groupCounts);

    if (groupsList.length === 0) {
      dynamicBoardTabs.innerHTML = `<button class="tab-btn active">No Groups</button>`;
      return;
    }

    if (!activeGroupTitle || !groupsList.includes(activeGroupTitle)) {
      activeGroupTitle = groupsList[0];
    }

    let html = '';
    groupsList.forEach(grp => {
      const count = groupCounts[grp];
      const isActive = activeGroupTitle === grp;
      html += `<button class="tab-btn ${isActive ? 'active' : ''}" data-group="${escapeHTML(grp)}">📁 ${escapeHTML(grp)} (${count} Items)</button>`;
    });

    dynamicBoardTabs.innerHTML = html;

    const grpBtns = dynamicBoardTabs.querySelectorAll('[data-group]');
    grpBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        activeGroupTitle = btn.getAttribute('data-group');
        renderGroupTabs();
        populateDynamicFilterDropdowns();
        resetAllFilters();
      });
    });
  }

  // DYNAMIC FILTER ENGINE: Scans dataset and populates dropdowns with 100% of unique values
  function populateDynamicFilterDropdowns() {
    let targetItems = currentBoardItems;
    if (activeGroupTitle) {
      targetItems = currentBoardItems.filter(item => (item.group_title || '') === activeGroupTitle);
    }

    const curSector = filterSector ? filterSector.value : 'ALL';
    const curStatus = filterStatus ? filterStatus.value : 'ALL';
    const curStage = filterStage ? filterStage.value : 'ALL';

    const rawSectors = new Set();
    const rawStatuses = new Set();
    const rawStages = new Set();

    targetItems.forEach(it => {
      const sec = (it['Sector/service'] || it['Sector'] || it.sector || '').trim();
      if (sec && sec !== 'Sector/service' && sec !== 'Sector') rawSectors.add(sec);

      const stat = (it['Deal Status'] || it['Execution Status'] || it.status || '').trim();
      if (stat && stat !== 'Deal Status' && stat !== 'Execution Status') rawStatuses.add(stat);

      const stg = (it['Deal Stage'] || it['Pipeline Stage'] || it.stage || '').trim();
      if (stg && stg !== 'Deal Stage' && stg !== 'Pipeline Stage') rawStages.add(stg);
    });

    const sectorsSorted = Array.from(rawSectors).sort();
    const statusesSorted = Array.from(rawStatuses).sort();
    const stagesSorted = Array.from(rawStages).sort();

    if (filterSector) {
      let secHtml = `<option value="ALL">All Sectors</option>`;
      sectorsSorted.forEach(s => {
        secHtml += `<option value="${escapeHTML(s)}" ${curSector === s ? 'selected' : ''}>${escapeHTML(s)}</option>`;
      });
      filterSector.innerHTML = secHtml;
    }

    if (filterStatus) {
      let statHtml = `<option value="ALL">All Statuses</option>`;
      statusesSorted.forEach(st => {
        statHtml += `<option value="${escapeHTML(st)}" ${curStatus === st ? 'selected' : ''}>${escapeHTML(st)}</option>`;
      });
      filterStatus.innerHTML = statHtml;
    }

    if (filterStage) {
      let stgHtml = `<option value="ALL">All Deal Stages</option>`;
      stagesSorted.forEach(stg => {
        stgHtml += `<option value="${escapeHTML(stg)}" ${curStage === stg ? 'selected' : ''}>${escapeHTML(stg)}</option>`;
      });
      filterStage.innerHTML = stgHtml;
    }
  }

  // KPI Cards Navigation Listeners
  const kpiCards = document.querySelectorAll('.kpi-card.clickable');
  kpiCards.forEach(card => {
    card.addEventListener('click', () => {
      const filterType = card.getAttribute('data-filter');
      const btnBoards = document.getElementById('btn-nav-boards');
      if (btnBoards) btnBoards.click();

      if (filterType === 'work-orders') {
        activeGroupTitle = 'Work_Order_Tracker_Data.csv';
        renderGroupTabs();
        populateDynamicFilterDropdowns();
        resetAllFilters();
      } else {
        activeGroupTitle = 'Deal_funnel_Data.csv';
        renderGroupTabs();
        populateDynamicFilterDropdowns();
        if (filterType === 'won-deals') {
          if (filterStatus) filterStatus.value = 'Won';
          applyTableFilters('Closed Won Revenue');
        } else if (filterType === 'negotiation-deals') {
          if (filterStage) filterStage.value = 'F. Negotiations';
          applyTableFilters('Active Proposals & Negotiations');
        } else {
          resetAllFilters();
        }
      }
    });
  });

  // Master Multi-Criteria Compound (AND) Filtering Function
  function applyTableFilters(customLabel = null) {
    const searchText = filterSearch ? filterSearch.value.trim().toLowerCase() : '';
    const selectedSector = filterSector ? filterSector.value : 'ALL';
    const selectedStatus = filterStatus ? filterStatus.value : 'ALL';
    const selectedStage = filterStage ? filterStage.value : 'ALL';

    const activeCriteria = [];
    if (activeGroupTitle) activeCriteria.push(`Group: ${activeGroupTitle}`);
    if (searchText) activeCriteria.push(`"${searchText}"`);
    if (selectedSector !== 'ALL') activeCriteria.push(`Sector: ${selectedSector}`);
    if (selectedStatus !== 'ALL') activeCriteria.push(`Status: ${selectedStatus}`);
    if (selectedStage !== 'ALL') activeCriteria.push(`Stage: ${selectedStage}`);

    const hasActiveFilters = activeCriteria.length > 0;

    let itemsToFilter = currentBoardItems;
    if (activeGroupTitle) {
      itemsToFilter = currentBoardItems.filter(item => (item.group_title || '') === activeGroupTitle);
    }

    const filtered = itemsToFilter.filter(item => {
      if (searchText) {
        const itemStr = JSON.stringify(item).toLowerCase();
        if (!itemStr.includes(searchText)) return false;
      }
      if (selectedSector !== 'ALL') {
        const sec = (item['Sector/service'] || item['Sector'] || item.sector || '').trim();
        if (sec.toLowerCase() !== selectedSector.toLowerCase()) return false;
      }
      if (selectedStatus !== 'ALL') {
        const stat = (item['Deal Status'] || item['Execution Status'] || item.status || '').trim();
        if (stat.toLowerCase() !== selectedStatus.toLowerCase()) return false;
      }
      if (selectedStage !== 'ALL') {
        const stage = (item['Deal Stage'] || item['Pipeline Stage'] || item.stage || '').trim();
        if (stage.toLowerCase() !== selectedStage.toLowerCase()) return false;
      }
      return true;
    });

    if (hasActiveFilters || customLabel) {
      if (filterIndicator && filterText) {
        filterIndicator.style.display = 'flex';
        const labelText = customLabel || activeCriteria.join(' + ');
        filterText.textContent = `🎯 Filtered View: ${labelText} (${filtered.length} matching items)`;
      }
    } else {
      if (filterIndicator) filterIndicator.style.display = 'none';
    }

    renderTableRows(filtered);
  }

  // Intelligent Column Mapper
  function renderTableRows(items) {
    const head = document.getElementById('table-head');
    const body = document.getElementById('table-body');
    if (!items || items.length === 0) {
      head.innerHTML = `<th>Item Name</th><th>Group</th><th>Details</th>`;
      body.innerHTML = `<tr><td colspan="3" style="text-align:center; padding: 25px; color: #94a3b8;">⚠️ No items match the selected criteria.</td></tr>`;
      return;
    }

    const isDealsGroup = activeGroupTitle.toLowerCase().includes('deal') || activeGroupTitle.toLowerCase().includes('funnel');
    const isOrdersGroup = activeGroupTitle.toLowerCase().includes('work') || activeGroupTitle.toLowerCase().includes('order') || activeGroupTitle.toLowerCase().includes('tracker');

    if (isDealsGroup) {
      head.innerHTML = `
        <th>Deal Name</th>
        <th>Client Code</th>
        <th>Sector / Service</th>
        <th>Deal Stage</th>
        <th>Deal Status</th>
        <th>Deal Value (₹)</th>
        <th>Owner Code</th>
      `;
      body.innerHTML = items.map(d => {
        const dName = d['Deal Name'] || d['Deal name masked'] || d['Project Name'] || 'Item';
        const client = d['Client Code'] || d['Customer Name Code'] || d['Client Name'] || '-';
        const sector = d['Sector/service'] || d['Sector'] || '-';
        const stage = d['Deal Stage'] || d['Pipeline Stage'] || '-';
        const status = d['Deal Status'] || 'Open';
        const rawVal = d['Masked Deal value'] || d['Deal Value ($)'] || d['Value'] || '0';
        const valNum = parseFloat(String(rawVal).replace(/[^0-9.]/g, '')) || 0;
        const owner = d['Owner code'] || d['BD/KAM Personnel code'] || '-';

        return `
          <tr>
            <td><strong>${escapeHTML(dName)}</strong></td>
            <td>${escapeHTML(client)}</td>
            <td>${escapeHTML(sector)}</td>
            <td>${escapeHTML(stage)}</td>
            <td><span class="badge ${status === 'Won' ? 'badge-security' : ''}">${escapeHTML(status)}</span></td>
            <td>₹${valNum.toLocaleString('en-IN', {minimumFractionDigits: 2})}</td>
            <td>${escapeHTML(owner)}</td>
          </tr>
        `;
      }).join('');
      return;
    }

    if (isOrdersGroup) {
      head.innerHTML = `
        <th>Project Name</th>
        <th>Customer Code</th>
        <th>Serial #</th>
        <th>Sector</th>
        <th>Execution Status</th>
        <th>Billed Amount (₹)</th>
        <th>Personnel Code</th>
      `;
      body.innerHTML = items.map(o => {
        const pName = o['Deal name masked'] || o['Project Name'] || o['Deal Name'] || 'Project';
        const client = o['Customer Name Code'] || o['Client Code'] || '-';
        const serial = o['Serial #'] || o['Work Order ID'] || '-';
        const sector = o['Sector'] || o['Sector/service'] || '-';
        const status = o['Execution Status'] || o['Flight Status'] || 'Ongoing';
        const rawCost = o['Amount in Rupees (Excl of GST) (Masked)'] || o['Billed Value in Rupees (Excl of GST.) (Masked)'] || '0';
        const costNum = parseFloat(String(rawCost).replace(/[^0-9.]/g, '')) || 0;
        const owner = o['BD/KAM Personnel code'] || o['Owner code'] || '-';

        return `
          <tr>
            <td><strong>${escapeHTML(pName)}</strong></td>
            <td>${escapeHTML(client)}</td>
            <td>${escapeHTML(serial)}</td>
            <td>${escapeHTML(sector)}</td>
            <td><span class="badge badge-security">${escapeHTML(status)}</span></td>
            <td>₹${costNum.toLocaleString('en-IN', {minimumFractionDigits: 2})}</td>
            <td>${escapeHTML(owner)}</td>
          </tr>
        `;
      }).join('');
      return;
    }

    // Generic Fallback for Custom Boards
    const sample = items[0];
    const ignoreKeys = ['Deal Name', 'Deal name masked', 'Project Name', 'group_title', 'group_id', 'person', 'status', 'date4', 'person_1'];
    
    const dataKeys = Object.keys(sample).filter(k => {
      if (ignoreKeys.includes(k)) return false;
      return items.some(it => (it[k] || '').trim() !== '');
    }).slice(0, 6);

    head.innerHTML = `<th>Item Name</th><th>Group</th>` + dataKeys.map(k => `<th>${escapeHTML(k)}</th>`).join('');

    body.innerHTML = items.map(item => `
      <tr>
        <td><strong>${escapeHTML(item['Deal Name'] || item['Project Name'] || item['Deal name masked'] || 'Item')}</strong></td>
        <td><span class="badge badge-cyan">${escapeHTML(item.group_title || 'Main Group')}</span></td>
        ${dataKeys.map(k => `<td>${escapeHTML(item[k] || '')}</td>`).join('')}
      </tr>
    `).join('');
  }

  async function loadBriefingView() {
    const contentEl = document.getElementById('view-briefing-content');
    contentEl.textContent = '⚡ Loading Executive Briefing...';
    try {
      const res = await fetch('/api/leadership-update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      const data = await res.json();
      contentEl.textContent = data.markdown;
    } catch (e) {
      contentEl.textContent = '❌ Failed to load briefing.';
    }
  }

  async function loadSecurityLogs() {
    const tbody = document.getElementById('audit-table-body');
    try {
      const res = await fetch('/api/security/audit');
      const data = await res.json();
      const logs = data.audit_logs || [];
      if (logs.length === 0) {
        tbody.innerHTML = `<tr><td colspan="4" style="text-align:center;">No security audit events logged yet.</td></tr>`;
        return;
      }
      tbody.innerHTML = logs.map(l => `
        <tr>
          <td>${l.timestamp}</td>
          <td><span class="badge badge-security">${escapeHTML(l.event_type)}</span></td>
          <td>${escapeHTML(l.details)}</td>
          <td><code>${l.checksum}</code></td>
        </tr>
      `).join('');
    } catch (e) {
      tbody.innerHTML = `<tr><td colspan="4" style="text-align:center;">Error loading security logs.</td></tr>`;
    }
  }

  async function checkHealth() {
    try {
      const res = await fetch('/api/health');
      const data = await res.json();
      const statusTitle = document.getElementById('status-title');
      const statusDesc = document.getElementById('status-desc');

      if (data.monday_connected) {
        statusTitle.textContent = 'Monday.com Connected';
        statusDesc.textContent = 'Live GraphQL API v2';
      } else {
        statusTitle.textContent = 'Live Demo Mode';
        statusDesc.textContent = 'Official Resilient Dataset';
      }
    } catch (e) {
      console.warn('Health check warning:', e);
    }
  }

  async function loadBoardData() {
    try {
      const res = await fetch('/api/monday/boards');
      const data = await res.json();
      loadedDeals = data.deals || [];
      loadedWorkOrders = data.work_orders || [];
      discoveredBoards = data.all_boards || [];

      renderBoardDropdown();
      updateCurrentBoardState();
      renderGroupTabs();
      populateDynamicFilterDropdowns();

      if (data.caveats) {
        updateCaveats(data.caveats);
      }
      applyTableFilters();
    } catch (e) {
      console.warn('Board data load warning:', e);
    }
  }

  function appendMessage(sender, text) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${sender === 'user' ? 'user-message' : 'agent-message'}`;
    msgDiv.innerHTML = `
      <div class="msg-avatar">${sender === 'user' ? '👤' : '🤖'}</div>
      <div class="msg-content">${escapeHTML(text)}</div>
    `;
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
  }

  function escapeHTML(str) {
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br>');
  }

  function updateKPIs(metrics) {
    if (metrics.total_pipeline !== undefined) {
      document.getElementById('kpi-pipeline').textContent = `₹${metrics.total_pipeline.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
    }
    if (metrics.closed_won !== undefined) {
      document.getElementById('kpi-won').textContent = `₹${metrics.closed_won.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
    }
    if (metrics.in_negotiation !== undefined) {
      document.getElementById('kpi-negotiation').textContent = `₹${metrics.in_negotiation.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
    }
    if (metrics.completed_flights !== undefined) {
      document.getElementById('kpi-flights').textContent = `${metrics.completed_flights} Projects`;
    }
  }

  function updateCaveats(caveatsList) {
    const listEl = document.getElementById('caveats-list');
    if (!caveatsList || caveatsList.length === 0) {
      listEl.innerHTML = '<li>✅ All data validated with 100% field integrity.</li>';
      return;
    }
    listEl.innerHTML = caveatsList.map(c => `<li>${c}</li>`).join('');
  }
});
