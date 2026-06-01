<template>
  <section class="result-page">
    <img class="page-bg" :src="homeBackgroundUrl" alt="" aria-hidden="true" />
    <div class="bg-wash"></div>

    <a-empty v-if="!tripPlan" class="empty-state" description="还没有旅行方案">
      <template #image>
        <div class="empty-mark">AI</div>
      </template>
      <template #description>
        <span>先创建一次旅行任务，这里会显示完整行程。</span>
      </template>
      <a-button type="primary" @click="goHome">返回创建</a-button>
    </a-empty>

    <template v-else>
      <div class="result-shell">
        <header class="result-hero glass-card">
          <div>
            <a-button class="ghost-button" @click="goHome">返回首页</a-button>
            <p class="eyebrow">Trip Canvas</p>
            <h1>{{ tripPlan.city }} 旅行计划</h1>
            <p class="date-line">{{ tripPlan.start_date }} 至 {{ tripPlan.end_date }}</p>
          </div>

          <a-space wrap>
            <a-button @click="exportAsImage">导出图片</a-button>
            <a-button type="primary" @click="confirmPlan" :loading="confirming">确认计划</a-button>
          </a-space>
        </header>

        <div class="result-layout">
          <main class="main-content">
            <section class="overview-section glass-card">
              <div>
                <span class="section-label">Overview</span>
                <h2>整体建议</h2>
                <p>{{ tripPlan.overall_suggestions || '暂无整体建议。' }}</p>
                <p v-if="tripPlan.optimization_summary" class="optimization">
                  {{ tripPlan.optimization_summary }}
                </p>
              </div>

              <div v-if="tripPlan.budget" class="budget-panel">
                <span>预计总费用</span>
                <strong>¥{{ tripPlan.budget.total }}</strong>
                <div>
                  <small>门票 ¥{{ tripPlan.budget.total_attractions }}</small>
                  <small>住宿 ¥{{ tripPlan.budget.total_hotels }}</small>
                  <small>餐饮 ¥{{ tripPlan.budget.total_meals }}</small>
                  <small>交通 ¥{{ tripPlan.budget.total_transportation }}</small>
                </div>
              </div>
            </section>

            <section class="map-section glass-card">
              <div class="section-heading">
                <span class="section-label">Map</span>
                <h2>景点地图</h2>
              </div>
              <div id="amap-container"></div>
            </section>

            <section class="days-section glass-card">
              <div class="section-heading">
                <span class="section-label">Daily Plan</span>
                <h2>每日行程</h2>
              </div>

              <a-collapse v-model:activeKey="activeDays" class="day-collapse">
                <a-collapse-panel v-for="day in tripPlan.days" :key="day.day_index">
                  <template #header>
                    <div class="day-title">
                      <strong>Day {{ day.day_index + 1 }}</strong>
                      <span>{{ day.date }}</span>
                    </div>
                  </template>

                  <div class="day-meta">
                    <div>
                      <span>说明</span>
                      <strong>{{ day.description }}</strong>
                    </div>
                    <div>
                      <span>交通</span>
                      <strong>{{ day.transportation }}</strong>
                    </div>
                    <div>
                      <span>住宿</span>
                      <strong>{{ day.accommodation }}</strong>
                    </div>
                  </div>

                  <div class="timeline">
                    <article
                      v-for="(item, index) in day.attractions"
                      :key="`${day.day_index}-${item.name}-${index}`"
                      class="attraction-card"
                    >
                      <div class="image-wrap">
                        <img :src="getAttractionImage(item.name, index)" :alt="item.name" />
                        <span>{{ index + 1 }}</span>
                      </div>
                      <div class="card-body">
                        <h3>{{ item.name }}</h3>
                        <p>{{ item.description }}</p>
                        <dl>
                          <div>
                            <dt>地址</dt>
                            <dd>{{ item.address }}</dd>
                          </div>
                          <div>
                            <dt>时长</dt>
                            <dd>{{ item.visit_duration }} 分钟</dd>
                          </div>
                          <div v-if="item.ticket_price">
                            <dt>门票</dt>
                            <dd>¥{{ item.ticket_price }}</dd>
                          </div>
                        </dl>
                      </div>
                    </article>
                  </div>

                  <div class="support-grid">
                    <section v-if="day.hotel" class="support-card">
                      <span class="section-label">Hotel</span>
                      <h3>{{ day.hotel.name }}</h3>
                      <p>{{ day.hotel.address }}</p>
                      <small>{{ day.hotel.price_range }} · {{ day.hotel.rating }}</small>
                    </section>

                    <section class="support-card">
                      <span class="section-label">Meals</span>
                      <div v-for="meal in day.meals" :key="meal.type" class="meal-row">
                        <span>{{ getMealLabel(meal.type) }}</span>
                        <strong>{{ meal.name }}</strong>
                        <small v-if="meal.description">{{ meal.description }}</small>
                      </div>
                    </section>
                  </div>
                </a-collapse-panel>
              </a-collapse>
            </section>

            <section v-if="tripPlan.weather_info?.length" class="weather-section glass-card">
              <div class="section-heading">
                <span class="section-label">Weather</span>
                <h2>天气信息</h2>
              </div>
              <div class="weather-grid">
                <article v-for="item in tripPlan.weather_info" :key="item.date">
                  <strong>{{ item.date }}</strong>
                  <span>白天 {{ item.day_weather }} {{ item.day_temp }}°C</span>
                  <span>夜间 {{ item.night_weather }} {{ item.night_temp }}°C</span>
                  <small>{{ item.wind_direction }} {{ item.wind_power }}</small>
                </article>
              </div>
            </section>
          </main>

          <aside class="revision-panel">
            <a-affix :offset-top="84">
              <div class="revision-card glass-card">
                <span class="section-label">Revise</span>
                <h2>继续修改这份计划</h2>
                <p>你可以直接告诉它要加景点、换酒店、放慢节奏或准备雨天替代方案。</p>

                <div class="quick-prompts">
                  <button
                    v-for="prompt in quickPrompts"
                    :key="prompt"
                    type="button"
                    @click="revisionText = prompt"
                  >
                    {{ prompt }}
                  </button>
                </div>

                <a-textarea
                  v-model:value="revisionText"
                  :rows="5"
                  placeholder="例如：第二天想增加一个景点，但不要太远。"
                />

                <a-button
                  type="primary"
                  block
                  class="revise-button"
                  :loading="revising"
                  :disabled="!sessionId"
                  @click="revisePlan"
                >
                  {{ sessionId ? '发送修改要求' : '会话已结束' }}
                </a-button>

                <div v-if="revisionHistory.length" class="history">
                  <strong>修改记录</strong>
                  <span v-for="item in revisionHistory" :key="item">{{ item }}</span>
                </div>
              </div>
            </a-affix>
          </aside>
        </div>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import html2canvas from 'html2canvas'
import AMapLoader from '@amap/amap-jsapi-loader'
import { confirmTripPlan, reviseTripPlan } from '@/services/api'
import type { TripPlan } from '@/types'
import homeBackgroundUrl from '@/assets/home-background.jpg'

const router = useRouter()
const tripPlan = ref<TripPlan | null>(null)
const sessionId = ref('')
const activeDays = ref<number[]>([0])
const revisionText = ref('')
const revising = ref(false)
const confirming = ref(false)
const revisionHistory = ref<string[]>([])
let map: any = null

const quickPrompts = [
  '第二天想增加一个景点，但不要太远',
  '如果下雨，给我室内替代方案',
  '多安排本地小吃，少安排购物',
  '酒店想换成更便宜、靠近地铁的'
]

const allAttractions = computed(() => {
  if (!tripPlan.value) return []
  return tripPlan.value.days.flatMap((day, dayIndex) =>
    day.attractions.map((attraction, attrIndex) => ({ ...attraction, dayIndex, attrIndex }))
  )
})

onMounted(async () => {
  const data = sessionStorage.getItem('tripPlan')
  sessionId.value = sessionStorage.getItem('tripSessionId') || ''
  if (!data) return

  tripPlan.value = JSON.parse(data)
  await nextTick()
  await initMap()
})

const goHome = () => {
  router.push('/')
}

const revisePlan = async () => {
  if (!sessionId.value || !revisionText.value.trim()) {
    message.warning('请先输入修改要求')
    return
  }

  revising.value = true
  try {
    const text = revisionText.value.trim()
    const response = await reviseTripPlan({
      session_id: sessionId.value,
      message: text
    })

    if (response.success && response.data) {
      tripPlan.value = response.data
      sessionStorage.setItem('tripPlan', JSON.stringify(response.data))
      revisionHistory.value.unshift(text)
      revisionText.value = ''
      message.success('旅行方案已更新')
      await nextTick()
      await rebuildMap()
    }
  } catch (error: any) {
    message.error(error.message || '修改失败')
  } finally {
    revising.value = false
  }
}

const confirmPlan = async () => {
  confirming.value = true
  try {
    if (sessionId.value) {
      await confirmTripPlan({ session_id: sessionId.value })
    }
    sessionStorage.removeItem('tripSessionId')
    sessionStorage.removeItem('tripPlan')
    sessionId.value = ''
    message.success('计划已确认，会话已结束。重新打开就是新的旅程。')
  } catch (error: any) {
    message.error(error.message || '确认失败')
  } finally {
    confirming.value = false
  }
}

const getMealLabel = (type: string): string => {
  const labels: Record<string, string> = {
    breakfast: '早餐',
    lunch: '午餐',
    dinner: '晚餐',
    snack: '小吃'
  }
  return labels[type] || type
}

const getAttractionImage = (name: string, index: number): string => {
  const colors = [
    ['#347ee8', '#6fcce8'],
    ['#19a981', '#7bd9c3'],
    ['#d99021', '#ffd98a'],
    ['#bc5b7c', '#f0abc0']
  ]
  const [start, end] = colors[index % colors.length]
  const safeName = name.replace(/[<&>]/g, '')
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="760" height="460">
    <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="${start}"/><stop offset="100%" stop-color="${end}"/>
    </linearGradient></defs>
    <rect width="760" height="460" fill="url(#g)"/>
    <circle cx="612" cy="112" r="92" fill="rgba(255,255,255,0.22)"/>
    <path d="M0 330 C160 270 260 380 430 310 C560 258 640 300 760 250 L760 460 L0 460 Z" fill="rgba(255,255,255,0.24)"/>
    <text x="46" y="246" font-family="Arial, sans-serif" font-size="42" font-weight="800" fill="#fff">${safeName}</text>
  </svg>`

  return `data:image/svg+xml;base64,${btoa(unescape(encodeURIComponent(svg)))}`
}

const exportAsImage = async () => {
  try {
    const element = document.querySelector('.main-content') as HTMLElement
    if (!element) throw new Error('未找到行程内容')

    const canvas = await html2canvas(element, {
      backgroundColor: '#eef8ff',
      scale: 2,
      logging: false,
      useCORS: true
    })

    const link = document.createElement('a')
    link.download = `旅行方案_${tripPlan.value?.city}_${Date.now()}.png`
    link.href = canvas.toDataURL('image/png')
    link.click()
    message.success('图片导出成功')
  } catch (error: any) {
    message.error(`图片导出失败: ${error.message}`)
  }
}

const initMap = async () => {
  const container = document.getElementById('amap-container')
  if (!container || !tripPlan.value) return

  try {
    const AMap = await AMapLoader.load({
      key: import.meta.env.VITE_AMAP_WEB_JS_KEY,
      version: '2.0',
      plugins: ['AMap.Marker', 'AMap.Polyline']
    })

    map = new AMap.Map('amap-container', {
      zoom: 12,
      center: [116.397128, 39.916527],
      viewMode: '3D',
      mapStyle: 'amap://styles/normal'
    })

    addAttractionMarkers(AMap)
  } catch (error) {
    console.error('地图加载失败:', error)
  }
}

const rebuildMap = async () => {
  if (map) {
    map.destroy()
    map = null
  }
  await initMap()
}

const addAttractionMarkers = (AMap: any) => {
  if (!map) return

  const markers: any[] = []
  allAttractions.value.forEach((attraction, index) => {
    if (!attraction.location?.longitude || !attraction.location?.latitude) return

    markers.push(
      new AMap.Marker({
        position: [attraction.location.longitude, attraction.location.latitude],
        title: attraction.name,
        label: {
          content: `<div style="background:#347ee8;color:#fff;padding:5px 8px;border-radius:8px;font-weight:800;">${index + 1}</div>`,
          offset: new AMap.Pixel(0, -30)
        }
      })
    )
  })

  if (!markers.length) return
  map.add(markers)
  map.setFitView(markers)

  const dayGroups = allAttractions.value.reduce<Record<number, any[]>>((groups, attr) => {
    groups[attr.dayIndex] = groups[attr.dayIndex] || []
    groups[attr.dayIndex].push(attr)
    return groups
  }, {})

  Object.values(dayGroups).forEach(dayAttractions => {
    if (dayAttractions.length < 2) return

    map.add(
      new AMap.Polyline({
        path: dayAttractions.map(attr => [attr.location.longitude, attr.location.latitude]),
        strokeColor: '#347ee8',
        strokeWeight: 5,
        strokeOpacity: 0.9,
        showDir: true
      })
    )
  })
}
</script>

<style scoped>
.result-page {
  position: relative;
  min-height: calc(100vh - 62px);
  overflow: hidden;
  padding: 28px;
}

.page-bg,
.bg-wash {
  position: fixed;
  inset: 0;
}

.page-bg {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.bg-wash {
  background:
    linear-gradient(90deg, rgba(230, 242, 252, 0.28), rgba(230, 242, 252, 0.12)),
    linear-gradient(180deg, rgba(255, 255, 255, 0.1), rgba(15, 45, 70, 0.18));
}

.result-shell {
  position: relative;
  z-index: 1;
  width: min(1480px, 100%);
  margin: 0 auto;
}

.glass-card {
  border: 1px solid rgba(255, 255, 255, 0.56);
  border-radius: 26px;
  background: rgba(244, 249, 255, 0.46);
  box-shadow: 0 24px 80px rgba(16, 47, 72, 0.2);
  backdrop-filter: blur(18px) saturate(1.25);
}

.result-hero {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 22px;
  padding: 28px;
}

.ghost-button {
  margin-bottom: 22px;
  border-color: rgba(255, 255, 255, 0.62);
  background: rgba(255, 255, 255, 0.42);
}

.eyebrow,
.section-label {
  display: block;
  margin: 0 0 10px;
  color: #347ee8;
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

h1,
h2,
h3,
p {
  margin-top: 0;
  letter-spacing: 0;
}

h1 {
  margin-bottom: 10px;
  color: #10283a;
  font-size: clamp(40px, 5vw, 72px);
  line-height: 1;
  font-weight: 950;
}

.date-line {
  margin-bottom: 0;
  color: #31546a;
}

.result-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: 22px;
  align-items: start;
}

.overview-section {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 280px;
  gap: 22px;
  margin-bottom: 18px;
  padding: 24px;
}

.overview-section h2,
.section-heading h2,
.revision-card h2 {
  color: #10283a;
  font-size: 26px;
}

.overview-section p {
  color: #28495c;
  line-height: 1.8;
}

.optimization {
  margin: 18px 0 0;
  padding: 14px;
  border-left: 3px solid #347ee8;
  background: rgba(255, 255, 255, 0.38);
}

.budget-panel {
  display: grid;
  gap: 12px;
  padding: 18px;
  border-radius: 20px;
  color: #fff;
  background: rgba(52, 126, 232, 0.72);
}

.budget-panel span,
.budget-panel small {
  color: rgba(255, 255, 255, 0.78);
}

.budget-panel strong {
  font-size: 42px;
  line-height: 1;
}

.budget-panel div {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.map-section,
.days-section,
.weather-section,
.revision-card {
  margin-bottom: 18px;
  padding: 24px;
}

#amap-container {
  height: 420px;
  margin: 18px -24px -24px;
  overflow: hidden;
  border-radius: 0 0 26px 26px;
  background: rgba(255, 255, 255, 0.44);
}

.day-collapse {
  border: 0;
  background: transparent;
}

.day-title {
  display: flex;
  justify-content: space-between;
  width: 100%;
}

.day-meta {
  display: grid;
  grid-template-columns: 1.4fr 0.8fr 0.8fr;
  gap: 12px;
  margin-bottom: 18px;
}

.day-meta div,
.support-card,
.weather-grid article {
  padding: 16px;
  border: 1px solid rgba(255, 255, 255, 0.56);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.42);
}

.day-meta span,
dt,
.meal-row span {
  color: #5a7787;
}

.day-meta strong {
  display: block;
  margin-top: 5px;
  color: #10283a;
}

.timeline {
  display: grid;
  gap: 16px;
}

.attraction-card {
  display: grid;
  grid-template-columns: 250px minmax(0, 1fr);
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.56);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.48);
}

.image-wrap {
  position: relative;
  min-height: 210px;
  overflow: hidden;
}

.image-wrap img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-wrap span {
  position: absolute;
  top: 12px;
  left: 12px;
  display: grid;
  width: 34px;
  height: 34px;
  place-items: center;
  border-radius: 999px;
  color: #fff;
  background: #347ee8;
  font-weight: 900;
}

.card-body {
  padding: 18px;
}

.card-body h3,
.support-card h3 {
  color: #10283a;
}

.card-body p,
.support-card p,
.revision-card p {
  color: #36596d;
  line-height: 1.7;
}

dl {
  display: grid;
  gap: 8px;
  margin: 0;
}

dl div {
  display: grid;
  grid-template-columns: 52px 1fr;
  gap: 10px;
}

dd {
  margin: 0;
  color: #183448;
}

.support-grid,
.weather-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-top: 18px;
}

.weather-grid {
  grid-template-columns: repeat(3, 1fr);
}

.meal-row {
  display: grid;
  gap: 4px;
  padding: 10px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.46);
}

.meal-row:last-child {
  border-bottom: 0;
}

.quick-prompts {
  display: grid;
  gap: 8px;
  margin: 18px 0;
}

.quick-prompts button {
  padding: 10px 12px;
  border: 1px solid rgba(255, 255, 255, 0.56);
  border-radius: 14px;
  color: #203f52;
  background: rgba(255, 255, 255, 0.42);
  text-align: left;
  cursor: pointer;
}

.quick-prompts button:hover {
  border-color: rgba(52, 126, 232, 0.5);
  color: #347ee8;
}

.revise-button {
  height: 46px;
  margin-top: 12px;
  border-radius: 999px;
  font-weight: 900;
}

.history {
  display: grid;
  gap: 8px;
  margin-top: 18px;
  color: #36596d;
  font-size: 13px;
}

.empty-state {
  position: relative;
  z-index: 1;
  margin: 90px auto 0;
  width: min(720px, 100%);
  padding: 56px 24px;
  border-radius: 26px;
  background: rgba(244, 249, 255, 0.58);
  backdrop-filter: blur(18px);
}

.empty-mark {
  display: inline-grid;
  width: 86px;
  height: 86px;
  place-items: center;
  border-radius: 50%;
  background: #347ee8;
  color: #fff;
  font-size: 30px;
  font-weight: 900;
}

:deep(.ant-collapse-item) {
  margin-bottom: 14px;
  overflow: hidden;
  border: 0 !important;
  border-radius: 18px !important;
  background: rgba(255, 255, 255, 0.34);
}

:deep(.ant-collapse-header) {
  align-items: center !important;
  background: rgba(255, 255, 255, 0.54);
  border-radius: 18px !important;
}

:deep(.ant-collapse-content) {
  border-top: 0 !important;
  background: transparent !important;
}

:deep(.ant-collapse-content-box) {
  padding: 18px 0 0 !important;
}

:deep(.ant-input),
:deep(textarea.ant-input) {
  border-color: rgba(255, 255, 255, 0.62) !important;
  background: rgba(255, 255, 255, 0.5) !important;
}

@media (max-width: 1120px) {
  .result-layout,
  .overview-section {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .result-page {
    padding: 16px;
  }

  .result-hero {
    align-items: flex-start;
    flex-direction: column;
  }

  .day-meta,
  .attraction-card,
  .support-grid,
  .weather-grid {
    grid-template-columns: 1fr;
  }
}
</style>
