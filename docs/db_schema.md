# 数据库结构导出

来源：当前项目 SQLAlchemy ORM 模型定义。

表数量：14

表列表：
- alarm_levels
- alarm_types
- cinemas
- roles
- halls
- users
- cameras
- seats
- alarms
- camera_status
- video_recognition_results
- video_streams
- alarm_action_logs
- alarm_notifications

## 1. alarm_levels
- id: INTEGER [PK, NOT NULL]
- name: VARCHAR(20) [NOT NULL, UNIQUE]
- code: VARCHAR(10) [NOT NULL, UNIQUE]
- priority: INTEGER
- color: VARCHAR(20)
- description: VARCHAR(100)

## 2. alarm_types
- id: INTEGER [PK, NOT NULL]
- name: VARCHAR(50) [NOT NULL, UNIQUE]
- code: VARCHAR(20) [NOT NULL, UNIQUE]
- description: VARCHAR(200)
- icon: VARCHAR(50)
- created_at: DATETIME

## 3. cinemas
- id: INTEGER [PK, NOT NULL]
- name: VARCHAR(100) [NOT NULL]
- address: VARCHAR(255)
- city: VARCHAR(50)
- district: VARCHAR(50)
- phone: VARCHAR(20)
- contact: VARCHAR(50)
- status: INTEGER
- created_at: DATETIME
- updated_at: DATETIME

## 4. roles
- id: INTEGER [PK, NOT NULL]
- name: VARCHAR(20) [NOT NULL, UNIQUE]
- description: VARCHAR(100)
- created_at: DATETIME

## 5. halls
- id: INTEGER [PK, NOT NULL]
- cinema_id: INTEGER [NOT NULL, FK -> cinemas.id]
- name: VARCHAR(50) [NOT NULL]
- hall_type: VARCHAR(20)
- rows: INTEGER
- cols: INTEGER
- total_seats: INTEGER
- status: INTEGER
- created_at: DATETIME
- updated_at: DATETIME

## 6. users
- id: INTEGER [PK, NOT NULL]
- username: VARCHAR(50) [NOT NULL, UNIQUE]
- password_hash: VARCHAR(255) [NOT NULL]
- real_name: VARCHAR(50)
- email: VARCHAR(100)
- phone: VARCHAR(20)
- role_id: INTEGER [FK -> roles.id]
- cinema_id: INTEGER [FK -> cinemas.id]
- status: INTEGER
- last_login: DATETIME
- created_at: DATETIME
- updated_at: DATETIME

## 7. cameras
- id: INTEGER [PK, NOT NULL]
- name: VARCHAR(100) [NOT NULL]
- cinema_id: INTEGER [NOT NULL, FK -> cinemas.id]
- hall_id: INTEGER [FK -> halls.id]
- rtsp_url: VARCHAR(500)
- username: VARCHAR(50)
- password: VARCHAR(100)
- position: VARCHAR(50)
- angle: FLOAT
- mount_height: FLOAT
- detection_enabled: INTEGER
- detection_types: VARCHAR(200)
- status: INTEGER
- stream_status: INTEGER
- manufacturer: VARCHAR(50)
- model: VARCHAR(50)
- ip_address: VARCHAR(50)
- port: INTEGER
- created_at: DATETIME
- updated_at: DATETIME

## 8. seats
- id: INTEGER [PK, NOT NULL]
- hall_id: INTEGER [NOT NULL, FK -> halls.id]
- row: VARCHAR(5) [NOT NULL]
- number: INTEGER [NOT NULL]
- seat_type: VARCHAR(20)
- status: INTEGER
- created_at: DATETIME

唯一约束：
- unique_seat(hall_id, row, number)

## 9. alarms
- id: INTEGER [PK, NOT NULL]
- alarm_type_id: INTEGER [NOT NULL, FK -> alarm_types.id]
- camera_id: INTEGER [NOT NULL, FK -> cameras.id]
- level_id: INTEGER [NOT NULL, FK -> alarm_levels.id]
- title: VARCHAR(200) [NOT NULL]
- description: TEXT
- location: VARCHAR(200)
- image_url: VARCHAR(500)
- video_url: VARCHAR(500)
- detection_box: VARCHAR(100)
- confidence: FLOAT
- status: INTEGER
- handler_id: INTEGER [FK -> users.id]
- handler_note: TEXT
- occurred_at: DATETIME
- confirmed_at: DATETIME
- resolved_at: DATETIME
- created_at: DATETIME
- updated_at: DATETIME

## 10. camera_status
- id: INTEGER [PK, NOT NULL]
- camera_id: INTEGER [NOT NULL, FK -> cameras.id]
- status: INTEGER
- cpu_usage: FLOAT
- memory_usage: FLOAT
- network_delay: FLOAT
- bitrate: INTEGER
- fps: FLOAT
- record_time: DATETIME

## 11. video_recognition_results
- id: INTEGER [PK, NOT NULL]
- task_id: VARCHAR(64) [NOT NULL]
- camera_id: INTEGER [FK -> cameras.id]
- cinema_id: INTEGER [FK -> cinemas.id]
- frame_index: INTEGER [NOT NULL]
- image_url: VARCHAR(500)
- person_count: INTEGER
- violation: BOOLEAN
- violation_codes: VARCHAR(200)
- llm_summary: TEXT
- llm_reply: TEXT
- created_at: DATETIME

## 12. video_streams
- id: INTEGER [PK, NOT NULL]
- camera_id: INTEGER [NOT NULL, UNIQUE, FK -> cameras.id]
- stream_url: VARCHAR(500)
- width: INTEGER
- height: INTEGER
- fps: FLOAT
- status: INTEGER
- error_message: VARCHAR(500)
- total_frames: INTEGER
- dropped_frames: INTEGER
- avg_latency: FLOAT
- auto_reconnect: INTEGER
- reconnect_interval: INTEGER
- max_reconnect: INTEGER
- started_at: DATETIME
- stopped_at: DATETIME
- created_at: DATETIME
- updated_at: DATETIME

## 13. alarm_action_logs
- id: INTEGER [PK, NOT NULL]
- alarm_id: INTEGER [NOT NULL, FK -> alarms.id]
- user_id: INTEGER [FK -> users.id]
- action: VARCHAR(50) [NOT NULL]
- from_status: INTEGER
- to_status: INTEGER
- note: TEXT
- created_at: DATETIME

## 14. alarm_notifications
- id: INTEGER [PK, NOT NULL]
- alarm_id: INTEGER [NOT NULL, FK -> alarms.id]
- user_id: INTEGER [NOT NULL, FK -> users.id]
- channel: VARCHAR(20)
- status: INTEGER
- sent_at: DATETIME
- read_at: DATETIME
- created_at: DATETIME

## 关系概览
- cinemas 1 -> n halls
- cinemas 1 -> n cameras
- cinemas 1 -> n users
- roles 1 -> n users
- halls 1 -> n seats
- halls 1 -> n cameras
- cameras 1 -> n alarms
- cameras 1 -> n camera_status
- cameras 1 -> 1 video_streams
- cameras 1 -> n video_recognition_results
- alarm_types 1 -> n alarms
- alarm_levels 1 -> n alarms
- alarms 1 -> n alarm_action_logs
- alarms 1 -> n alarm_notifications
- users 1 -> n alarm_notifications
- users 1 -> n alarms(handler_id)
