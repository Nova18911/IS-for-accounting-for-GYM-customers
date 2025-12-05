CREATE TABLE users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'reception', 'trainer') DEFAULT 'reception',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

INSERT INTO users (email, password_hash, role) VALUES
-- Администратор (пароль: admin123)
('admin@fitness.ru', SHA2('admin123', 256), 'admin'),
-- Ресепшн (пароль: reception123)
('reception@fitness.ru', SHA2('reception123', 256), 'reception'),