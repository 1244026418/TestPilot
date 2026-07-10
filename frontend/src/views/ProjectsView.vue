<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import client, { errorMessage } from '../api/client'
import { useAuthStore } from '../stores/auth'
import type { Project } from '../types'

const auth = useAuthStore()
const projects = ref<Project[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const form = reactive({ name: '', description: '' })

async function load() {
  loading.value = true
  try { projects.value = (await client.get<Project[]>('/projects')).data }
  catch (error) { ElMessage.error(errorMessage(error)) }
  finally { loading.value = false }
}

async function createProject() {
  if (!form.name.trim()) return ElMessage.warning('请输入项目名称')
  try {
    await client.post('/projects', form)
    dialogVisible.value = false
    form.name = ''; form.description = ''
    ElMessage.success('项目已创建')
    await load()
  } catch (error) { ElMessage.error(errorMessage(error)) }
}

async function remove(project: Project) {
  await ElMessageBox.confirm(`确认删除项目“${project.name}”及其所有测试数据？`, '删除项目', { type: 'warning' })
  try {
    await client.delete(`/projects/${project.id}`)
    ElMessage.success('项目已删除')
    await load()
  } catch (error) { ElMessage.error(errorMessage(error)) }
}

onMounted(load)
</script>

<template>
  <div>
    <div class="page-heading"><div><h2>项目管理</h2><p>按业务或服务划分接口测试资产</p></div><el-button type="primary" :icon="Plus" @click="dialogVisible = true">新建项目</el-button></div>
    <div class="surface">
      <el-table v-loading="loading" :data="projects" stripe empty-text="暂无项目">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="项目名称" min-width="180" />
        <el-table-column prop="description" label="描述" min-width="260" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" width="190" />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="scope"><el-button v-if="auth.isAdmin" type="danger" link @click="remove(scope.row)">删除</el-button></template>
        </el-table-column>
      </el-table>
    </div>
    <el-dialog v-model="dialogVisible" title="新建测试项目" width="480px">
      <el-form label-position="top">
        <el-form-item label="项目名称"><el-input v-model="form.name" placeholder="例如：用户中心接口测试" /></el-form-item>
        <el-form-item label="项目描述"><el-input v-model="form.description" type="textarea" :rows="4" placeholder="说明服务范围和测试目标" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="dialogVisible = false">取消</el-button><el-button type="primary" @click="createProject">创建</el-button></template>
    </el-dialog>
  </div>
</template>
