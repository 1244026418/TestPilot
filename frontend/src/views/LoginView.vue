<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Lock, User } from '@element-plus/icons-vue'
import { errorMessage } from '../api/client'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const mode = ref<'login' | 'register'>('login')
const loading = ref(false)
const form = reactive({ username: '', password: '' })

async function submit() {
  if (form.username.length < 3 || form.password.length < 6) {
    ElMessage.warning('用户名至少 3 位，密码至少 6 位')
    return
  }
  loading.value = true
  try {
    if (mode.value === 'login') await auth.login(form.username, form.password)
    else await auth.register(form.username, form.password)
    ElMessage.success(mode.value === 'login' ? '登录成功' : '注册成功')
    router.replace('/')
  } catch (error) {
    ElMessage.error(errorMessage(error))
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <section class="login-panel">
      <div class="login-brand"><h1>TestPilot</h1><p>AI 辅助接口自动化测试平台</p></div>
      <el-segmented v-model="mode" :options="[{ label: '登录', value: 'login' }, { label: '注册', value: 'register' }]" block />
      <el-form class="login-form" label-position="top" @submit.prevent="submit">
        <el-form-item label="用户名">
          <el-input v-model="form.username" :prefix-icon="User" placeholder="请输入用户名" size="large" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" :prefix-icon="Lock" type="password" show-password placeholder="请输入密码" size="large" @keyup.enter="submit" />
        </el-form-item>
        <el-button type="primary" size="large" :loading="loading" style="width: 100%" @click="submit">
          {{ mode === 'login' ? '登录平台' : '创建账号' }}
        </el-button>
      </el-form>
      <el-alert v-if="mode === 'register'" title="第一个注册账号自动成为管理员" type="info" :closable="false" show-icon />
    </section>
    <section class="login-scene">
      <div><h2>把接口资产、测试设计、自动执行和报告分析放在同一套工作流里。</h2><p>支持 OpenAPI 与 Postman 导入，使用 GPT 或规则引擎生成测试用例，并沉淀每次执行结果。</p></div>
    </section>
  </div>
</template>

<style scoped>
.login-form { margin: 28px 0 18px; }
</style>
