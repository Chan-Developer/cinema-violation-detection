-- MySQL 初始化脚本
-- 设置字符集
ALTER DATABASE cinema_detection CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建表的字符集设置
CREATE TABLE IF NOT EXISTS user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    real_name VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    avatar VARCHAR(255),
    role_id INT,
    cinema_id INT,
    status INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 为现有表添加索引
CREATE INDEX idx_username ON user(username);
CREATE INDEX idx_role_id ON user(role_id);
CREATE INDEX idx_cinema_id ON user(cinema_id);
