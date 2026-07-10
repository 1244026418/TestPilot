<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import client, { errorMessage } from '../api/client'
import type { DashboardStats } from '../types'

const loading = ref(false)
const stats = ref<DashboardStats>({ projects: 0, endpoints: 0, cases: 0, runs: 0, passed_runs: 0, failed_runs: 0, latest_run: null })

async function load() {
  loading.value = true
  try {
    stats.value = (await client.get<DashboardStats>('/dashboard/stats')).data
  } catch (error) {
    ElMessage.error(errorMessage(error))
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div v-loading="loading">
    <div class="page-heading"><div><h2>工作台</h2><p>查看当前接口测试资产和最近一次执行状态</p></div><el-button @click="load">刷新数据</el-button></div>
    <section class="metric-grid">
      <article class="metric-item"><span>测试项目</span><strong>{{ stats.projects }}</strong></article>
      <article class="metric-item"><span>接口数量</span><strong>{{ stats.endpoints }}</strong></article>
      <article class="metric-item"><span>测试用例</span><strong>{{ stats.cases }}</strong></article>
      <article class="metric-item"><span>执行次数</span><strong>{{ stats.runs }}</strong></article>
    </section>
    <section class="section-grid">
      <div class="surface">
        <h3>执行质量</h3>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="通过批次"><span class="status-passed">{{ stats.passed_runs }}</span></el-descriptions-item>
          <el-descriptions-item label="失败批次"><span class="status-failed">{{ stats.failed_runs }}</span></el-descriptions-item>
        </el-descriptions>
      </div>
      <div class="surface">
        <h3>最近执行</h3>
        <el-empty v-if="!stats.latest_run" description="暂无执行记录" :image-size="68" />
        <el-descriptions v-else :column="2" border>
          <el-descriptions-item label="状态">{{ stats.latest_run.status === 'passed' ? '通过' : '失败' }}</el-descriptions-item>
          <el-descriptions-item label="用例数">{{ stats.latest_run.total }}</el-descriptions-item>
          <el-descriptions-item label="通过">{{ stats.latest_run.passed }}</el-descriptions-item>
          <el-descriptions-item label="失败">{{ stats.latest_run.failed }}</el-descriptions-item>
        </el-descriptions>
      </div>
    </section>
  </div>
</template>
