from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Documentation"])

OFFLINE_DOCS_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ServiceFlow — API Documentation</title>
  <style>
    :root {
      --bg: #0c0a09;
      --card-bg: #1c1917;
      --border: #292524;
      --text: #f5f5f4;
      --text-muted: #a8a29e;
      --primary: #d97706;
      --primary-hover: #b45309;
      --get: #0284c7;
      --post: #16a34a;
      --patch: #ea580c;
      --delete: #dc2626;
      --code-bg: #141210;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
    body { background-color: var(--bg); color: var(--text); padding: 24px; line-height: 1.5; }
    .container { max-width: 1100px; margin: 0 auto; }
    header { margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px; }
    h1 { font-size: 24px; font-weight: 800; color: #fafaf9; display: flex; align-items: center; gap: 8px; }
    .badge { font-size: 11px; padding: 3px 8px; border-radius: 6px; font-weight: 700; text-transform: uppercase; }
    .badge-dev { background: #451a03; color: #fbbf24; border: 1px solid #78350f; }
    .badge-offline { background: #064e3b; color: #34d399; border: 1px solid #047857; }
    .auth-card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 16px; margin-bottom: 24px; }
    .auth-title { font-size: 13px; font-weight: 700; margin-bottom: 8px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; }
    .btn-group { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; }
    button { padding: 6px 12px; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer; border: 1px solid var(--border); background: #292524; color: #e7e5e4; transition: all 0.15s; }
    button:hover { background: #44403c; color: #fff; }
    button.btn-primary { background: var(--primary); color: #fff; border-color: var(--primary); }
    button.btn-primary:hover { background: var(--primary-hover); }
    .token-input-row { display: flex; gap: 8px; align-items: center; }
    input[type="text"], textarea { flex: 1; background: var(--code-bg); border: 1px solid var(--border); border-radius: 6px; padding: 8px 12px; color: #fafaf9; font-size: 12px; }
    input:focus, textarea:focus { outline: none; border-color: var(--primary); }
    .auth-status { font-size: 12px; font-weight: 600; margin-top: 8px; color: #34d399; }
    .search-bar { width: 100%; margin-bottom: 24px; padding: 10px 14px; font-size: 13px; background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; color: #fff; }
    .tag-section { margin-bottom: 28px; }
    .tag-title { font-size: 18px; font-weight: 700; margin-bottom: 12px; color: #e7e5e4; border-bottom: 1px solid var(--border); padding-bottom: 6px; }
    .route-card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; margin-bottom: 8px; overflow: hidden; }
    .route-header { padding: 10px 14px; display: flex; align-items: center; justify-content: space-between; cursor: pointer; user-select: none; }
    .route-header:hover { background: #24211e; }
    .route-main { display: flex; align-items: center; gap: 12px; font-size: 13px; font-weight: 600; font-family: monospace; }
    .method-badge { font-size: 11px; padding: 3px 8px; border-radius: 4px; font-weight: 800; min-width: 55px; text-align: center; color: #fff; font-family: sans-serif; }
    .method-GET { background: var(--get); }
    .method-POST { background: var(--post); }
    .method-PATCH { background: var(--patch); }
    .method-DELETE { background: var(--delete); }
    .route-desc { font-size: 12px; color: var(--text-muted); font-family: sans-serif; font-weight: 400; }
    .route-body { padding: 16px; border-top: 1px solid var(--border); background: var(--code-bg); display: none; }
    .route-body.open { display: block; }
    .param-title { font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--text-muted); margin: 10px 0 6px; }
    pre { background: #000; padding: 10px; border-radius: 6px; overflow-x: auto; font-size: 11px; color: #a3e635; margin-bottom: 10px; }
    .exec-btn { background: var(--primary); color: #fff; border: none; padding: 7px 16px; border-radius: 6px; font-size: 12px; font-weight: 700; margin-top: 8px; }
    .exec-btn:hover { background: var(--primary-hover); }
    .response-box { margin-top: 12px; padding: 10px; border-radius: 6px; background: #0c0a09; border: 1px solid var(--border); }
    .resp-meta { font-size: 11px; font-weight: 700; margin-bottom: 6px; }
    .resp-200 { color: #4ade80; }
    .resp-400, .resp-401, .resp-403, .resp-404, .resp-422, .resp-500 { color: #f87171; }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div>
        <h1>
          ServiceFlow API
          <span class="badge badge-dev">v1.0.0</span>
          <span class="badge badge-offline">Offline & Firewall Resilient</span>
        </h1>
        <p style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">
          Multi-Branch Café Operations Platform & AI Shift Intelligence (Zero external CDN dependencies)
        </p>
      </div>
      <div>
        <a href="/" style="font-size: 12px; color: var(--primary); text-decoration: none; font-weight: 600;">← Open Web App (React)</a>
      </div>
    </header>

    <!-- Quick Auth Helper -->
    <div class="auth-card">
      <div class="auth-title">Quick Authentication Helper</div>
      <div class="btn-group">
        <button onclick="quickLogin('kariz-cafe', 'manager@kariz.ir', 'password123', 'Manager')">
          🔑 Login as Manager (Ali Rezaei)
        </button>
        <button onclick="quickLogin('kariz-cafe', 'waiter.enghelab@kariz.ir', 'password123', 'Waiter (Enghelab)')">
          🔑 Login as Waiter (Saeed)
        </button>
        <button onclick="quickLogin('kariz-cafe', 'barista.enghelab@kariz.ir', 'password123', 'Barista (Enghelab)')">
          🔑 Login as Barista (Nima)
        </button>
        <button onclick="clearToken()">✖ Clear Auth</button>
      </div>
      <div class="token-input-row">
        <input type="text" id="authToken" placeholder="Bearer Token (Paste custom token or use 1-click login buttons above)..." oninput="saveManualToken()">
      </div>
      <div id="authStatus" class="auth-status" style="display: none;"></div>
    </div>

    <!-- Filter input -->
    <input type="text" class="search-bar" id="searchFilter" placeholder="Filter endpoints by path, method, or tag..." oninput="filterRoutes()">

    <!-- Routes Container -->
    <div id="routesContainer">
      <div style="text-align: center; padding: 40px; color: var(--text-muted);">
        Loading API schema from <code>/openapi.json</code>...
      </div>
    </div>
  </div>

  <script>
    let openapiData = null;
    let currentToken = localStorage.getItem('serviceflow_docs_token') || '';

    if (currentToken) {
      document.getElementById('authToken').value = currentToken;
      showAuthStatus('Token loaded from local storage');
    }

    async function quickLogin(slug, email, password, roleName) {
      try {
        const res = await fetch('/api/v1/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ restaurant_slug: slug, email: email, password: password })
        });
        if (!res.ok) {
          const err = await res.json();
          alert('Login failed: ' + (err.detail || JSON.stringify(err)));
          return;
        }
        const data = await res.json();
        currentToken = data.access_token;
        localStorage.setItem('serviceflow_docs_token', currentToken);
        document.getElementById('authToken').value = currentToken;
        showAuthStatus('✓ Authorized as ' + roleName + ' (' + data.full_name + ')');
      } catch (e) {
        alert('Network error logging in: ' + e.message);
      }
    }

    function clearToken() {
      currentToken = '';
      localStorage.removeItem('serviceflow_docs_token');
      document.getElementById('authToken').value = '';
      document.getElementById('authStatus').style.display = 'none';
    }

    function saveManualToken() {
      currentToken = document.getElementById('authToken').value.trim();
      localStorage.setItem('serviceflow_docs_token', currentToken);
      if (currentToken) showAuthStatus('Manual token active');
      else document.getElementById('authStatus').style.display = 'none';
    }

    function showAuthStatus(msg) {
      const el = document.getElementById('authStatus');
      el.innerText = msg;
      el.style.display = 'block';
    }

    async function loadSchema() {
      try {
        const res = await fetch('/openapi.json');
        if (!res.ok) throw new Error('HTTP ' + res.status);
        openapiData = await res.json();
        renderDocumentation(openapiData);
      } catch (e) {
        document.getElementById('routesContainer').innerHTML = 
          '<div style="background: #450a0a; border: 1px solid #7f1d1d; color: #fca5a5; padding: 20px; border-radius: 8px;">' +
          '<b>Failed to load /openapi.json:</b> ' + e.message + '</div>';
      }
    }

    function renderDocumentation(spec) {
      const container = document.getElementById('routesContainer');
      container.innerHTML = '';

      const tagsMap = {};
      const paths = spec.paths || {};

      for (const [path, methods] of Object.entries(paths)) {
        for (const [method, op] of Object.entries(methods)) {
          if (['get', 'post', 'put', 'patch', 'delete'].indexOf(method.toLowerCase()) === -1) continue;
          const tag = (op.tags && op.tags.length > 0) ? op.tags[0] : 'General';
          if (!tagsMap[tag]) tagsMap[tag] = [];
          tagsMap[tag].push({ path, method: method.toUpperCase(), op });
        }
      }

      for (const [tag, routes] of Object.entries(tagsMap)) {
        const tagSection = document.createElement('div');
        tagSection.className = 'tag-section';
        tagSection.id = 'tag-' + tag.replace(/\\s+/g, '-');

        const tagHeader = document.createElement('div');
        tagHeader.className = 'tag-title';
        tagHeader.innerText = tag;
        tagSection.appendChild(tagHeader);

        routes.forEach((route, idx) => {
          const card = document.createElement('div');
          card.className = 'route-card';
          card.dataset.filter = (tag + ' ' + route.method + ' ' + route.path + ' ' + (route.op.summary || '')).toLowerCase();

          const cardId = 'route-' + tag.replace(/\\s+/g, '-') + '-' + idx;
          const reqBodySchema = getRequestBodySchema(route.op, spec);

          card.innerHTML = `
            <div class="route-header" onclick="toggleRoute('${cardId}')">
              <div class="route-main">
                <span class="method-badge method-${route.method}">${route.method}</span>
                <span>${route.path}</span>
              </div>
              <span class="route-desc">${route.op.summary || route.op.description || ''}</span>
            </div>
            <div class="route-body" id="${cardId}">
              <p style="font-size: 12px; color: var(--text-muted); margin-bottom: 8px;">${route.op.description || route.op.summary || 'No description provided.'}</p>
              
              ${renderParams(route.op.parameters)}

              ${reqBodySchema ? `
                <div class="param-title">Request Body (JSON Example):</div>
                <textarea id="${cardId}-payload" rows="5" style="width: 100%; font-family: monospace;">${JSON.stringify(reqBodySchema, null, 2)}</textarea>
              ` : ''}

              <button class="exec-btn" onclick="executeRoute('${route.method}', '${route.path}', '${cardId}')">▶ Execute Request</button>
              
              <div id="${cardId}-resp" class="response-box" style="display: none;"></div>
            </div>
          `;
          tagSection.appendChild(card);
        });

        container.appendChild(tagSection);
      }
    }

    function toggleRoute(cardId) {
      const el = document.getElementById(cardId);
      if (el) el.classList.toggle('open');
    }

    function renderParams(params) {
      if (!params || params.length === 0) return '';
      let html = '<div class="param-title">Parameters:</div><ul style="font-size: 12px; margin-left: 20px; color: #d6d3d1;">';
      params.forEach(p => {
        html += `<li><code>${p.name}</code> (${p.in}${p.required ? ', required' : ''}): <span style="color: var(--text-muted)">${p.description || ''}</span></li>`;
      });
      html += '</ul>';
      return html;
    }

    function getRequestBodySchema(op, spec) {
      try {
        const content = op.requestBody && op.requestBody.content && op.requestBody.content['application/json'];
        if (!content || !content.schema) return null;
        let s = content.schema;
        if (s['$ref']) {
          const refName = s['$ref'].split('/').pop();
          s = spec.components.schemas[refName];
        }
        if (s && s.properties) {
          const sample = {};
          for (const [k, v] of Object.entries(s.properties)) {
            if (v.example !== undefined) sample[k] = v.example;
            else if (v.default !== undefined) sample[k] = v.default;
            else if (v.type === 'string') sample[k] = 'string';
            else if (v.type === 'integer') sample[k] = 1;
            else if (v.type === 'boolean') sample[k] = true;
            else if (v.type === 'array') sample[k] = [];
            else sample[k] = null;
          }
          return sample;
        }
      } catch (e) {
        return null;
      }
      return null;
    }

    async function executeRoute(method, pathTemplate, cardId) {
      const respBox = document.getElementById(cardId + '-resp');
      respBox.style.display = 'block';
      respBox.innerHTML = '<span style="color: var(--text-muted)">Executing request...</span>';

      let actualPath = pathTemplate;
      // If path has parameters like {order_id}, prompt user
      const paramMatches = pathTemplate.match(/\\{([^}]+)\\}/g);
      if (paramMatches) {
        for (const m of paramMatches) {
          const pName = m.replace('{', '').replace('}', '');
          const val = prompt('Enter value for path parameter "' + pName + '":');
          if (val === null) {
            respBox.innerHTML = '<span style="color: #f87171">Request cancelled: missing parameter ' + pName + '</span>';
            return;
          }
          actualPath = actualPath.replace(m, encodeURIComponent(val));
        }
      }

      const headers = { 'Content-Type': 'application/json' };
      if (currentToken) {
        headers['Authorization'] = 'Bearer ' + currentToken;
      }

      const options = { method, headers };
      if (['POST', 'PUT', 'PATCH'].includes(method)) {
        const payloadBox = document.getElementById(cardId + '-payload');
        if (payloadBox && payloadBox.value.trim()) {
          options.body = payloadBox.value.trim();
        }
      }

      const startTime = performance.now();
      try {
        const res = await fetch(actualPath, options);
        const duration = Math.round(performance.now() - startTime);
        let data;
        const text = await res.text();
        try { data = JSON.parse(text); } catch (e) { data = text; }

        const statusClass = res.ok ? 'resp-200' : 'resp-' + res.status;
        respBox.innerHTML = `
          <div class="resp-meta ${statusClass}">
            Status: ${res.status} ${res.statusText} (${duration} ms)
          </div>
          <pre>${typeof data === 'object' ? JSON.stringify(data, null, 2) : data}</pre>
        `;
      } catch (err) {
        respBox.innerHTML = '<div class="resp-meta resp-500">Network Error: ' + err.message + '</div>';
      }
    }

    function filterRoutes() {
      const query = document.getElementById('searchFilter').value.toLowerCase().trim();
      document.querySelectorAll('.route-card').forEach(card => {
        if (!query || card.dataset.filter.includes(query)) {
          card.style.display = 'block';
        } else {
          card.style.display = 'none';
        }
      });
    }

    loadSchema();
  </script>
</body>
</html>
"""

@router.get("/docs", response_class=HTMLResponse, include_in_schema=False)
def get_offline_docs():
    return HTMLResponse(content=OFFLINE_DOCS_HTML)

