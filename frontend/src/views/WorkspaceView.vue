<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Check, Cpu, Delete, Edit, Plus, Setting } from '@element-plus/icons-vue'
import client, { errorMessage } from '../api/client'
import type { ApiEndpoint, Project, TestCase, TestEnvironment } from '../types'

interface AssertionDraft {
  type: string
  operator: string
  target: string
  expected: string
  schemaText: string
}

interface ExtractorDraft {
  name: string
  expression: string
}

const projects = ref<Project[]>([])
const environments = ref<TestEnvironment[]>([])
const endpoints = ref<ApiEndpoint[]>([])
const cases = ref<TestCase[]>([])
const projectId = ref<number | null>(null)
const endpointId = ref<number | null>(null)
const loading = ref(false)
const endpointDialog = ref(false)
const environmentDialog = ref(false)
const editingEnvironmentId = ref<number | null>(null)
const caseDialog = ref(false)
const editingCaseId = ref<number | null>(null)
const aiDialog = ref(false)
const endpointForm = reactive({ name: '', method: 'POST', url: '', expected_status: 200, headersText: '{"Content-Type":"application/json"}', bodyText: '{}' })
const environmentForm = reactive({ name: '', base_url: '', variablesText: '{}', is_active: false })
const caseForm = reactive({
  title: '',
  category: 'normal',
  expected_status: 200,
  headersText: '{}',
  bodyText: '{}',
  reason: '',
  assertions: [] as AssertionDraft[],
  extractors: [] as ExtractorDraft[],
})
const aiForm = reactive({ requirement: '', use_ai: true })

const assertionTypes = [
  { label: '状态码', value: 'status' },
  { label: 'JSONPath', value: 'jsonpath' },
  { label: '响应头', value: 'header' },
  { label: '响应时间', value: 'response_time' },
  { label: 'JSON Schema', value: 'json_schema' },
  { label: '正文包含', value: 'body_contains' },
]
const operatorOptions = [
  { label: '等于', value: 'eq' }, { label: '不等于', value: 'ne' },
  { label: '包含', value: 'contains' }, { label: '不包含', value: 'not_contains' },
  { label: '大于', value: 'gt' }, { label: '大于等于', value: 'gte' },
  { label: '小于', value: 'lt' }, { label: '小于等于', value: 'lte' },
  { label: '存在', value: 'exists' }, { label: '不存在', value: 'not_exists' },
]

function parseObject(value: string) {
  const result = JSON.parse(value || '{}')
  if (!result || Array.isArray(result) || typeof result !== 'object') throw new Error('JSON 必须是对象')
  return result
}

function categoryLabel(category: string) {
  return { normal: '正常', exception: '异常', boundary: '边界', auth: '鉴权' }[category] || category
}

function resetEnvironmentForm() {
  editingEnvironmentId.value = null
  Object.assign(environmentForm, { name: '', base_url: '', variablesText: '{}', is_active: environments.value.length === 0 })
}

function openEnvironmentDialog(item?: TestEnvironment) {
  resetEnvironmentForm()
  if (item) {
    editingEnvironmentId.value = item.id
    Object.assign(environmentForm, {
      name: item.name,
      base_url: item.base_url,
      variablesText: JSON.stringify(item.variables, null, 2),
      is_active: item.is_active,
    })
  }
  environmentDialog.value = true
}

function resetCaseForm() {
  editingCaseId.value = null
  Object.assign(caseForm, {
    title: '', category: 'normal', expected_status: 200, headersText: '{}', bodyText: '{}', reason: '',
    assertions: [{ type: 'status', operator: 'eq', target: '', expected: '200', schemaText: '{}' }],
    extractors: [],
  })
}

function addAssertion() {
  caseForm.assertions.push({ type: 'jsonpath', operator: 'eq', target: '$.', expected: '', schemaText: '{\n  "type": "object"\n}' })
}

function onAssertionTypeChange(rule: AssertionDraft) {
  if (rule.type === 'status') { rule.operator = 'eq'; rule.expected = '200'; rule.target = '' }
  if (rule.type === 'response_time') { rule.operator = 'lte'; rule.expected = '2000'; rule.target = '' }
  if (rule.type === 'body_contains') { rule.operator = 'contains'; rule.target = '' }
  if (rule.type === 'json_schema') { rule.operator = ''; rule.target = '' }
}

async function loadProjects() {
  projects.value = (await client.get<Project[]>('/projects')).data
  if (!projectId.value && projects.value.length) projectId.value = projects.value[0].id
}

async function loadEnvironments() {
  environments.value = projectId.value ? (await client.get<TestEnvironment[]>(`/projects/${projectId.value}/environments`)).data : []
}

async function loadEndpoints() {
  endpoints.value = projectId.value ? (await client.get<ApiEndpoint[]>(`/projects/${projectId.value}/endpoints`)).data : []
  if (!endpoints.value.some((item) => item.id === endpointId.value)) endpointId.value = endpoints.value[0]?.id || null
}

async function loadCases() {
  cases.value = endpointId.value ? (await client.get<TestCase[]>(`/endpoints/${endpointId.value}/cases`)).data : []
}

function selectEndpoint(row: ApiEndpoint | null) {
  endpointId.value = row?.id || null
}

async function saveEnvironment() {
  if (!projectId.value || !environmentForm.name.trim()) return ElMessage.warning('请填写环境名称')
  try {
    const payload = {
      name: environmentForm.name,
      base_url: environmentForm.base_url,
      variables: parseObject(environmentForm.variablesText),
      is_active: environmentForm.is_active,
    }
    if (editingEnvironmentId.value) {
      await client.put(`/projects/${projectId.value}/environments/${editingEnvironmentId.value}`, payload)
    } else {
      await client.post(`/projects/${projectId.value}/environments`, payload)
    }
    environmentDialog.value = false
    ElMessage.success('环境已保存')
    await loadEnvironments()
  } catch (error) { ElMessage.error(errorMessage(error)) }
}

async function activateEnvironment(item: TestEnvironment) {
  if (!projectId.value || item.is_active) return
  await client.put(`/projects/${projectId.value}/environments/${item.id}`, { is_active: true })
  ElMessage.success(`已切换到${item.name}`)
  await loadEnvironments()
}

async function deleteEnvironment(item: TestEnvironment) {
  if (!projectId.value) return
  await ElMessageBox.confirm(`确认删除环境“${item.name}”？`, '删除环境', { type: 'warning' })
  await client.delete(`/projects/${projectId.value}/environments/${item.id}`)
  await loadEnvironments()
}

async function createEndpoint() {
  if (!projectId.value) return
  try {
    await client.post(`/projects/${projectId.value}/endpoints`, {
      name: endpointForm.name, method: endpointForm.method, url: endpointForm.url,
      expected_status: endpointForm.expected_status,
      headers: parseObject(endpointForm.headersText), body: parseObject(endpointForm.bodyText),
    })
    endpointDialog.value = false
    ElMessage.success('接口已保存')
    await loadEndpoints()
  } catch (error) { ElMessage.error(errorMessage(error)) }
}

function buildAssertions() {
  return caseForm.assertions.map((rule) => {
    if (rule.type === 'json_schema') return { type: rule.type, schema: parseObject(rule.schemaText) }
    let expected: unknown = rule.expected
    if (['status', 'response_time'].includes(rule.type)) expected = Number(rule.expected)
    else {
      try { expected = JSON.parse(rule.expected) }
      catch { expected = rule.expected }
    }
    const result: Record<string, unknown> = { type: rule.type, operator: rule.operator, expected }
    if (rule.target) result.target = rule.target
    if (['exists', 'not_exists'].includes(rule.operator)) delete result.expected
    return result
  })
}

async function createCase() {
  if (!endpointId.value) return
  try {
    const payload = {
      title: caseForm.title, category: caseForm.category,
      request_headers: parseObject(caseForm.headersText), request_body: parseObject(caseForm.bodyText),
      expected_status: caseForm.expected_status, expected_contains: null,
      assertions: buildAssertions(), extractors: caseForm.extractors, reason: caseForm.reason,
    }
    if (editingCaseId.value) await client.put(`/endpoints/${endpointId.value}/cases/${editingCaseId.value}`, payload)
    else await client.post(`/endpoints/${endpointId.value}/cases`, payload)
    caseDialog.value = false
    ElMessage.success('用例已保存')
    await loadCases()
  } catch (error) { ElMessage.error(errorMessage(error)) }
}

async function generateCases() {
  if (!endpointId.value || aiForm.requirement.length < 4) return ElMessage.warning('请填写需求描述')
  loading.value = true
  try {
    await client.post(`/endpoints/${endpointId.value}/cases/generate`, aiForm)
    aiDialog.value = false
    ElMessage.success(aiForm.use_ai ? '用例生成完成' : '规则用例生成完成')
    await loadCases()
  } catch (error) { ElMessage.error(errorMessage(error)) }
  finally { loading.value = false }
}

async function deleteEndpoint(item: ApiEndpoint) {
  if (!projectId.value) return
  await ElMessageBox.confirm(`确认删除接口“${item.name}”？`, '删除接口', { type: 'warning' })
  await client.delete(`/projects/${projectId.value}/endpoints/${item.id}`)
  await loadEndpoints(); await loadCases()
}

async function deleteCase(item: TestCase) {
  if (!endpointId.value) return
  await client.delete(`/endpoints/${endpointId.value}/cases/${item.id}`)
  await loadCases()
}

function openCaseDialog(item?: TestCase) {
  resetCaseForm()
  if (item) {
    editingCaseId.value = item.id
    Object.assign(caseForm, {
      title: item.title,
      category: item.category,
      expected_status: item.expected_status || 200,
      headersText: JSON.stringify(item.request_headers, null, 2),
      bodyText: JSON.stringify(item.request_body, null, 2),
      reason: item.reason,
      assertions: item.assertions.map((rule) => ({
        type: rule.type,
        operator: rule.operator || '',
        target: rule.target || '',
        expected: typeof rule.expected === 'string' ? rule.expected : JSON.stringify(rule.expected ?? ''),
        schemaText: JSON.stringify(rule.schema || {}, null, 2),
      })),
      extractors: item.extractors.map((rule) => ({ ...rule })),
    })
  }
  caseDialog.value = true
}

watch(projectId, async () => { endpointId.value = null; await Promise.all([loadEnvironments(), loadEndpoints()]); await loadCases() })
watch(endpointId, loadCases)
onMounted(async () => { try { await loadProjects(); await Promise.all([loadEnvironments(), loadEndpoints()]); await loadCases() } catch (error) { ElMessage.error(errorMessage(error)) } })
</script>

<template>
  <div v-loading="loading">
    <div class="page-heading"><div><h2>接口与用例</h2><p>配置测试环境、接口和可重复执行的验证规则</p></div></div>

    <section class="surface environment-section">
      <div class="section-title-row">
        <div><h3>项目环境</h3><p>请求中的 <code v-text="'{{变量名}}'" /> 会在执行时替换为当前环境变量</p></div>
        <div class="toolbar compact-toolbar">
          <el-select v-model="projectId" placeholder="选择项目" style="width: 240px"><el-option v-for="item in projects" :key="item.id" :label="item.name" :value="item.id" /></el-select>
          <el-button :icon="Plus" :disabled="!projectId" @click="openEnvironmentDialog()">新增环境</el-button>
        </div>
      </div>
      <el-table :data="environments" empty-text="暂无环境，可先新增本地或测试环境">
        <el-table-column label="状态" width="80"><template #default="scope"><el-tag v-if="scope.row.is_active" type="success" size="small">当前</el-tag><span v-else class="muted-text">待用</span></template></el-table-column>
        <el-table-column prop="name" label="环境名称" min-width="150" />
        <el-table-column prop="base_url" label="基础地址" min-width="240" show-overflow-tooltip />
        <el-table-column label="变量" min-width="180"><template #default="scope"><span class="code-summary">{{ Object.keys(scope.row.variables).join('、') || '无' }}</span></template></el-table-column>
        <el-table-column label="操作" width="172" align="right"><template #default="scope">
          <el-tooltip content="设为当前环境"><el-button :icon="Check" circle size="small" :disabled="scope.row.is_active" @click="activateEnvironment(scope.row)" /></el-tooltip>
          <el-tooltip content="编辑环境"><el-button :icon="Edit" circle size="small" @click="openEnvironmentDialog(scope.row)" /></el-tooltip>
          <el-tooltip content="删除环境"><el-button :icon="Delete" circle size="small" type="danger" @click="deleteEnvironment(scope.row)" /></el-tooltip>
        </template></el-table-column>
      </el-table>
    </section>

    <div class="toolbar surface workspace-toolbar">
      <el-button type="primary" :icon="Plus" :disabled="!projectId" @click="endpointDialog = true">新增接口</el-button>
      <el-button :icon="Cpu" :disabled="!endpointId" @click="aiDialog = true">生成测试用例</el-button>
      <el-button :icon="Setting" :disabled="!endpointId" @click="openCaseDialog">配置测试用例</el-button>
    </div>
    <div class="section-grid">
      <section class="surface">
        <h3>接口列表</h3>
        <el-table :data="endpoints" highlight-current-row empty-text="暂无接口" @current-change="selectEndpoint">
          <el-table-column prop="method" label="方法" width="78" />
          <el-table-column prop="name" label="名称" min-width="130" />
          <el-table-column prop="url" label="地址" min-width="210" show-overflow-tooltip />
          <el-table-column label="操作" width="58"><template #default="scope"><el-button :icon="Delete" circle size="small" type="danger" @click.stop="deleteEndpoint(scope.row)" /></template></el-table-column>
        </el-table>
      </section>
      <section class="surface">
        <h3>测试用例</h3>
        <el-table :data="cases" empty-text="请选择接口或新增用例">
          <el-table-column prop="title" label="用例" min-width="170" />
          <el-table-column label="类型" width="76"><template #default="scope">{{ categoryLabel(scope.row.category) }}</template></el-table-column>
          <el-table-column label="规则" width="82"><template #default="scope">{{ scope.row.assertions.length }} 断言</template></el-table-column>
          <el-table-column label="提取" width="72"><template #default="scope">{{ scope.row.extractors.length }}</template></el-table-column>
          <el-table-column label="来源" width="68"><template #default="scope"><el-tag size="small" :type="scope.row.created_by_ai ? 'primary' : 'info'">{{ scope.row.created_by_ai ? 'GPT' : '手工' }}</el-tag></template></el-table-column>
          <el-table-column label="操作" width="98"><template #default="scope"><el-button :icon="Edit" circle size="small" @click="openCaseDialog(scope.row)" /><el-button :icon="Delete" circle size="small" type="danger" @click="deleteCase(scope.row)" /></template></el-table-column>
        </el-table>
      </section>
    </div>

    <el-dialog v-model="environmentDialog" :title="editingEnvironmentId ? '编辑环境' : '新增环境'" width="620px">
      <el-form label-position="top">
        <el-form-item label="环境名称"><el-input v-model="environmentForm.name" placeholder="例如：本地环境、测试环境" /></el-form-item>
        <el-form-item label="基础地址"><el-input v-model="environmentForm.base_url" placeholder="http://127.0.0.1:8000" /></el-form-item>
        <el-form-item label="环境变量 JSON" class="code-input"><el-input v-model="environmentForm.variablesText" type="textarea" :rows="7" placeholder='{"username":"demo"}' /></el-form-item>
        <el-form-item><el-checkbox v-model="environmentForm.is_active">保存后设为当前环境</el-checkbox></el-form-item>
      </el-form>
      <template #footer><el-button @click="environmentDialog = false">取消</el-button><el-button type="primary" @click="saveEnvironment">保存</el-button></template>
    </el-dialog>

    <el-dialog v-model="endpointDialog" title="新增接口" width="640px">
      <el-form label-position="top">
        <el-row :gutter="12"><el-col :span="16"><el-form-item label="接口名称"><el-input v-model="endpointForm.name" /></el-form-item></el-col><el-col :span="8"><el-form-item label="请求方法"><el-select v-model="endpointForm.method" style="width: 100%"><el-option v-for="m in ['GET','POST','PUT','PATCH','DELETE']" :key="m" :label="m" :value="m" /></el-select></el-form-item></el-col></el-row>
        <el-form-item label="请求地址"><el-input v-model="endpointForm.url" placeholder="/demo-target/login 或完整 URL" /></el-form-item>
        <el-form-item label="预期状态码"><el-input-number v-model="endpointForm.expected_status" :min="100" :max="599" /></el-form-item>
        <el-form-item label="请求头 JSON" class="code-input"><el-input v-model="endpointForm.headersText" type="textarea" :rows="4" /></el-form-item>
        <el-form-item label="请求体 JSON" class="code-input"><el-input v-model="endpointForm.bodyText" type="textarea" :rows="5" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="endpointDialog = false">取消</el-button><el-button type="primary" @click="createEndpoint">保存</el-button></template>
    </el-dialog>

    <el-dialog v-model="caseDialog" :title="editingCaseId ? '编辑测试用例' : '配置测试用例'" width="860px" top="5vh">
      <el-form label-position="top">
        <el-row :gutter="12"><el-col :span="12"><el-form-item label="用例标题"><el-input v-model="caseForm.title" /></el-form-item></el-col><el-col :span="6"><el-form-item label="用例类型"><el-select v-model="caseForm.category" style="width: 100%"><el-option label="正常" value="normal" /><el-option label="异常" value="exception" /><el-option label="边界" value="boundary" /><el-option label="鉴权" value="auth" /></el-select></el-form-item></el-col><el-col :span="6"><el-form-item label="默认状态码"><el-input-number v-model="caseForm.expected_status" :min="100" :max="599" style="width: 100%" /></el-form-item></el-col></el-row>
        <el-row :gutter="12"><el-col :span="12"><el-form-item label="请求头 JSON" class="code-input"><el-input v-model="caseForm.headersText" type="textarea" :rows="5" /></el-form-item></el-col><el-col :span="12"><el-form-item label="请求体 JSON" class="code-input"><el-input v-model="caseForm.bodyText" type="textarea" :rows="5" /></el-form-item></el-col></el-row>

        <div class="rule-heading"><strong>断言规则</strong><el-button :icon="Plus" size="small" @click="addAssertion">添加断言</el-button></div>
        <div v-for="(rule, index) in caseForm.assertions" :key="index" class="rule-row">
          <el-select v-model="rule.type" style="width: 130px" @change="onAssertionTypeChange(rule)"><el-option v-for="item in assertionTypes" :key="item.value" :label="item.label" :value="item.value" /></el-select>
          <template v-if="rule.type === 'json_schema'"><el-input v-model="rule.schemaText" type="textarea" :rows="3" class="schema-editor code-input" /></template>
          <template v-else>
            <el-input v-if="['jsonpath','header'].includes(rule.type)" v-model="rule.target" class="rule-target" :placeholder="rule.type === 'jsonpath' ? '$.data.id' : 'Content-Type'" />
            <el-select v-model="rule.operator" style="width: 116px"><el-option v-for="item in operatorOptions" :key="item.value" :label="item.label" :value="item.value" /></el-select>
            <el-input v-if="!['exists','not_exists'].includes(rule.operator)" v-model="rule.expected" class="rule-expected" placeholder="期望值，可使用 {{变量名}}" />
          </template>
          <el-button :icon="Delete" circle type="danger" size="small" @click="caseForm.assertions.splice(index, 1)" />
        </div>

        <div class="rule-heading"><strong>响应提取</strong><el-button :icon="Plus" size="small" @click="caseForm.extractors.push({ name: '', expression: '$.' })">添加提取器</el-button></div>
        <div v-for="(extractor, index) in caseForm.extractors" :key="index" class="rule-row">
          <el-input v-model="extractor.name" style="width: 180px" placeholder="变量名，例如 token" />
          <el-input v-model="extractor.expression" class="rule-expected" placeholder="JSONPath，例如 $.token" />
          <el-button :icon="Delete" circle type="danger" size="small" @click="caseForm.extractors.splice(index, 1)" />
        </div>
        <el-form-item label="设计原因" class="reason-field"><el-input v-model="caseForm.reason" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="caseDialog = false">取消</el-button><el-button type="primary" @click="createCase">保存用例</el-button></template>
    </el-dialog>

    <el-dialog v-model="aiDialog" title="生成测试用例" width="560px">
      <el-form label-position="top"><el-form-item label="需求描述"><el-input v-model="aiForm.requirement" type="textarea" :rows="5" placeholder="描述业务规则、必填字段、鉴权和边界要求" /></el-form-item><el-form-item><el-checkbox v-model="aiForm.use_ai">优先使用 GPT，失败时自动回退规则生成器</el-checkbox></el-form-item></el-form>
      <template #footer><el-button @click="aiDialog = false">取消</el-button><el-button type="primary" @click="generateCases">生成并保存</el-button></template>
    </el-dialog>
  </div>
</template>
