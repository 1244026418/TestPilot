<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { DataAnalysis, DocumentAdd, FolderOpened, Operation, SwitchButton, Tickets } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

function logout() {
  auth.logout()
  router.replace('/login')
}
</script>

<template>
  <el-container class="app-layout">
    <el-aside class="app-aside" width="232px">
      <div class="brand-block">
        <div class="brand-mark">TP</div>
        <div><strong>TestPilot</strong><span>接口测试平台</span></div>
      </div>
      <el-menu :default-active="route.path" router class="app-menu">
        <el-menu-item index="/"><el-icon><DataAnalysis /></el-icon><span>工作台</span></el-menu-item>
        <el-menu-item index="/projects"><el-icon><FolderOpened /></el-icon><span>项目管理</span></el-menu-item>
        <el-menu-item index="/workspace"><el-icon><Operation /></el-icon><span>接口与用例</span></el-menu-item>
        <el-menu-item index="/import"><el-icon><DocumentAdd /></el-icon><span>文档导入</span></el-menu-item>
        <el-menu-item index="/runs"><el-icon><Tickets /></el-icon><span>执行记录</span></el-menu-item>
      </el-menu>
      <div class="aside-user">
        <div><strong>{{ auth.user?.username }}</strong><span>{{ auth.isAdmin ? '管理员' : '普通用户' }}</span></div>
        <el-button :icon="SwitchButton" circle title="退出登录" @click="logout" />
      </div>
    </el-aside>
    <el-container>
      <el-header class="app-header">
        <div><h1>AI 辅助接口自动化测试平台</h1><p>项目、接口、用例与测试报告统一管理</p></div>
        <el-link href="/docs" target="_blank" type="primary">API 文档</el-link>
      </el-header>
      <el-main class="app-main"><router-view /></el-main>
    </el-container>
  </el-container>
</template>
