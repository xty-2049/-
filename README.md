# 智能旅行规划系统

本项目是一个基于 Vue 3、FastAPI、HelloAgents 和高德地图能力的个性化旅行规划系统。系统支持根据城市、日期、交通方式、住宿偏好和兴趣标签生成旅行计划，并展示地图路线、预算明细、天气信息和导出结果。

## 本次增强

本项目新增了三个适合简历展示的核心能力：

1. SQLite 缓存机制
   - 文件：`backend/app/services/cache_service.py`
   - 缓存 POI、天气、路线、地理编码、POI 详情和行程优化结果。
   - 目的：减少重复外部 API 调用，提高响应速度并降低接口调用成本。

2. 区域聚类
   - 文件：`backend/app/services/cluster_service.py`
   - 使用轻量 K-Means 思路，根据景点经纬度和旅行天数将景点划分到不同游览区域。
   - 目的：尽量把同一天的景点安排在相近区域，减少跨区域通勤。

3. 路径优化
   - 文件：`backend/app/services/route_optimizer.py`
   - 使用最近邻算法生成初始访问顺序，再用 2-opt 进行局部优化。
   - 目的：优化每日景点访问顺序，减少景点间通勤距离。

整体后处理入口：

```text
backend/app/services/itinerary_optimizer.py
```

系统在 LLM 生成初始行程后，会自动执行：

```text
收集景点坐标 -> 按天数区域聚类 -> 每日路径优化 -> 写入优化摘要 -> 缓存优化结果
```

前端结果页会展示 `optimization_summary`，用于说明区域聚类和路径优化效果。

## 技术栈

- 前端：Vue 3、TypeScript、Vite、Ant Design Vue、高德地图 JS API
- 后端：FastAPI、Pydantic、HelloAgents、SQLite
- 算法：K-Means 风格区域聚类、最近邻路径排序、2-opt 局部优化

## 简历描述参考

基于 Vue3、FastAPI、LLM Agent 和高德地图服务开发个性化旅行规划系统，实现景点检索、天气查询、酒店推荐、预算估算、地图可视化和 PDF 导出。设计区域聚类与路径优化模块，先根据经纬度将景点按旅行天数划分为多个游览区域，再采用最近邻与 2-opt 策略优化每日访问顺序；同时引入 SQLite 缓存机制复用 POI、天气、路线和优化结果，减少重复外部 API 调用并提升响应效率。

## 验证

后端语法检查：

```bash
python -m py_compile backend/app/services/cache_service.py backend/app/services/geo_utils.py backend/app/services/route_optimizer.py backend/app/services/cluster_service.py backend/app/services/itinerary_optimizer.py
```

前端构建：

```bash
cd frontend
npm run build
```
