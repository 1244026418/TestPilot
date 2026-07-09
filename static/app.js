const state = {
  projects: [],
  endpoints: [],
  cases: [],
  runs: [],
  selectedProjectId: null,
  selectedEndpointId: null,
};

const $ = (selector) => document.querySelector(selector);

const els = {
  projectForm: $("#projectForm"),
  endpointForm: $("#endpointForm"),
  generateForm: $("#generateForm"),
  caseForm: $("#caseForm"),
  demoProjectBtn: $("#demoProjectBtn"),
  refreshProjectsBtn: $("#refreshProjectsBtn"),
  runProjectBtn: $("#runProjectBtn"),
  projectList: $("#projectList"),
  endpointList: $("#endpointList"),
  caseList: $("#caseList"),
  runList: $("#runList"),
  currentProjectTitle: $("#currentProjectTitle"),
  endpointHint: $("#endpointHint"),
  caseHint: $("#caseHint"),
  runHint: $("#runHint"),
  toast: $("#toast"),
  stats: {
    projects: $("#statProjects"),
    endpoints: $("#statEndpoints"),
    cases: $("#statCases"),
    runs: $("#statRuns"),
  },
};

function toast(message) {
  els.toast.textContent = message;
  els.toast.classList.add("show");
  window.clearTimeout(toast.timer);
  toast.timer = window.setTimeout(() => els.toast.classList.remove("show"), 2600);
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const text = await response.text();
  const data = text ? JSON.parse(text) : null;
  if (!response.ok) {
    const detail = data && data.detail ? data.detail : `请求失败：${response.status}`;
    throw new Error(detail);
  }
  return data;
}

function parseJson(text, fallback = {}) {
  if (!text.trim()) return fallback;
  try {
    return JSON.parse(text);
  } catch (error) {
    throw new Error("JSON 格式不正确");
  }
}

function formatDate(value) {
  if (!value) return "-";
  return new Date(value).toLocaleString("zh-CN", { hour12: false });
}

function safeJson(value) {
  return JSON.stringify(value || {}, null, 2);
}

function empty(text) {
  return `<div class="empty">${text}</div>`;
}

function badge(text, type = "") {
  return `<span class="badge ${type}">${text}</span>`;
}

async function loadStats() {
  const stats = await api("/dashboard/stats");
  els.stats.projects.textContent = stats.projects;
  els.stats.endpoints.textContent = stats.endpoints;
  els.stats.cases.textContent = stats.cases;
  els.stats.runs.textContent = stats.runs;
}

async function loadProjects() {
  state.projects = await api("/projects");
  renderProjects();
  await loadStats();
}

function renderProjects() {
  if (!state.projects.length) {
    els.projectList.innerHTML = empty("暂无项目");
    return;
  }
  els.projectList.innerHTML = state.projects.map((project) => `
    <article class="project-item ${project.id === state.selectedProjectId ? "active" : ""}" data-project-id="${project.id}">
      <div class="item-head">
        <div>
          <h3>${project.name}</h3>
          <div class="meta">${project.description || "无描述"}</div>
        </div>
        ${badge(`#${project.id}`)}
      </div>
    </article>
  `).join("");
}

async function selectProject(projectId) {
  state.selectedProjectId = projectId;
  state.selectedEndpointId = null;
  const project = state.projects.find((item) => item.id === projectId);
  els.currentProjectTitle.textContent = project ? project.name : "请选择项目";
  els.runProjectBtn.disabled = !projectId;
  els.endpointForm.querySelector("button[type='submit']").disabled = !projectId;
  renderProjects();
  await Promise.all([loadEndpoints(), loadRuns()]);
  state.cases = [];
  renderCases();
}

async function loadEndpoints() {
  if (!state.selectedProjectId) {
    state.endpoints = [];
    renderEndpoints();
    return;
  }
  state.endpoints = await api(`/projects/${state.selectedProjectId}/endpoints`);
  renderEndpoints();
}

function renderEndpoints() {
  els.endpointHint.textContent = state.selectedProjectId ? "选择接口后生成或维护用例" : "选择项目后录入接口";
  if (!state.endpoints.length) {
    els.endpointList.innerHTML = empty("暂无接口");
    return;
  }
  els.endpointList.innerHTML = state.endpoints.map((endpoint) => `
    <article class="data-item ${endpoint.id === state.selectedEndpointId ? "active" : ""}" data-endpoint-id="${endpoint.id}">
      <div class="item-head">
        <div>
          <h3>${endpoint.name}</h3>
          <div class="meta">${endpoint.method} ${endpoint.url}</div>
        </div>
        <div class="item-actions">
          ${badge(String(endpoint.expected_status), endpoint.expected_status < 400 ? "success" : "warning")}
          <button class="secondary select-endpoint" data-endpoint-id="${endpoint.id}">选择</button>
          <button class="danger delete-endpoint" data-endpoint-id="${endpoint.id}">删除</button>
        </div>
      </div>
      <pre class="json-preview">${safeJson(endpoint.body)}</pre>
    </article>
  `).join("");
}

async function selectEndpoint(endpointId) {
  state.selectedEndpointId = endpointId;
  const endpoint = state.endpoints.find((item) => item.id === endpointId);
  els.caseHint.textContent = endpoint ? endpoint.name : "选择接口后管理用例";
  els.generateForm.querySelector("button[type='submit']").disabled = !endpointId;
  els.caseForm.querySelector("button[type='submit']").disabled = !endpointId;
  renderEndpoints();
  await loadCases();
}

async function loadCases() {
  if (!state.selectedEndpointId) {
    state.cases = [];
    renderCases();
    return;
  }
  state.cases = await api(`/endpoints/${state.selectedEndpointId}/cases`);
  renderCases();
}

function renderCases() {
  if (!state.selectedEndpointId) {
    els.caseList.innerHTML = empty("未选择接口");
    return;
  }
  if (!state.cases.length) {
    els.caseList.innerHTML = empty("暂无用例");
    return;
  }
  els.caseList.innerHTML = state.cases.map((item) => `
    <article class="data-item">
      <div class="item-head">
        <div>
          <h3>${item.title}</h3>
          <div class="meta">${item.reason || "无设计原因"}</div>
        </div>
        <div class="item-actions">
          ${badge(categoryText(item.category), item.category === "normal" ? "success" : "warning")}
          ${badge(String(item.expected_status || "-"))}
          <button class="danger delete-case" data-case-id="${item.id}">删除</button>
        </div>
      </div>
      <pre class="json-preview">${safeJson(item.request_body)}</pre>
    </article>
  `).join("");
}

function categoryText(category) {
  return { normal: "正常", exception: "异常", boundary: "边界", auth: "鉴权" }[category] || category;
}

async function loadRuns() {
  if (!state.selectedProjectId) {
    state.runs = [];
    renderRuns();
    return;
  }
  state.runs = await api(`/projects/${state.selectedProjectId}/runs`);
  renderRuns();
}

function renderRuns() {
  if (!state.selectedProjectId) {
    els.runList.innerHTML = empty("未选择项目");
    return;
  }
  if (!state.runs.length) {
    els.runList.innerHTML = empty("暂无执行记录");
    return;
  }
  els.runList.innerHTML = state.runs.map((run) => {
    const passed = run.status === "passed";
    return `
      <article class="run-item">
        <div class="run-head">
          <div>
            <h3>执行 #${run.id}</h3>
            <div class="meta">${formatDate(run.started_at)}，总数 ${run.total}，通过 ${run.passed}，失败 ${run.failed}</div>
          </div>
          <div class="run-actions">
            ${badge(passed ? "通过" : "失败", passed ? "success" : "failed")}
            <a class="secondary" href="/projects/${state.selectedProjectId}/runs/${run.id}/report" target="_blank">打开报告</a>
          </div>
        </div>
      </article>
    `;
  }).join("");
}

async function createDemoProject() {
  const project = await api("/projects", {
    method: "POST",
    body: JSON.stringify({
      name: `演示项目 ${new Date().toLocaleTimeString("zh-CN", { hour12: false })}`,
      description: "登录接口与下单接口自动化测试",
    }),
  });

  const login = await api(`/projects/${project.id}/endpoints`, {
    method: "POST",
    body: JSON.stringify({
      name: "用户登录",
      method: "POST",
      url: "http://127.0.0.1:8000/demo-target/login",
      headers: { "Content-Type": "application/json" },
      body: { username: "demo", password: "123456" },
      expected_status: 200,
    }),
  });

  const order = await api(`/projects/${project.id}/endpoints`, {
    method: "POST",
    body: JSON.stringify({
      name: "创建订单",
      method: "POST",
      url: "http://127.0.0.1:8000/demo-target/orders",
      headers: { "Content-Type": "application/json" },
      body: { product_id: 1, quantity: 2 },
      expected_status: 200,
    }),
  });

  await api(`/endpoints/${login.id}/cases`, {
    method: "POST",
    body: JSON.stringify({
      title: "登录成功",
      category: "normal",
      request_body: { username: "demo", password: "123456" },
      expected_status: 200,
      expected_contains: "demo-token",
      reason: "验证正确账号密码可登录。",
    }),
  });
  await api(`/endpoints/${login.id}/cases`, {
    method: "POST",
    body: JSON.stringify({
      title: "密码错误",
      category: "auth",
      request_body: { username: "demo", password: "wrong" },
      expected_status: 401,
      reason: "验证错误密码不可登录。",
    }),
  });
  await api(`/endpoints/${order.id}/cases`, {
    method: "POST",
    body: JSON.stringify({
      title: "下单数量越界",
      category: "boundary",
      request_body: { product_id: 1, quantity: 0 },
      expected_status: 400,
      reason: "验证数量边界校验。",
    }),
  });

  await loadProjects();
  await selectProject(project.id);
  toast("演示项目已生成");
}

els.projectForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  try {
    const project = await api("/projects", {
      method: "POST",
      body: JSON.stringify({
        name: form.get("name"),
        description: form.get("description"),
      }),
    });
    event.currentTarget.reset();
    await loadProjects();
    await selectProject(project.id);
    toast("项目已创建");
  } catch (error) {
    toast(error.message);
  }
});

els.endpointForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  try {
    const endpoint = await api(`/projects/${state.selectedProjectId}/endpoints`, {
      method: "POST",
      body: JSON.stringify({
        name: form.get("name"),
        method: form.get("method"),
        url: form.get("url"),
        headers: parseJson(form.get("headers")),
        body: parseJson(form.get("body")),
        expected_status: Number(form.get("expected_status")),
      }),
    });
    await loadEndpoints();
    await selectEndpoint(endpoint.id);
    toast("接口已保存");
  } catch (error) {
    toast(error.message);
  }
});

els.generateForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  try {
    const requirement = encodeURIComponent(form.get("requirement"));
    await api(`/endpoints/${state.selectedEndpointId}/cases/generate?requirement=${requirement}`, { method: "POST" });
    await loadCases();
    await loadStats();
    toast("用例已生成");
  } catch (error) {
    toast(error.message);
  }
});

els.caseForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  try {
    await api(`/endpoints/${state.selectedEndpointId}/cases`, {
      method: "POST",
      body: JSON.stringify({
        title: form.get("title"),
        category: form.get("category"),
        request_body: parseJson(form.get("request_body")),
        expected_status: form.get("expected_status") ? Number(form.get("expected_status")) : null,
        expected_contains: form.get("expected_contains") || null,
        reason: form.get("reason"),
      }),
    });
    await loadCases();
    await loadStats();
    toast("用例已保存");
  } catch (error) {
    toast(error.message);
  }
});

els.projectList.addEventListener("click", async (event) => {
  const item = event.target.closest("[data-project-id]");
  if (!item) return;
  await selectProject(Number(item.dataset.projectId));
});

els.endpointList.addEventListener("click", async (event) => {
  const selectButton = event.target.closest(".select-endpoint");
  const deleteButton = event.target.closest(".delete-endpoint");
  if (selectButton) {
    await selectEndpoint(Number(selectButton.dataset.endpointId));
  }
  if (deleteButton) {
    const endpointId = Number(deleteButton.dataset.endpointId);
    await api(`/projects/${state.selectedProjectId}/endpoints/${endpointId}`, { method: "DELETE" });
    if (state.selectedEndpointId === endpointId) {
      state.selectedEndpointId = null;
      state.cases = [];
    }
    await loadEndpoints();
    renderCases();
    await loadStats();
    toast("接口已删除");
  }
});

els.caseList.addEventListener("click", async (event) => {
  const button = event.target.closest(".delete-case");
  if (!button) return;
  await api(`/endpoints/${state.selectedEndpointId}/cases/${button.dataset.caseId}`, { method: "DELETE" });
  await loadCases();
  await loadStats();
  toast("用例已删除");
});

els.runProjectBtn.addEventListener("click", async () => {
  if (!state.selectedProjectId) return;
  try {
    els.runProjectBtn.disabled = true;
    els.runProjectBtn.textContent = "执行中";
    await api(`/projects/${state.selectedProjectId}/runs`, { method: "POST" });
    await loadRuns();
    await loadStats();
    toast("执行完成");
  } catch (error) {
    toast(error.message);
  } finally {
    els.runProjectBtn.textContent = "执行项目";
    els.runProjectBtn.disabled = false;
  }
});

els.refreshProjectsBtn.addEventListener("click", async () => {
  await loadProjects();
  toast("已刷新");
});

els.demoProjectBtn.addEventListener("click", async () => {
  try {
    await createDemoProject();
  } catch (error) {
    toast(error.message);
  }
});

loadProjects().catch((error) => toast(error.message));
