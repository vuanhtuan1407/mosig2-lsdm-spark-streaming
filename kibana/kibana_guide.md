# Kibana Dashboard Setup Guide

## Index Patterns Setup

### 1. Create Index Patterns (Stack Management > Index Patterns)

```bash
# Index Pattern 1: Basic Task Events
Name: metrics-task-events-*
Time field: window_start
Description: Real-time task event counts and distribution

# Index Pattern 2: Scheduling Delays  
Name: metrics-scheduling-delays-*
Time field: window_start
Description: Task scheduling delay metrics with anomaly detection

# Index Pattern 3: Resource Utilization
Name: metrics-resources-*
Time field: window_start
Description: Machine resource utilization tracking
```

---

## Dashboard Visualizations

### **Dashboard 1: Real-time Monitoring Overview**

#### Visualization 1: Event Count Timeline
```
Type: Line Chart
Index: metrics-task-events-*
Metrics:
  - Y-axis: Sum of event_count
Buckets:
  - X-axis: Date Histogram on window_start (interval: auto)
  - Split series: Terms on event_type.keyword
```

#### Visualization 2: Event Type Distribution (Pie Chart)
```
Type: Pie Chart
Index: metrics-task-events-*
Metrics:
  - Slice size: Sum of event_count
Buckets:
  - Split slices: Terms on event_type.keyword (size: 10)
```

#### Visualization 3: Active Jobs & Machines
```
Type: Metric
Index: metrics-task-events-*
Metrics:
  - Metric 1: Average of unique_jobs (Label: "Active Jobs")
  - Metric 2: Average of unique_machines (Label: "Active Machines")
```

---

### **Dashboard 2: Scheduling Performance**

#### Visualization 4: Scheduling Delay Percentiles
```
Type: Line Chart
Index: metrics-scheduling-delays-*
Metrics:
  - Y-axis 1: Average of p50_delay (Label: "P50")
  - Y-axis 2: Average of p95_delay (Label: "P95")
  - Y-axis 3: Average of p99_delay (Label: "P99")
Buckets:
  - X-axis: Date Histogram on window_start (interval: auto)
```

#### Visualization 5: Average Delay by Priority
```
Type: Area Chart
Index: metrics-scheduling-delays-*
Metrics:
  - Y-axis: Average of avg_delay
Buckets:
  - X-axis: Date Histogram on window_start
  - Split series: Terms on priority
```

#### Visualization 6: SLA Violations (Gauge)
```
Type: Gauge
Index: metrics-scheduling-delays-*
Metrics:
  - Metric: Sum of sla_violation_count
Goal: 0 (green), Warning: 5 (yellow), Critical: 10 (red)
```

#### Visualization 7: Anomaly Heatmap
```
Type: Heat Map
Index: metrics-scheduling-delays-*
Metrics:
  - Value: Max of anomaly_score
Buckets:
  - Y-axis: Terms on priority
  - X-axis: Date Histogram on window_start
```

---

### **Dashboard 3: Anomaly Detection**

#### Visualization 8: Anomaly Timeline
```
Type: Line Chart with Threshold
Index: metrics-scheduling-delays-*
Metrics:
  - Y-axis: Max of anomaly_score
Buckets:
  - X-axis: Date Histogram on window_start
Threshold line: 5.0 (anomaly threshold)
```

#### Visualization 9: Anomaly Alerts Table
```
Type: Data Table
Index: metrics-scheduling-delays-*
Columns:
  - window_start
  - priority
  - scheduling_class
  - avg_delay
  - max_delay
  - anomaly_score
  - is_anomaly
Filter: is_anomaly = true
Sort: anomaly_score (descending)
```

#### Visualization 10: Tasks with High Delays
```
Type: Bar Chart (Horizontal)
Index: metrics-scheduling-delays-*
Metrics:
  - X-axis: Average of max_delay
Buckets:
  - Y-axis: Terms on priority (order by metric: descending)
  - Split series: Terms on scheduling_class
```

---

### **Dashboard 4: Resource Utilization**

#### Visualization 11: CPU Usage by Machine
```
Type: Area Chart
Index: metrics-resources-*
Metrics:
  - Y-axis: Average of avg_cpu
Buckets:
  - X-axis: Date Histogram on window_start
  - Split series: Terms on machine_ID (top 10)
```

#### Visualization 12: Memory Usage by Machine
```
Type: Line Chart
Index: metrics-resources-*
Metrics:
  - Y-axis: Average of avg_memory
Buckets:
  - X-axis: Date Histogram on window_start
  - Split series: Terms on machine_ID (top 10)
```

#### Visualization 13: Top Resource Consumers
```
Type: Data Table
Index: metrics-resources-*
Columns:
  - machine_ID
  - scheduled_tasks (sum)
  - total_cpu (sum)
  - total_memory (sum)
Group by: machine_ID
Sort: total_cpu (descending)
```

#### Visualization 14: Machine Utilization Heatmap
```
Type: Heat Map
Index: metrics-resources-*
Metrics:
  - Value: Sum of scheduled_tasks
Buckets:
  - Y-axis: Terms on machine_ID
  - X-axis: Date Histogram on window_start (interval: 1m)
```

---

## Complete Dashboard Layout

### Dashboard: **Cluster Monitoring Overview**

```
┌──────────────────────────────────────────────────────────┐
│  Time Range Selector: Last 15 minutes (auto-refresh 10s) │
├──────────────────────────────────────────────────────────┤
│  [Metric: Active Jobs] [Metric: Active Machines]         │
├──────────────────────────────────────────────────────────┤
│  Event Count Timeline (full width)                       │
├──────────────────────────────────────────────────────────┤
│  [Event Type Pie]  │  [SLA Violations Gauge]             │
├──────────────────────────────────────────────────────────┤
│  Scheduling Delay Percentiles (P50/P95/P99)              │
├──────────────────────────────────────────────────────────┤
│  [CPU Usage Chart] │ [Memory Usage Chart]                │
├──────────────────────────────────────────────────────────┤
│  Anomaly Alerts Table (collapsed by default)             │
└──────────────────────────────────────────────────────────┘
```

---

## Alerting Setup (Kibana Alerting)

### Alert 1: High Scheduling Delay
```
Alert Type: Index Threshold
Index: metrics-scheduling-delays-*
Conditions:
  - WHEN average p95_delay
  - OVER all documents
  - FOR THE LAST 5 minutes
  - IS ABOVE 60 seconds
Actions:
  - Log to console
  - Send webhook (if Slack configured)
```

### Alert 2: Anomaly Detected
```
Alert Type: Index Threshold
Index: metrics-scheduling-delays-*
Conditions:
  - WHEN max anomaly_score
  - OVER all documents
  - FOR THE LAST 1 minute
  - IS ABOVE 5
Actions:
  - Create case
  - Send email notification
```

### Alert 3: High Resource Usage
```
Alert Type: Index Threshold
Index: metrics-resources-*
Conditions:
  - WHEN average avg_cpu
  - GROUPED BY machine_ID
  - FOR THE LAST 5 minutes
  - IS ABOVE 0.8
Actions:
  - Log warning
```

---

## Kibana Dev Tools Queries

### Query 1: Get Latest Metrics
```json
GET metrics-scheduling-delays-*/_search
{
  "size": 10,
  "sort": [
    { "window_start": "desc" }
  ],
  "query": {
    "range": {
      "window_start": {
        "gte": "now-15m"
      }
    }
  }
}
```

### Query 2: Find Anomalies
```json
GET metrics-scheduling-delays-*/_search
{
  "query": {
    "bool": {
      "must": [
        { "term": { "is_anomaly": true } },
        { "range": { "window_start": { "gte": "now-1h" } } }
      ]
    }
  },
  "sort": [
    { "anomaly_score": "desc" }
  ]
}
```

### Query 3: Aggregate by Priority
```json
GET metrics-scheduling-delays-*/_search
{
  "size": 0,
  "query": {
    "range": {
      "window_start": { "gte": "now-1h" }
    }
  },
  "aggs": {
    "by_priority": {
      "terms": { "field": "priority" },
      "aggs": {
        "avg_delay": { "avg": { "field": "avg_delay" } },
        "p95_delay": { "avg": { "field": "p95_delay" } }
      }
    }
  }
}
```

---

## Quick Start Checklist

- [ ] Start Spark streaming job
- [ ] Wait 2-3 minutes for data to flow
- [ ] Open Kibana: http://localhost:5601
- [ ] Create 3 index patterns (task-events, scheduling-delays, resources)
- [ ] Import or create visualizations above
- [ ] Create dashboard and arrange panels
- [ ] Set auto-refresh to 10 seconds
- [ ] Configure alerts (optional)
- [ ] Save and share dashboard

---

## Pro Tips

1. **Auto-refresh**: Set dashboard refresh to 10s for real-time monitoring
2. **Time range**: Use "Last 15 minutes" for live monitoring, "Last 24 hours" for analysis
3. **Filters**: Add priority/scheduling_class filters to drill down
4. **Drill-downs**: Click on chart elements to filter other visualizations
5. **Saved searches**: Create saved searches for common anomaly queries
6. **Color coding**: 
   - Green: Normal (delay < 30s)
   - Yellow: Warning (30s < delay < 60s)
   - Red: Critical (delay > 60s or anomaly detected)

---

## Color Palette Suggestion

```
Priority Colors:
- Priority 0-3 (High):    #E74C3C (Red)
- Priority 4-7 (Medium):  #F39C12 (Orange)  
- Priority 8-11 (Low):    #3498DB (Blue)

Event Type Colors:
- SUBMIT (0):   #2ECC71 (Green)
- SCHEDULE (1): #3498DB (Blue)
- EVICT (2):    #F39C12 (Orange)
- FAIL (3):     #E74C3C (Red)
- FINISH (4):   #9B59B6 (Purple)

Anomaly Colors:
- Normal:       #2ECC71 (Green)
- Warning:      #F39C12 (Orange)
- Critical:     #E74C3C (Red)
```

---

## Expected Dashboard Screenshots

Your dashboard should show:
1. ✅ Real-time event counts trending upward
2. ✅ Scheduling delays mostly under 30 seconds
3. ✅ P95 and P99 spike detection
4. ✅ Anomaly score usually 0, spikes to >5 during issues
5. ✅ Resource utilization balanced across machines
6. ✅ SLA violations counter (should be low)

**Happy Monitoring!**