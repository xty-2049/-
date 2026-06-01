<template>
  <section class="home-page">
    <img class="page-bg" :src="homeBackgroundUrl" alt="" aria-hidden="true" />
    <div class="bg-wash"></div>

    <div class="split-layout">
      <aside class="intro-panel">
        <p class="eyebrow">AI Travel Planner</p>
        <h1>云端智策，畅享旅途</h1>
        <p class="intro-text">
          输入目的地、日期和偏好，AI为你生成专属行程。随时调整节奏、增减景点，直到满意为止。
        </p>

        <div class="feature-row">
          <div>
            <strong>01</strong>
            <span>一键生成专属行程初版</span>
          </div>
          <div>
            <strong>02</strong>
            <span>自然语言修改，越改越合心意</span>
          </div>
          <div>
            <strong>03</strong>
            <span>确认行程，开启你的旅行</span>
          </div>
        </div>
      </aside>

      <a-form class="planner-panel" :model="formData" layout="vertical" @finish="handleSubmit">
        <div class="panel-head">
          <div>
            <p class="eyebrow">Start planning</p>
            <h2>创建旅行计划</h2>
          </div>
          <span>{{ formData.travel_days }} 天</span>
        </div>

        <div class="form-grid">
          <a-form-item
            name="city"
            label="目的地"
            :rules="[{ required: true, message: '请输入目的地城市' }]"
          >
            <a-input v-model:value="formData.city" size="large" placeholder="例如：北京" />
          </a-form-item>

          <a-form-item
            name="start_date"
            label="开始日期"
            :rules="[{ required: true, message: '请选择开始日期' }]"
          >
            <a-date-picker
              v-model:value="formData.start_date"
              size="large"
              placeholder="选择日期"
              style="width: 100%"
            />
          </a-form-item>

          <a-form-item
            name="end_date"
            label="结束日期"
            :rules="[{ required: true, message: '请选择结束日期' }]"
          >
            <a-date-picker
              v-model:value="formData.end_date"
              size="large"
              placeholder="选择日期"
              style="width: 100%"
            />
          </a-form-item>
        </div>

        <div class="option-grid">
          <a-form-item name="transportation" label="交通方式">
            <a-segmented v-model:value="formData.transportation" block :options="transportOptions" />
          </a-form-item>

          <a-form-item name="accommodation" label="住宿偏好">
            <a-select v-model:value="formData.accommodation" size="large" :options="hotelOptions" />
          </a-form-item>
        </div>

        <a-form-item name="preferences" label="旅行偏好">
          <a-checkbox-group v-model:value="formData.preferences" class="preference-grid">
            <a-checkbox v-for="item in preferenceOptions" :key="item" :value="item">
              {{ item }}
            </a-checkbox>
          </a-checkbox-group>
        </a-form-item>

        <a-form-item name="free_text_input" label="补充要求">
          <a-textarea
            v-model:value="formData.free_text_input"
            :rows="4"
            placeholder="例如：想多吃本地美食、老人同行、少走路、需要雨天替代方案..."
          />
        </a-form-item>

        <div v-if="loading" class="loading-panel">
          <a-progress
            :percent="loadingProgress"
            status="active"
            :stroke-color="{ '0%': '#347ee8', '100%': '#19a981' }"
          />
          <span>{{ loadingStatus }}</span>
        </div>

        <a-button
          type="primary"
          html-type="submit"
          size="large"
          block
          :loading="loading"
          class="submit-button"
        >
          {{ loading ? '正在生成专属行程' : '生成初版行程' }}
        </a-button>
      </a-form>
    </div>
  </section>
</template>

<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { generateTripPlan } from '@/services/api'
import type { TripFormData } from '@/types'
import type { Dayjs } from 'dayjs'
import homeBackgroundUrl from '@/assets/home-background.jpg'

const router = useRouter()
const loading = ref(false)
const loadingProgress = ref(0)
const loadingStatus = ref('')

type TripFormState = Omit<TripFormData, 'start_date' | 'end_date'> & {
  start_date: Dayjs | null
  end_date: Dayjs | null
}

const transportOptions = [
  { label: '公交', value: '公共交通' },
  { label: '自驾', value: '自驾' },
  { label: '步行', value: '步行' },
  { label: '混合', value: '混合' }
]

const hotelOptions = [
  { label: '经济型酒店', value: '经济型酒店' },
  { label: '舒适型酒店', value: '舒适型酒店' },
  { label: '高端酒店', value: '高端酒店' },
  { label: '民宿', value: '民宿' }
]

const preferenceOptions = ['历史文化', '自然风光', '本地美食', '城市漫步', '艺术展览', '亲子休闲']

const formData = reactive<TripFormState>({
  city: '',
  start_date: null,
  end_date: null,
  travel_days: 1,
  transportation: '公共交通',
  accommodation: '舒适型酒店',
  preferences: [],
  free_text_input: ''
})

watch([() => formData.start_date, () => formData.end_date], ([start, end]) => {
  if (!start || !end) return

  const days = end.diff(start, 'day') + 1
  if (days > 0 && days <= 30) {
    formData.travel_days = days
    return
  }

  message.warning(days > 30 ? '旅行天数不能超过 30 天' : '结束日期不能早于开始日期')
  formData.end_date = null
})

const handleSubmit = async () => {
  if (!formData.start_date || !formData.end_date) {
    message.error('请选择旅行日期')
    return
  }

  loading.value = true
  loadingProgress.value = 8
  loadingStatus.value = '正在创建临时会话...'

  const progressInterval = window.setInterval(() => {
    if (loadingProgress.value >= 88) return
    loadingProgress.value += 8

    if (loadingProgress.value <= 32) {
      loadingStatus.value = '正在搜索目的地信息...'
    } else if (loadingProgress.value <= 56) {
      loadingStatus.value = '正在编排行程节奏...'
    } else if (loadingProgress.value <= 76) {
      loadingStatus.value = '正在生成可修改方案...'
    } else {
      loadingStatus.value = '正在保存临时会话...'
    }
  }, 500)

  try {
    const requestData: TripFormData = {
      city: formData.city,
      start_date: formData.start_date.format('YYYY-MM-DD'),
      end_date: formData.end_date.format('YYYY-MM-DD'),
      travel_days: formData.travel_days,
      transportation: formData.transportation,
      accommodation: formData.accommodation,
      preferences: formData.preferences,
      free_text_input: formData.free_text_input
    }

    const response = await generateTripPlan(requestData)
    window.clearInterval(progressInterval)
    loadingProgress.value = 100
    loadingStatus.value = '初版行程已生成'

    if (response.success && response.data) {
      sessionStorage.setItem('tripPlan', JSON.stringify(response.data))
      if (response.session_id) {
        sessionStorage.setItem('tripSessionId', response.session_id)
      }
      message.success('初版旅行方案已生成')
      window.setTimeout(() => router.push('/result'), 400)
    } else {
      message.error(response.message || '生成失败')
    }
  } catch (error: any) {
    window.clearInterval(progressInterval)
    message.error(error.message || '生成旅行方案失败，请稍后重试')
  } finally {
    window.setTimeout(() => {
      loading.value = false
      loadingProgress.value = 0
      loadingStatus.value = ''
    }, 800)
  }
}
</script>

<style scoped>
.home-page {
  position: relative;
  min-height: calc(100vh - 62px);
  overflow: hidden;
  padding: 28px;
}

.page-bg {
  position: fixed;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 1;
}

.bg-wash {
  position: fixed;
  inset: 0;
  background:
    linear-gradient(90deg, rgba(230, 242, 252, 0.28), rgba(230, 242, 252, 0.12)),
    linear-gradient(180deg, rgba(255, 255, 255, 0.1), rgba(15, 45, 70, 0.18));
}

.split-layout {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: minmax(0, 0.46fr) minmax(0, 0.54fr);
  gap: 24px;
  width: min(1760px, 100%);
  min-height: calc(100vh - 118px);
  margin: 0 auto;
  align-items: center;
}

.intro-panel,
.planner-panel {
  border: 1px solid rgba(255, 255, 255, 0.56);
  border-radius: 28px;
  background: rgba(244, 249, 255, 0.46);
  box-shadow: 0 24px 80px rgba(16, 47, 72, 0.22);
  backdrop-filter: blur(18px) saturate(1.25);
}

.intro-panel {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: 760px;
  padding: 38px;
}

.eyebrow {
  margin: 0 0 20px;
  color: #347ee8;
  font-size: 16px;
  font-weight: 900;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

h1,
h2,
p {
  margin-top: 0;
  letter-spacing: 0;
}

h1 {
  margin-bottom: 26px;
  color: #10283a;
  font-size: clamp(48px, 4.25vw, 82px);
  line-height: 1.02;
  font-weight: 950;
  text-shadow: 0 2px 18px rgba(255, 255, 255, 0.42);
}

.intro-text {
  max-width: 820px;
  margin-bottom: 42px;
  color: #1f4155;
  font-size: clamp(18px, 1.2vw, 22px);
  line-height: 1.85;
}

.feature-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
}

.feature-row div {
  min-height: 104px;
  padding: 18px 20px;
  border: 1px solid rgba(255, 255, 255, 0.62);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.5);
  box-shadow: 0 14px 36px rgba(48, 91, 123, 0.08);
  backdrop-filter: blur(14px);
}

.feature-row strong,
.feature-row span {
  display: block;
}

.feature-row strong {
  color: #347ee8;
  font-size: 30px;
  line-height: 1;
}

.feature-row span {
  margin-top: 12px;
  color: #213949;
  font-size: 17px;
  font-weight: 900;
}

.planner-panel {
  padding: 34px;
}

.panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 30px;
}

.panel-head h2 {
  margin: 0;
  color: #10283a;
  font-size: 32px;
  font-weight: 500;
}

.panel-head span {
  display: inline-grid;
  min-width: 58px;
  min-height: 58px;
  place-items: center;
  border-radius: 999px;
  color: #347ee8;
  background: rgba(226, 238, 255, 0.58);
  font-size: 20px;
  font-weight: 900;
}

.form-grid {
  display: grid;
  grid-template-columns: 1.2fr 1fr 1fr;
  gap: 18px;
}

.option-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}

.preference-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  width: 100%;
}

.preference-grid :deep(.ant-checkbox-wrapper) {
  display: flex;
  align-items: center;
  min-height: 52px;
  margin: 0;
  padding: 12px 14px;
  border: 1px solid rgba(255, 255, 255, 0.58);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.46);
  font-size: 16px;
  backdrop-filter: blur(12px);
}

.preference-grid :deep(.ant-checkbox-wrapper-checked) {
  border-color: rgba(52, 126, 232, 0.52);
  background: rgba(52, 126, 232, 0.14);
}

.loading-panel {
  margin: 6px 0 20px;
  padding: 16px;
  border-radius: 16px;
  background: rgba(237, 249, 255, 0.54);
}

.loading-panel span {
  display: block;
  margin-top: 8px;
  color: #4a6575;
}

.submit-button {
  height: 64px;
  border-radius: 999px;
  font-size: 19px;
  font-weight: 900;
  box-shadow: 0 16px 36px rgba(52, 126, 232, 0.28);
}

:deep(.ant-form-item) {
  margin-bottom: 20px;
}

:deep(.ant-form-item-label > label) {
  color: #203948;
  font-size: 16px;
  font-weight: 900;
}

:deep(.ant-input),
:deep(.ant-picker),
:deep(.ant-select-selector),
:deep(textarea.ant-input) {
  border-color: rgba(255, 255, 255, 0.62) !important;
  background: rgba(255, 255, 255, 0.5) !important;
  font-size: 17px !important;
  backdrop-filter: blur(12px);
}

:deep(.ant-input),
:deep(.ant-picker),
:deep(.ant-select-selector) {
  min-height: 54px !important;
}

:deep(.ant-segmented) {
  min-height: 48px;
  background: rgba(255, 255, 255, 0.44) !important;
  backdrop-filter: blur(12px);
}

:deep(.ant-segmented-item) {
  min-height: 44px;
  line-height: 44px;
  font-size: 16px;
}

@media (max-width: 980px) {
  .split-layout {
    grid-template-columns: 1fr;
  }

  .intro-panel {
    min-height: auto;
  }
}

@media (max-width: 760px) {
  .home-page {
    padding: 16px;
  }

  .intro-panel,
  .planner-panel {
    padding: 24px;
    border-radius: 22px;
  }

  h1 {
    font-size: 52px;
  }

  .intro-text {
    font-size: 18px;
  }

  .feature-row,
  .form-grid,
  .option-grid,
  .preference-grid {
    grid-template-columns: 1fr;
  }
}
</style>
