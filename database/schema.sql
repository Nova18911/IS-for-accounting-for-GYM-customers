CREATE DATABASE fitness_club;

-- Таблица клиентов
CREATE TABLE clients (
    id INT PRIMARY KEY AUTO_INCREMENT,
    last_name VARCHAR(50) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    middle_name VARCHAR(50),
    phone VARCHAR(20),
    email VARCHAR(100),
    photo LONGBLOB,
    subscription_id INT UNIQUE, -- Обеспечивает только один активный абонемент
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id)
);

-- Таблица абонементов
CREATE TABLE subscriptions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    start_date DATE NOT NULL,
    subscription_price_id INT NOT NULL,
    status ENUM('active', 'expired', 'cancelled') DEFAULT 'active',
    end_date DATE,
    FOREIGN KEY (subscription_price_id) REFERENCES subscription_prices(id)
);

-- Добавляем внешний ключ после создания subscriptions
ALTER TABLE clients ADD FOREIGN KEY (subscription_id) REFERENCES subscriptions(id);

-- Таблица типов тренеров
CREATE TABLE trainer_types (
    id INT PRIMARY KEY AUTO_INCREMENT,
    type_name VARCHAR(50) NOT NULL UNIQUE -- 'персональный', 'групповой', 'общий'
);

-- Таблица тренеров
CREATE TABLE trainers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    last_name VARCHAR(50) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    middle_name VARCHAR(50),
    phone VARCHAR(20),
    photo LONGBLOB,
    rate DECIMAL(10,2),
    trainer_type_id INT NOT NULL,
    FOREIGN KEY (trainer_type_id) REFERENCES trainer_types(id)
);

-- Таблица залов
CREATE TABLE halls (
    id INT PRIMARY KEY AUTO_INCREMENT,
    capacity INT NOT NULL
);

-- Таблица услуг
CREATE TABLE services (
    id INT PRIMARY KEY AUTO_INCREMENT,
    service_name VARCHAR(100) NOT NULL,
    price DECIMAL(10,2),
    hall_id INT NOT NULL,
    FOREIGN KEY (hall_id) REFERENCES halls(id)
);

-- Таблица стоимости абонементов
CREATE TABLE subscription_prices (
    id INT PRIMARY KEY AUTO_INCREMENT,
    duration VARCHAR(50) NOT NULL, -- '1 месяц', '3 месяца'
    price DECIMAL(10,2) NOT NULL
);


-- Таблица групповых тренировок
CREATE TABLE group_trainings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    training_date DATE NOT NULL,
    start_time TIME NOT NULL,
    trainer_id INT NOT NULL,
    service_id INT NOT NULL,
    FOREIGN KEY (trainer_id) REFERENCES trainers(id),
    FOREIGN KEY (service_id) REFERENCES services(id)
);

-- Таблица персональных тренировок
CREATE TABLE personal_trainings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    training_date DATE NOT NULL,
    start_time TIME NOT NULL,
    price DECIMAL(10,2),
    trainer_id INT NOT NULL,
    client_id INT NOT NULL,
    FOREIGN KEY (trainer_id) REFERENCES trainers(id),
    FOREIGN KEY (client_id) REFERENCES clients(id)
);

-- Таблица посещений групповых тренировок
CREATE TABLE group_attendances (
    id INT PRIMARY KEY AUTO_INCREMENT,
    group_training_id INT NOT NULL,
    client_id INT NOT NULL,
    attendance_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_training_id) REFERENCES group_trainings(id),
    FOREIGN KEY (client_id) REFERENCES clients(id)
);