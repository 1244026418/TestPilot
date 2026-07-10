<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { VideoPlay } from '@element-plus/icons-vue'
import client, { errorMessage } from '../api/client'
import type { Project, TestRun } from '../types'

const projects = ref<Project[]>([])
const runs = ref<TestRun[]>([])
const projectId = ref<number | null>(null)
const running = ref(false)

async function loadRuns() {
  runs.value = projectId.value ? (await client.get<TestRun[]>(`/projects/${projectId.value}/runs`)).data : []
}

async function execute() {
  if (!projectId.value) return
  running.value = true
  try {
    await client.post(`/projects/${projectId.value}/runs`)
    ElMessage.success('测试执行完成')
    await loadRuns()
  } catch (error) { ElMessage.error(errorMessage(error)) }
  finally { running.value = false }
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

watch(projectId, loadRuns)
onMounted(async () => {
  try {
    projects.value = (await client.get<Project[]>('/projects')).data
    projectId.value = projects.value[0]?.id || null
    await loadRuns()
  } catch (error) { ElMessage.error(errorMessage(error)) }
})
</script>

<template>
  <div>
    <div class="page-heading"><div><h2>执行记录</h2><p>运行项目下全部用例并查看历史测试报告</p></div></div>
    <div class="surface">
      <div class="toolbar"><el-select v-model="projectId" placeholder="选择项目" style="width: 280px"><el-option v-for="item in projects" :key="item.id" :label="item.name" :value="item.id" /></el-select><el-button type="primary" :icon="VideoPlay" :loading="running" :disabled="!projectId" @click="execute">执行项目</el-button></div>
      <el-table :data="runs" stripe empty-text="暂无执行记录">
        <el-table-column prop="id" label="批次" width="80" />
        <el-table-column label="状态" width="100"><template #default="scope"><el-tag :type="scope.row.status === 'passed' ? 'success' : 'danger'">{{ scope.row.status === 'passed' ? '通过' : '失败' }}</el-tag></template></el-table-column>
        <el-table-column prop="total" label="总数" width="90" />
        <el-table-column prop="passed" label="通过" width="90" />
        <el-table-column prop="failed" label="失败" width="90" />
        <el-table-column prop="started_at" label="开始时间" min-width="190" />
        <el-table-column label="报告" width="100"><template #default="scope"><el-button type="primary" link @click="openReport(scope.row)">查看报告</el-button></template></el-table-column>
      </el-table>
    </div>
  </div>
</template>
