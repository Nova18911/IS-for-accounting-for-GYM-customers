USE 2025_mysql_art;

-- Временно отключаем проверку внешних ключей
SET FOREIGN_KEY_CHECKS = 0;

-- Удаляем таблицы если они уже существуют (в обратном порядке зависимостей)
DROP TABLE IF EXISTS group_attendances;
DROP TABLE IF EXISTS personal_trainings;
DROP TABLE IF EXISTS group_trainings;
DROP TABLE IF EXISTS services;
DROP TABLE IF EXISTS halls;
DROP TABLE IF EXISTS clients;
DROP TABLE IF EXISTS subscriptions;
DROP TABLE IF EXISTS subscription_prices;
DROP TABLE IF EXISTS trainers;
DROP TABLE IF EXISTS trainer_types;
DROP TABLE IF EXISTS users;

-- 1. Создаем таблицы в правильном порядке (от независимых к зависимым)

-- Таблица залов
CREATE TABLE halls (
    hall_id INT PRIMARY KEY AUTO_INCREMENT,
    hall_name VARCHAR(30) NOT NULL UNIQUE,
    capacity INT
);

-- Таблица типов тренеров
CREATE TABLE trainer_types (
    trainer_type_id INT PRIMARY KEY AUTO_INCREMENT,
    trainer_type_name VARCHAR(50) NOT NULL UNIQUE,
    rate INT
);

CREATE TABLE trainers (
    trainer_id INT PRIMARY KEY AUTO_INCREMENT,
    last_name VARCHAR(50) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    middle_name VARCHAR(50),
    photo LONGBLOB,
    phone VARCHAR(20),
    email VARCHAR(50),
    trainer_type_id INT NOT NULL,
    FOREIGN KEY (trainer_type_id) REFERENCES trainer_types(trainer_type_id)
);


-- Таблица стоимости абонементов
CREATE TABLE subscription_prices (
    subscription_price_id INT PRIMARY KEY AUTO_INCREMENT,
    duration VARCHAR(50) NOT NULL UNIQUE,
    price VARCHAR(45) NOT NULL
);

-- Таблица абонементов
CREATE TABLE subscriptions (
    subscription_id INT PRIMARY KEY AUTO_INCREMENT,
    start_date DATE NOT NULL,
    subscription_price_id INT NOT NULL,
    FOREIGN KEY (subscription_price_id) REFERENCES subscription_prices(subscription_price_id)
);

-- Таблица клиентов
CREATE TABLE clients (
    client_id INT PRIMARY KEY AUTO_INCREMENT,
    last_name VARCHAR(50) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    middle_name VARCHAR(50),
    phone VARCHAR(20),
    email VARCHAR(100),
    photo LONGBLOB,
    subscription_id INT UNIQUE,
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(subscription_id)
);

-- Таблица услуг
CREATE TABLE services (
    service_id INT PRIMARY KEY AUTO_INCREMENT,
    service_name VARCHAR(100) NOT NULL UNIQUE,
    price INT,
    hall_id INT NOT NULL,
    FOREIGN KEY (hall_id) REFERENCES halls(hall_id)
);

-- Таблица групповых тренировок
CREATE TABLE group_trainings (
    group_training_id INT PRIMARY KEY AUTO_INCREMENT,
    training_date DATE NOT NULL,
    start_time TIME NOT NULL,
    trainer_id INT NOT NULL,
    service_id INT NOT NULL,
    FOREIGN KEY (trainer_id) REFERENCES trainers(trainer_id),
    FOREIGN KEY (service_id) REFERENCES services(service_id)
);

-- Таблица персональных тренировок
CREATE TABLE personal_trainings (
    personal_training_id INT PRIMARY KEY AUTO_INCREMENT,
    training_date DATE NOT NULL,
    start_time TIME NOT NULL,
    price INT,
    trainer_id INT NOT NULL,
    client_id INT NOT NULL,
    FOREIGN KEY (trainer_id) REFERENCES trainers(trainer_id),
    FOREIGN KEY (client_id) REFERENCES clients(client_id)
);

-- Таблица посещений групповых тренировок
CREATE TABLE group_attendances (
    attendance_id INT PRIMARY KEY AUTO_INCREMENT,
    group_training_id INT NOT NULL,
    client_id INT NOT NULL,
    attendance_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_training_id) REFERENCES group_trainings(group_training_id),
    FOREIGN KEY (client_id) REFERENCES clients(client_id)
);

-- Включаем проверку внешних ключей обратно
SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'reception', 'trainer') DEFAULT 'reception',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

INSERT INTO users (email, password_hash, role) VALUES
('admin@fitness.ru', SHA2('admin123', 256), 'admin'),
('reception@fitness.ru', SHA2('reception123', 256), 'reception');

-- Заполнение таблицы типов тренеров
INSERT INTO trainer_types (trainer_type_name, rate) VALUES
('Общий тренер', 2000),      -- Оклад 2000 за тренировку
('Групповой тренер', 1500),  -- Оклад 1500 за групповую тренировку
('Персональный тренер', 3000); -- Оклад 3000 за персональную тренировку

-- Заполнение таблицы стоимости абонементов
INSERT INTO subscription_prices (duration, price) VALUES
('1 месяц', 3000),    -- 3000 руб за месяц
('3 месяца', 8000),   -- 8000 руб за 3 месяца (скидка)
('полгода', 15000),   -- 15000 руб за полгода (скидка)
('год', 28000);       -- 28000 руб за год (скидка)
