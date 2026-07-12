<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Document, VideoPlay } from '@element-plus/icons-vue'
import client, { errorMessage } from '../api/client'
import type { Project, TestEnvironment, TestResult, TestRun } from '../types'

const projects = ref<Project[]>([])
const environments = ref<TestEnvironment[]>([])
const runs = ref<TestRun[]>([])
const projectId = ref<number | null>(null)
const environmentId = ref<number | null>(null)
const running = ref(false)
const detailVisible = ref(false)
const selectedRun = ref<TestRun | null>(null)

const selectedResults = computed(() => selectedRun.value?.results || [])

function assertionTypeLabel(type: string) {
  return {
    status: '状态码', body_contains: '正文包含', jsonpath: 'JSONPath', header: '响应头',
    response_time: '响应时间', json_schema: 'JSON Schema', extractor: '变量提取',
  }[type] || type
}

function displayValue(value: unknown) {
  if (value === null || value === undefined || value === '') return '-'
  return typeof value === 'object' ? JSON.stringify(value) : String(value)
}

async function loadEnvironments() {
  environments.value = projectId.value ? (await client.get<TestEnvironment[]>(`/projects/${projectId.value}/environments`)).data : []
  const active = environments.value.find((item) => item.is_active)
  if (!environments.value.some((item) => item.id === environmentId.value)) environmentId.value = active?.id || environments.value[0]?.id || null
}

async function loadRuns() {
  runs.value = projectId.value ? (await client.get<TestRun[]>(`/projects/${projectId.value}/runs`)).data : []
}

async function execute() {
  if (!projectId.value) return
  running.value = true
  try {
    await client.post(`/projects/${projectId.value}/runs`, { environment_id: environmentId.value })
    ElMessage.success('测试执行完成')
    await loadRuns()
  } catch (error) { ElMessage.error(errorMessage(error)) }
  finally { running.value = false }
}

function openDetail(run: TestRun) {
  selectedRun.value = run
  detailVisible.value = true
}

async function openReport(run: TestRun) {
  if (!projectId.value) return
  try {
    const response = await client.get(`/projects/${projectId.value}/runs/${run.id}/report`, { responseType: 'blob' })
    const url = URL.createObjectURL(response.data)
    window.open(url, '_blank')
    window.setTimeout(() => URL.revokeObjectURL(url), 60000)
  } catch (error) { ElMessage.error(errorMessage(error)) }
}

watch(projectId, async () => { await Promise.all([loadEnvironments(), loadRuns()]) })
onMounted(async () => {
  try {
    projects.value = (await client.get<Project[]>('/projects')).data
    projectId.value = projects.value[0]?.id || null
    await Promise.all([loadEnvironments(), loadRuns()])
  } catch (error) { ElMessage.error(errorMessage(error)) }
})
</script>

<template>
  <div>
    <div class="page-heading"><div><h2>执行记录</h2><p>选择环境运行项目，并逐项核对请求、断言和变量提取结果</p></div></div>
    <div class="surface">
      <div class="toolbar run-toolbar">
        <el-select v-model="projectId" placeholder="选择项目" style="width: 260px"><el-option v-for="item in projects" :key="item.id" :label="item.name" :value="item.id" /></el-select>
        <el-select v-model="environmentId" placeholder="使用当前环境" clearable style="width: 220px"><el-option v-for="item in environments" :key="item.id" :label="item.is_active ? `${item.name}（当前）` : item.name" :value="item.id" /></el-select>
        <el-button type="primary" :icon="VideoPlay" :loading="running" :disabled="!projectId" @click="execute">执行项目</el-button>
      </div>
      <el-table :data="runs" stripe empty-text="暂无执行记录">
        <el-table-column prop="id" label="批次" width="72" />
        <el-table-column label="状态" width="90"><template #default="scope"><el-tag :type="scope.row.status === 'passed' ? 'success' : 'danger'">{{ scope.row.status === 'passed' ? '通过' : '失败' }}</el-tag></template></el-table-column>
        <el-table-column prop="environment_name" label="测试环境" min-width="135"><template #default="scope">{{ scope.row.environment_name || '未指定' }}</template></el-table-column>
        <el-table-column prop="total" label="总数" width="72" />
        <el-table-column prop="passed" label="通过" width="72" />
        <el-table-column prop="failed" label="失败" width="72" />
        <el-table-column prop="started_at" label="开始时间" min-width="175" />
        <el-table-column label="操作" width="170" align="right"><template #default="scope">
          <el-button type="primary" link @click="openDetail(scope.row)">执行明细</el-button>
          <el-button :icon="Document" link @click="openReport(scope.row)">报告</el-button>
        </template></el-table-column>
      </el-table>
    </div>

    <el-drawer v-model="detailVisible" title="执行明细" size="72%">
      <div v-if="selectedRun" class="run-summary-strip">
        <span>批次 #{{ selectedRun.id }}</span><span>{{ selectedRun.environment_name || '未指定环境' }}</span>
        <el-tag :type="selectedRun.status === 'passed' ? 'success' : 'danger'">{{ selectedRun.passed }}/{{ selectedRun.total }} 通过</el-tag>
      </div>
      <el-collapse v-if="selectedResults.length" class="result-collapse">
        <el-collapse-item v-for="(result, index) in selectedResults" :key="result.id" :name="result.id">
          <template #title>
            <div class="result-title"><el-tag size="small" :type="result.status === 'passed' ? 'success' : 'danger'">{{ result.status === 'passed' ? '通过' : '失败' }}</el-tag><strong>用例 #{{ result.testcase_id }}</strong><span>{{ result.status_code ?? '-' }} / {{ result.elapsed_ms ?? '-' }} ms</span></div>
          </template>
          <div class="request-meta"><strong>请求地址</strong><code>{{ result.request_url || '-' }}</code></div>
          <el-table :data="result.assertion_results" size="small" border empty-text="无断言明细">
            <el-table-column label="结果" width="72"><template #default="scope"><el-tag size="small" :type="scope.row.passed ? 'success' : 'danger'">{{ scope.row.passed ? '通过' : '失败' }}</el-tag></template></el-table-column>
            <el-table-column label="规则" width="110"><template #default="scope">{{ assertionTypeLabel(scope.row.type) }}</template></el-table-column>
            <el-table-column prop="message" label="检查项" min-width="180" />
            <el-table-column label="期望" min-width="140"><template #default="scope"><code>{{ displayValue(scope.row.expected) }}</code></template></el-table-column>
            <el-table-column label="实际" min-width="140"><template #default="scope"><code>{{ displayValue(scope.row.actual) }}</code></template></el-table-column>
          </el-table>
          <p v-if="result.extracted_variables.length" class="extracted-line">已提取变量：<el-tag v-for="name in result.extracted_variables" :key="name" size="small">{{ name }}</el-tag></p>
          <el-alert v-if="result.error" :title="result.error" type="error" :closable="false" show-icon />
        </el-collapse-item>
      </el-collapse>
      <el-empty v-else description="本批次没有执行结果" />
    </el-drawer>
  </div>
</template>
