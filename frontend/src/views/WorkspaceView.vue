<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Cpu, Plus } from '@element-plus/icons-vue'
import client, { errorMessage } from '../api/client'
import type { ApiEndpoint, Project, TestCase } from '../types'

const projects = ref<Project[]>([])
const endpoints = ref<ApiEndpoint[]>([])
const cases = ref<TestCase[]>([])
const projectId = ref<number | null>(null)
const endpointId = ref<number | null>(null)
const loading = ref(false)
const endpointDialog = ref(false)
const caseDialog = ref(false)
const aiDialog = ref(false)
const endpointForm = reactive({ name: '', method: 'POST', url: '', expected_status: 200, headersText: '{"Content-Type":"application/json"}', bodyText: '{}' })
const caseForm = reactive({ title: '', category: 'normal', expected_status: 200, expected_contains: '', bodyText: '{}', reason: '' })
const aiForm = reactive({ requirement: '', use_ai: true })

function parseObject(value: string) {
  const result = JSON.parse(value || '{}')
  if (!result || Array.isArray(result) || typeof result !== 'object') throw new Error('JSON 必须是对象')
  return result
}

async function loadProjects() {
  projects.value = (await client.get<Project[]>('/projects')).data
  if (!projectId.value && projects.value.length) projectId.value = projects.value[0].id
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

async function createEndpoint() {
  if (!projectId.value) return
  try {
    await client.post(`/projects/${projectId.value}/endpoints`, {
      name: endpointForm.name,
      method: endpointForm.method,
      url: endpointForm.url,
      expected_status: endpointForm.expected_status,
      headers: parseObject(endpointForm.headersText),
      body: parseObject(endpointForm.bodyText),
    })
    endpointDialog.value = false
    ElMessage.success('接口已保存')
    await loadEndpoints()
  } catch (error) { ElMessage.error(errorMessage(error)) }
}

async function createCase() {
  if (!endpointId.value) return
  try {
    await client.post(`/endpoints/${endpointId.value}/cases`, {
      title: caseForm.title,
      category: caseForm.category,
      request_headers: {},
      request_body: parseObject(caseForm.bodyText),
      expected_status: caseForm.expected_status,
      expected_contains: caseForm.expected_contains || null,
      reason: caseForm.reason,
    })
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

watch(projectId, async () => { endpointId.value = null; await loadEndpoints(); await loadCases() })
watch(endpointId, loadCases)
onMounted(async () => { try { await loadProjects(); await loadEndpoints(); await loadCases() } catch (error) { ElMessage.error(errorMessage(error)) } })
</script>

<template>
  <div v-loading="loading">
    <div class="page-heading"><div><h2>接口与用例</h2><p>维护待测接口，并设计可重复执行的测试场景</p></div></div>
    <div class="toolbar surface">
      <el-select v-model="projectId" placeholder="选择项目" style="width: 260px"><el-option v-for="item in projects" :key="item.id" :label="item.name" :value="item.id" /></el-select>
      <el-button type="primary" :icon="Plus" :disabled="!projectId" @click="endpointDialog = true">新增接口</el-button>
      <el-button :icon="Cpu" :disabled="!endpointId" @click="aiDialog = true">生成测试用例</el-button>
      <el-button :disabled="!endpointId" @click="caseDialog = true">手工新增用例</el-button>
    </div>
    <div class="section-grid">
      <section class="surface">
        <h3>接口列表</h3>
        <el-table :data="endpoints" highlight-current-row empty-text="暂无接口" @current-change="selectEndpoint">
          <el-table-column prop="method" label="方法" width="78" />
          <el-table-column prop="name" label="名称" min-width="130" />
          <el-table-column prop="url" label="地址" min-width="220" show-overflow-tooltip />
          <el-table-column label="操作" width="70"><template #default="scope"><el-button type="danger" link @click.stop="deleteEndpoint(scope.row)">删除</el-button></template></el-table-column>
        </el-table>
      </section>
      <section class="surface">
        <h3>测试用例</h3>
        <el-table :data="cases" empty-text="请选择接口或新增用例">
          <el-table-column prop="title" label="用例" min-width="170" />
          <el-table-column prop="category" label="类型" width="85" />
          <el-table-column prop="expected_status" label="状态码" width="85" />
          <el-table-column label="来源" width="75"><template #default="scope"><el-tag size="small" :type="scope.row.created_by_ai ? 'primary' : 'info'">{{ scope.row.created_by_ai ? 'GPT' : '手工' }}</el-tag></template></el-table-column>
          <el-table-column label="操作" width="70"><template #default="scope"><el-button type="danger" link @click="deleteCase(scope.row)">删除</el-button></template></el-table-column>
        </el-table>
      </section>
    </div>

    <el-dialog v-model="endpointDialog" title="新增接口" width="640px">
      <el-form label-position="top">
        <el-row :gutter="12"><el-col :span="16"><el-form-item label="接口名称"><el-input v-model="endpointForm.name" /></el-form-item></el-col><el-col :span="8"><el-form-item label="请求方法"><el-select v-model="endpointForm.method" style="width: 100%"><el-option v-for="m in ['GET','POST','PUT','PATCH','DELETE']" :key="m" :label="m" :value="m" /></el-select></el-form-item></el-col></el-row>
        <el-form-item label="请求地址"><el-input v-model="endpointForm.url" placeholder="http://127.0.0.1:8000/demo-target/login" /></el-form-item>
        <el-form-item label="预期状态码"><el-input-number v-model="endpointForm.expected_status" :min="100" :max="599" /></el-form-item>
        <el-form-item label="Headers JSON" class="code-input"><el-input v-model="endpointForm.headersText" type="textarea" :rows="4" /></el-form-item>
        <el-form-item label="Body JSON" class="code-input"><el-input v-model="endpointForm.bodyText" type="textarea" :rows="5" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="endpointDialog = false">取消</el-button><el-button type="primary" @click="createEndpoint">保存</el-button></template>
    </el-dialog>

    <el-dialog v-model="caseDialog" title="新增测试用例" width="600px">
      <el-form label-position="top">
        <el-form-item label="用例标题"><el-input v-model="caseForm.title" /></el-form-item>
        <el-row :gutter="12"><el-col :span="12"><el-form-item label="用例类型"><el-select v-model="caseForm.category" style="width: 100%"><el-option label="正常" value="normal" /><el-option label="异常" value="exception" /><el-option label="边界" value="boundary" /><el-option label="鉴权" value="auth" /></el-select></el-form-item></el-col><el-col :span="12"><el-form-item label="预期状态码"><el-input-number v-model="caseForm.expected_status" :min="100" :max="599" /></el-form-item></el-col></el-row>
        <el-form-item label="请求体 JSON" class="code-input"><el-input v-model="caseForm.bodyText" type="textarea" :rows="5" /></el-form-item>
        <el-form-item label="响应包含"><el-input v-model="caseForm.expected_contains" /></el-form-item>
        <el-form-item label="设计原因"><el-input v-model="caseForm.reason" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="caseDialog = false">取消</el-button><el-button type="primary" @click="createCase">保存</el-button></template>
    </el-dialog>

    <el-dialog v-model="aiDialog" title="生成测试用例" width="560px">
      <el-form label-position="top"><el-form-item label="需求描述"><el-input v-model="aiForm.requirement" type="textarea" :rows="5" placeholder="描述业务规则、必填字段、鉴权和边界要求" /></el-form-item><el-form-item><el-checkbox v-model="aiForm.use_ai">优先使用 GPT，失败时自动回退规则生成器</el-checkbox></el-form-item></el-form>
      <template #footer><el-button @click="aiDialog = false">取消</el-button><el-button type="primary" @click="generateCases">生成并保存</el-button></template>
    </el-dialog>
  </div>
</template>
