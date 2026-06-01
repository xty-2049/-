# 云途智旅

本项目是一个基于 Vue 3、FastAPI、HelloAgents 和高德地图能力的个性化旅行规划系统。系统支持根据城市、日期、交通方式、住宿偏好和兴趣标签生成旅行计划，并展示地图路线、预算明细、天气信息和导出结果。

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


系统在 LLM 生成初始行程后，会自动执行：

```text
收集景点坐标 -> 按天数区域聚类 -> 每日路径优化 -> 写入优化摘要 -> 缓存优化结果
```

前端结果页会展示 `optimization_summary`，用于说明区域聚类和路径优化效果。

## 技术栈

- 前端：Vue 3、TypeScript、Vite、Ant Design Vue、高德地图 JS API
- 后端：FastAPI、Pydantic、HelloAgents、SQLite
- 算法：K-Means 风格区域聚类、最近邻路径排序、2-opt 局部优化

## 图片效果预览：
<img width="2550" height="1379" alt="0ff7a28a135815c507eb08dd3b4976ca" src="https://github.com/user-attachments/assets/7ecd30e4-72b4-4e4d-a30d-c48148f0ea0f" />
<img width="1876" height="1238" alt="bd8e353c5054fdcdcee8f4f363d9ca07" src="https://github.com/user-attachments/assets/bc3ad8d9-c6b7-46dd-ac99-0a2d6e5791f8" />


