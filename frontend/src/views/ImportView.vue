<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import client, { errorMessage } from '../api/client'
import type { Project } from '../types'

const projects = ref<Project[]>([])
const projectId = ref<number | null>(null)
const format = ref<'openapi' | 'postman'>('openapi')
const content = ref('')
const baseUrl = ref('')
const loading = ref(false)

async function readFile(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (file) content.value = await file.text()
}

async function submit() {
  if (!projectId.value) return ElMessage.warning('请选择项目')
  if (!content.value.trim()) return ElMessage.warning('请选择文件或粘贴文档内容')
  loading.value = true
  try {
    const { data } = await client.post(`/import/${format.value}/${projectId.value}`, { content: content.value, base_url: baseUrl.value })
    ElMessage.success(data.message)
  } catch (error) { ElMessage.error(errorMessage(error)) }
  finally { loading.value = false }
}

onMounted(async () => {
  try {
    projects.value = (await client.get<Project[]>('/projects')).data
    projectId.value = projects.value[0]?.id || null
  } catch (error) { ElMessage.error(errorMessage(error)) }
})
</script>

<template>
  <div>
    <div class="page-heading"><div><h2>文档导入</h2><p>从 OpenAPI、Swagger 或 Postman Collection 批量创建接口资产</p></div></div>
    <div class="surface">
      <div class="toolbar">
        <el-select v-model="projectId" placeholder="选择目标项目" style="width: 260px"><el-option v-for="item in projects" :key="item.id" :label="item.name" :value="item.id" /></el-select>
        <el-segmented v-model="format" :options="[{ label: 'OpenAPI / Swagger', value: 'openapi' }, { label: 'Postman Collection', value: 'postman' }]" />
      </div>
      <el-form label-position="top">
        <el-form-item label="接口基础地址"><el-input v-model="baseUrl" placeholder="可选，例如 https://api.example.com" /></el-form-item>
        <el-form-item label="选择 JSON / YAML 文件"><label class="file-picker"><el-icon><UploadFilled /></el-icon><span>选择文档</span><input type="file" accept=".json,.yaml,.yml,application/json" @change="readFile" /></label></el-form-item>
        <el-form-item label="文档内容" class="code-input"><el-input v-model="content" type="textarea" :rows="18" placeholder="也可以直接粘贴 OpenAPI 或 Postman 文档" /></el-form-item>
      </el-form>
      <el-button type="primary" :loading="loading" @click="submit">开始导入</el-button>
    </div>
  </div>
</template>

<style scoped>
.file-picker { width: 100%; min-height: 76px; display: flex; align-items: center; justify-content: center; gap: 8px; border: 1px dashed #aeb8c8; border-radius: 6px; color: #526071; cursor: pointer; }
.file-picker input { display: none; }
</style>
