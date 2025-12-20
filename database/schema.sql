USE 2025_mysql_art;

SET FOREIGN_KEY_CHECKS = 0;

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


CREATE TABLE halls (
    hall_id INT PRIMARY KEY AUTO_INCREMENT,
    hall_name VARCHAR(30) NOT NULL UNIQUE,
    capacity INT
);


CREATE TABLE trainer_types (
    trainer_type_id INT PRIMARY KEY AUTO_INCREMENT,
    trainer_type_name VARCHAR(50) NOT NULL UNIQUE,
    rate DECIMAL(10, 2) NOT NULL
);


CREATE TABLE trainers (
    trainer_id INT PRIMARY KEY AUTO_INCREMENT,
    last_name VARCHAR(50) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    middle_name VARCHAR(50),
    photo LONGBLOB,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(50),
    trainer_type_id INT NOT NULL,
    FOREIGN KEY (trainer_type_id) REFERENCES trainer_types(trainer_type_id)
);


CREATE TABLE subscription_prices (
    subscription_price_id INT PRIMARY KEY AUTO_INCREMENT,
    duration VARCHAR(50) NOT NULL UNIQUE,
    price DECIMAL(10, 2) NOT NULL
);


CREATE TABLE subscriptions (
    subscription_id INT PRIMARY KEY AUTO_INCREMENT,
    start_date DATE NOT NULL DEFAULT CURRENT_DATE,
    subscription_price_id INT NOT NULL,
    FOREIGN KEY (subscription_price_id) REFERENCES subscription_prices(subscription_price_id)
);


CREATE TABLE clients (
    client_id INT PRIMARY KEY AUTO_INCREMENT,
    last_name VARCHAR(50) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    middle_name VARCHAR(50),
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(50),
    photo LONGBLOB,
    subscription_id INT UNIQUE,
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(subscription_id) ON DELETE CASCADE
);


CREATE TABLE services (
    service_id INT PRIMARY KEY AUTO_INCREMENT,
    service_name VARCHAR(100) NOT NULL UNIQUE,
    price DECIMAL(10, 2) NOT NULL,
    hall_id INT NOT NULL,
    FOREIGN KEY (hall_id) REFERENCES halls(hall_id) ON DELETE CASCADE
);


CREATE TABLE group_trainings (
    group_training_id INT PRIMARY KEY AUTO_INCREMENT,
    training_date DATE NOT NULL,
    start_time TIME NOT NULL,
    trainer_id INT NOT NULL,
    service_id INT NOT NULL,
    FOREIGN KEY (trainer_id) REFERENCES trainers(trainer_id),
    FOREIGN KEY (service_id) REFERENCES services(service_id) ON DELETE CASCADE
);


CREATE TABLE personal_trainings (
    personal_training_id INT PRIMARY KEY AUTO_INCREMENT,
    training_date DATE NOT NULL,
    start_time TIME NOT NULL,
    price DECIMAL(10, 2),
    trainer_id INT NOT NULL,
    client_id INT NOT NULL,
    FOREIGN KEY (trainer_id) REFERENCES trainers(trainer_id),
    FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE
);


CREATE TABLE group_attendances (
    attendance_id INT PRIMARY KEY AUTO_INCREMENT,
    group_training_id INT NOT NULL,
    client_id INT NOT NULL,
    FOREIGN KEY (group_training_id) REFERENCES group_trainings(group_training_id) ON DELETE CASCADE,
    FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE
);

SET FOREIGN_KEY_CHECKS = 1;

INSERT INTO trainer_types (trainer_type_name, rate) VALUES
('Общий тренер', 2000),
('Групповой тренер', 1500),
('Персональный тренер', 3000);

INSERT INTO subscription_prices (duration, price) VALUES
('1 месяц', 3000),
('3 месяца', 8000),
('полгода', 15000),
('год', 28000);