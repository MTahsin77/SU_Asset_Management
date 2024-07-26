-- Create the database
CREATE DATABASE IF NOT EXISTS suams_db;
USE suams_db;

-- Create Users table
CREATE TABLE Users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

-- Create Assets table
CREATE TABLE Assets (
    asset_id INT AUTO_INCREMENT PRIMARY KEY,
    asset_type VARCHAR(50) NOT NULL,
    asset_number VARCHAR(50) UNIQUE NOT NULL,
    location VARCHAR(100),
    room_number VARCHAR(20),
    purchase_date DATE,
    depreciation_date DATE
);

-- Create Allocations table
CREATE TABLE Allocations (
    allocation_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    asset_id INT,
    assigned_date DATE NOT NULL,
    return_date DATE,
    FOREIGN KEY (user_id) REFERENCES Users(user_id),
    FOREIGN KEY (asset_id) REFERENCES Assets(asset_id)
);

-- Create index for faster searches
CREATE INDEX idx_asset_number ON Assets(asset_number);
CREATE INDEX idx_user_name ON Users(name);
CREATE INDEX idx_allocation_dates ON Allocations(assigned_date, return_date);