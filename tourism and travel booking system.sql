-- Fully corrected final SQL for Tourism_and_Travel_Booking_System
-- Run as a user with privileges to CREATE DATABASE and CREATE USER if you want the user/grant section.

-- ================================
-- 0) Cleanup (safe)
-- ================================
DROP DATABASE IF EXISTS Tourism_and_Travel_Booking_System;
CREATE DATABASE Tourism_and_Travel_Booking_System;
USE Tourism_and_Travel_Booking_System;

-- ================================
-- 1) TABLE CREATION (corrected)
-- ================================

-- Customers
CREATE TABLE Customer (
    CustomerID INT AUTO_INCREMENT PRIMARY KEY,
    Cname VARCHAR(100) NOT NULL,
    Email VARCHAR(150) UNIQUE,
    State VARCHAR(50),
    City VARCHAR(50),
    Street VARCHAR(100),
    Country VARCHAR(50),
    Refers INT NULL,
    CONSTRAINT fk_customer_refers FOREIGN KEY (Refers) REFERENCES Customer(CustomerID)
        ON DELETE SET NULL ON UPDATE CASCADE
);

-- TourPackage (NO BookingID here)
CREATE TABLE TourPackage (
    PackageID INT AUTO_INCREMENT PRIMARY KEY,
    PackageName VARCHAR(100) NOT NULL,
    PackagePrice DECIMAL(12,2) NOT NULL CHECK (PackagePrice >= 0),
    Duration INT NOT NULL,
    No_of_Travelers INT NOT NULL
);

-- Booking (references Package)
CREATE TABLE Booking (
    BookingID INT AUTO_INCREMENT PRIMARY KEY,
    BookingDate DATE NOT NULL,
    Status ENUM('Confirmed','Pending','Cancelled','Paid') DEFAULT 'Pending',
    CustomerID INT NOT NULL,
    PackageID INT NOT NULL,
    FOREIGN KEY (CustomerID) REFERENCES Customer(CustomerID) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (PackageID) REFERENCES TourPackage(PackageID) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Payment
CREATE TABLE Payment (
    PaymentID INT AUTO_INCREMENT PRIMARY KEY,
    Amount DECIMAL(12,2) NOT NULL CHECK (Amount >= 0),
    PaymentDate DATE NOT NULL,
    PaymentMethod VARCHAR(50),
    BookingID INT NOT NULL,
    FOREIGN KEY (BookingID) REFERENCES Booking(BookingID) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Destination
CREATE TABLE Destination (
    DestinationID INT AUTO_INCREMENT PRIMARY KEY,
    DestinationName VARCHAR(100) NOT NULL,
    Dlocation VARCHAR(100)
);

-- Hotel
CREATE TABLE Hotel (
    HotelID INT AUTO_INCREMENT PRIMARY KEY,
    HotelName VARCHAR(150) NOT NULL,
    Address VARCHAR(255),
    Rating DECIMAL(2,1),
    HotelPrice DECIMAL(12,2) CHECK (HotelPrice >= 0)
);

-- Transport (use DATETIME for accurate timings)
CREATE TABLE Transport (
    TransportID INT AUTO_INCREMENT PRIMARY KEY,
    TransportType VARCHAR(50) NOT NULL,
    DepartLocation VARCHAR(100),
    ArrivalLocation VARCHAR(100),
    DepartDateTime DATETIME,
    ArrivalDateTime DATETIME,
    TransportPrice DECIMAL(12,2) CHECK (TransportPrice >= 0)
);

-- TravelDependent
DROP TABLE IF EXISTS TravelDependent;

CREATE TABLE TravelDependent (
    DependentName VARCHAR(100) NOT NULL,
    Age INT CHECK (Age >= 0),
    Relation VARCHAR(50),
    CustomerID INT NOT NULL,
    FOREIGN KEY (CustomerID) REFERENCES Customer(CustomerID) ON DELETE CASCADE ON UPDATE CASCADE
);

-- GuestStayIn (Package - Hotel) M:N
CREATE TABLE GuestStayIn (
    PackageID INT,
    HotelID INT,
    PRIMARY KEY (PackageID, HotelID),
    FOREIGN KEY (PackageID) REFERENCES TourPackage(PackageID) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (HotelID) REFERENCES Hotel(HotelID) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Covers (Package - Destination) M:N
CREATE TABLE Covers (
    PackageID INT,
    DestinationID INT,
    PRIMARY KEY (PackageID, DestinationID),
    FOREIGN KEY (PackageID) REFERENCES TourPackage(PackageID) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (DestinationID) REFERENCES Destination(DestinationID) ON DELETE CASCADE ON UPDATE CASCADE
);

-- IncludesTravelBy (Package - Transport) M:N
CREATE TABLE IncludesTravelBy (
    PackageID INT,
    TransportID INT,
    PRIMARY KEY (PackageID, TransportID),
    FOREIGN KEY (PackageID) REFERENCES TourPackage(PackageID) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (TransportID) REFERENCES Transport(TransportID) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Customer phones (multivalued)
CREATE TABLE Cust_Phone (
    CustomerID INT,
    CPhone VARCHAR(20),
    PRIMARY KEY (CustomerID, CPhone),
    FOREIGN KEY (CustomerID) REFERENCES Customer(CustomerID) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Itinerary (ternary: Booking - Hotel - Transport)
CREATE TABLE Itinerary (
    BookingID INT,
    HotelID INT,
    TransportID INT,
    RoomType VARCHAR(50),
    CheckInDate DATE,
    CheckOutDate DATE,
    SeatClass VARCHAR(20),
    PRIMARY KEY (BookingID, HotelID, TransportID),
    FOREIGN KEY (BookingID) REFERENCES Booking(BookingID) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (HotelID) REFERENCES Hotel(HotelID) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (TransportID) REFERENCES Transport(TransportID) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- AppUser table for GUI authentication & roles
CREATE TABLE AppUser (
    UserID INT AUTO_INCREMENT PRIMARY KEY,
    Username VARCHAR(50) NOT NULL UNIQUE,
    PasswordHash VARCHAR(255) NOT NULL,
    Role ENUM('admin','agent','accountant') NOT NULL DEFAULT 'agent',
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================
-- 2) SAMPLE DATA INSERTION (order matters)
-- ================================

-- Customers
INSERT INTO Customer (CustomerID, Cname, Email, State, City, Street, Country, Refers) VALUES
(1, 'Siya Raj', 'siya@example.com', 'Karnataka', 'Bangalore', 'MG Road', 'India', NULL),
(2, 'Amit Sharma', 'amit@example.com', 'Delhi', 'New Delhi', 'CP', 'India', 1),
(3, 'Priya Nair', 'priya@example.com', 'Kerala', 'Kochi', 'Marine Drive', 'India', 1),
(4, 'John Doe', 'john@example.com', 'California', 'Los Angeles', 'Sunset Blvd', 'USA', 2),
(5, 'Meera Iyer', 'meera@example.com', 'Tamil Nadu', 'Chennai', 'T Nagar', 'India', 3);

-- TourPackages (must exist before bookings)
INSERT INTO TourPackage (PackageID, PackageName, PackagePrice, Duration, No_of_Travelers) VALUES
(301, 'Goa Delight', 20000.00, 5, 2),
(302, 'Kerala Backwaters', 30000.00, 7, 3),
(303, 'Rajasthan Royal', 45000.00, 10, 4),
(304, 'Dubai Luxury', 80000.00, 6, 2),
(305, 'Europe Explorer', 120000.00, 15, 5);

-- Booking (references PackageID)
INSERT INTO Booking (BookingID, BookingDate, Status, CustomerID, PackageID) VALUES
(101, '2025-01-10', 'Confirmed', 1, 301),
(102, '2025-02-15', 'Pending', 2, 302),
(103, '2025-03-20', 'Cancelled', 3, 303),
(104, '2025-04-05', 'Confirmed', 4, 304),
(105, '2025-05-12', 'Confirmed', 5, 305);

-- Payments
INSERT INTO Payment (PaymentID, Amount, PaymentDate, PaymentMethod, BookingID) VALUES
(201, 50000.00, '2025-01-11', 'Credit Card', 101),
(202, 25000.00, '2025-02-16', 'UPI', 102),
(203, 40000.00, '2025-03-21', 'Net Banking', 103),
(204, 60000.00, '2025-04-06', 'Cash', 104),
(205, 35000.00, '2025-05-13', 'Credit Card', 105);

-- Destinations
INSERT INTO Destination (DestinationID, DestinationName, Dlocation) VALUES
(401, 'Goa Beach', 'Goa'),
(402, 'Munnar', 'Kerala'),
(403, 'Jaipur Fort', 'Rajasthan'),
(404, 'Burj Khalifa', 'Dubai'),
(405, 'Eiffel Tower', 'Paris');

-- Hotels
INSERT INTO Hotel (HotelID, HotelName, Address, Rating, HotelPrice) VALUES
(501, 'Taj Goa', 'Goa Beach Road', 4.5, 8000.00),
(502, 'Munnar Resort', 'Tea Valley, Kerala', 4.2, 7000.00),
(503, 'Raj Palace', 'Jaipur, Rajasthan', 4.7, 10000.00),
(504, 'Atlantis Dubai', 'Palm Jumeirah, Dubai', 5.0, 20000.00),
(505, 'Hilton Paris', 'Champs-Élysées, Paris', 4.8, 15000.00);

-- Transports (use DATETIME; sample dates chosen to match bookings)
INSERT INTO Transport (TransportID, TransportType, DepartLocation, ArrivalLocation, DepartDateTime, ArrivalDateTime, TransportPrice) VALUES
(601, 'Flight', 'Bangalore', 'Goa', '2025-01-10 09:00:00', '2025-01-10 11:00:00', 5000.00),
(602, 'Train', 'Delhi', 'Kochi', '2025-02-15 14:00:00', '2025-02-15 22:00:00', 3000.00),
(603, 'Flight', 'Jaipur', 'Dubai', '2025-04-05 22:00:00', '2025-04-06 03:00:00', 25000.00),
(604, 'Flight', 'Delhi', 'Jaipur', '2025-03-20 10:00:00', '2025-03-20 11:30:00', 4000.00),
(605, 'Flight', 'Chennai', 'Paris', '2025-05-12 05:00:00', '2025-05-12 14:00:00', 50000.00);

-- Travel dependents
INSERT INTO TravelDependent (DependentName, Age, Relation, CustomerID) VALUES
('Riya Raj', 12, 'Daughter', 1),
('Ananya Sharma', 10, 'Daughter', 2),
('Arjun Nair', 15, 'Son', 3),
('Mary Doe', 35, 'Wife', 4),
('Karthik Iyer', 40, 'Husband', 5);

-- GuestStayIn (Package - Hotel)
INSERT INTO GuestStayIn (PackageID, HotelID) VALUES
(301, 501), (302, 502), (303, 503), (304, 504), (305, 505);

-- Covers (Package - Destination)
INSERT INTO Covers (PackageID, DestinationID) VALUES
(301, 401), (302, 402), (303, 403), (304, 404), (305, 405);

-- IncludesTravelBy (Package - Transport)
INSERT INTO IncludesTravelBy (PackageID, TransportID) VALUES
(301, 601), (302, 602), (303, 604), (304, 603), (305, 605);

-- Customer Phones
INSERT INTO Cust_Phone (CustomerID, CPhone) VALUES
(1, '9876543210'), (2, '9123456780'), (3, '9988776655'), (4, '9001122334'), (5, '7890654321');

-- Itinerary (Booking - Hotel - Transport) -- use matching valid IDs
INSERT INTO Itinerary (BookingID, HotelID, TransportID, RoomType, CheckInDate, CheckOutDate, SeatClass) VALUES
(101, 501, 601, 'Deluxe', '2025-01-10', '2025-01-15', 'Economy'),
(102, 502, 602, 'Suite', '2025-02-15', '2025-02-20', 'Business'),
(103, 503, 604, 'Standard', '2025-03-20', '2025-03-25', 'Economy'),
(104, 504, 603, 'Luxury', '2025-04-05', '2025-04-11', 'First Class'),
(105, 505, 605, 'Deluxe', '2025-05-12', '2025-05-27', 'Business');

-- ================================
-- 3) TRIGGERS
-- ================================
DELIMITER $$
CREATE TRIGGER trg_before_insert_dependent
BEFORE INSERT ON TravelDependent
FOR EACH ROW
BEGIN
    IF NEW.Age < 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid age for dependent';
    END IF;
END$$
DELIMITER ;

DELIMITER $$
CREATE TRIGGER trg_after_payment_insert
AFTER INSERT ON Payment
FOR EACH ROW
BEGIN
    UPDATE Booking SET Status = 'Paid' WHERE BookingID = NEW.BookingID;
END$$
DELIMITER ;

-- ================================
-- 4) STORED PROCEDURES & FUNCTION
-- ================================

-- get bookings by customer (returns bookings + package info + optional payment)
DROP PROCEDURE IF EXISTS get_bookings_by_customer;
DELIMITER $$
CREATE PROCEDURE get_bookings_by_customer (IN in_customer_id INT)
BEGIN
    SELECT b.BookingID, b.BookingDate, b.Status,
           tp.PackageID, tp.PackageName, tp.PackagePrice,
           COALESCE(p.Amount,0) AS SamplePaymentAmount
    FROM Booking b
    JOIN TourPackage tp ON b.PackageID = tp.PackageID
    LEFT JOIN Payment p ON p.BookingID = b.BookingID
    WHERE b.CustomerID = in_customer_id;
END$$
DELIMITER ;

-- calculate estimated package total cost (sample join)
DROP PROCEDURE IF EXISTS calculate_package_total_cost;
DELIMITER $$
CREATE PROCEDURE calculate_package_total_cost (IN in_package_id INT)
BEGIN
    SELECT p.PackageName,
           p.PackagePrice AS PackagePrice,
           COALESCE(h.HotelPrice,0) AS SampleHotelPrice,
           COALESCE(t.TransportPrice,0) AS SampleTransportPrice,
           (p.PackagePrice + COALESCE(h.HotelPrice,0) + COALESCE(t.TransportPrice,0)) AS EstimatedTotal
    FROM TourPackage p
    LEFT JOIN GuestStayIn g ON p.PackageID = g.PackageID
    LEFT JOIN Hotel h ON g.HotelID = h.HotelID
    LEFT JOIN IncludesTravelBy it ON p.PackageID = it.PackageID
    LEFT JOIN Transport t ON it.TransportID = t.TransportID
    WHERE p.PackageID = in_package_id
    LIMIT 1;
END$$
DELIMITER ;

-- count dependents function
DROP FUNCTION IF EXISTS fn_count_dependents;
DELIMITER $$
CREATE FUNCTION fn_count_dependents(in_customer_id INT) RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE cnt INT;
    SELECT COUNT(*) INTO cnt FROM TravelDependent WHERE CustomerID = in_customer_id;
    RETURN IFNULL(cnt,0);
END$$
DELIMITER ;

DROP FUNCTION IF EXISTS TotalAmountSpent;

DELIMITER $$
CREATE FUNCTION TotalAmountSpent(cust_id INT)
RETURNS DECIMAL(10,2)
DETERMINISTIC
BEGIN
    DECLARE total DECIMAL(10,2);

    SELECT SUM(p.Amount)
    INTO total
    FROM Payment p
    JOIN Booking b ON p.BookingID = b.BookingID
    WHERE b.CustomerID = cust_id;

    RETURN IFNULL(total, 0);
END$$
DELIMITER ;






-- ================================
-- 5) VIEWS (useful for GUI / reports)
-- ================================
CREATE OR REPLACE VIEW vw_booking_details AS
SELECT b.BookingID, b.BookingDate, b.Status,
       c.CustomerID, c.Cname,
       tp.PackageID, tp.PackageName, tp.PackagePrice
FROM Booking b
JOIN Customer c ON b.CustomerID = c.CustomerID
JOIN TourPackage tp ON b.PackageID = tp.PackageID;

CREATE OR REPLACE VIEW vw_package_transport AS
SELECT tp.PackageID, tp.PackageName, t.TransportID, t.TransportType, t.DepartDateTime, t.ArrivalDateTime, t.TransportPrice
FROM TourPackage tp
JOIN IncludesTravelBy it ON tp.PackageID = it.PackageID
JOIN Transport t ON it.TransportID = t.TransportID;

-- ================================
-- 6) OPTIONAL: Create MySQL users + grants for role-based DB connections
--     (Run as root or admin user; edit passwords before using in production)
-- ================================
-- NOTE: If you already created these users, skip or adjust the passwords.
CREATE USER IF NOT EXISTS 'admin'@'localhost' IDENTIFIED BY 'admin';
CREATE USER IF NOT EXISTS 'agent'@'localhost' IDENTIFIED BY 'agent';
CREATE USER IF NOT EXISTS 'accountant'@'localhost' IDENTIFIED BY 'accountant';

GRANT ALL PRIVILEGES ON Tourism_and_Travel_Booking_System.* TO 'admin'@'localhost';

-- agent: 
GRANT SELECT, INSERT, UPDATE, DELETE ON Tourism_and_Travel_Booking_System.Customer TO 'agent'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON Tourism_and_Travel_Booking_System.Booking TO 'agent'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON Tourism_and_Travel_Booking_System.TourPackage TO 'agent'@'localhost';
GRANT SELECT ON Tourism_and_Travel_Booking_System.Payment TO 'agent'@'localhost';
GRANT SELECT ON Tourism_and_Travel_Booking_System.Hotel TO 'agent'@'localhost';
GRANT SELECT ON Tourism_and_Travel_Booking_System.Destination TO 'agent'@'localhost';
GRANT SELECT ON Tourism_and_Travel_Booking_System.Transport TO 'agent'@'localhost';


-- accountant: 
GRANT SELECT, INSERT, UPDATE ON Tourism_and_Travel_Booking_System.Payment TO 'accountant'@'localhost';
GRANT SELECT ON Tourism_and_Travel_Booking_System.Booking TO 'accountant'@'localhost';
GRANT SELECT ON Tourism_and_Travel_Booking_System.Customer TO 'accountant'@'localhost';
GRANT SELECT ON Tourism_and_Travel_Booking_System.TourPackage TO 'accountant'@'localhost';
GRANT SELECT ON Tourism_and_Travel_Booking_System.Hotel TO 'accountant'@'localhost';
GRANT SELECT ON Tourism_and_Travel_Booking_System.Destination TO 'accountant'@'localhost';
GRANT SELECT ON Tourism_and_Travel_Booking_System.Transport TO 'accountant'@'localhost';


FLUSH PRIVILEGES;

-- ================================
-- 7) OPTIONAL: Insert default admin AppUser (idempotent)
--    (UNCOMMENT if you want to create an app admin row from SQL.
--     Prefer creating via GUI which hashes the password.)
-- ================================
/*
INSERT INTO AppUser (Username, PasswordHash, Role)
SELECT 'admin', '$2b$12$ZqHcQTImZCwFZsP2bK8Q..9G49gZWx3d6/MS7D9m5Ia8g7aSSTbB6', 'admin'
WHERE NOT EXISTS (SELECT 1 FROM AppUser WHERE Username='admin');
-- Note: the hash above is bcrypt for "admin123". You can replace with your own.
*/

-- ================================
-- 8) EXAMPLE QUERIES (nested, join, aggregate)
-- ================================

-- a) Top 3 packages (by price) — simple and rubric-friendly
SELECT t.PackageName, t.PackagePrice
FROM TourPackage t
JOIN (
    SELECT DISTINCT PackagePrice
    FROM TourPackage
    ORDER BY PackagePrice DESC
    LIMIT 3
) AS top3
    ON t.PackagePrice = top3.PackagePrice
ORDER BY t.PackagePrice DESC;


-- b) Join: bookings with itinerary hotel
SELECT b.BookingID, c.Cname, h.HotelName, h.Rating
FROM Booking b
JOIN Customer c ON b.CustomerID = c.CustomerID
JOIN Itinerary i ON b.BookingID = i.BookingID
JOIN Hotel h ON i.HotelID = h.HotelID;

-- c) Aggregate: Total dependents per customer
SELECT c.Cname, COUNT(td.DependentName) AS Total_Dependents
FROM Customer c
LEFT JOIN TravelDependent td ON c.CustomerID = td.CustomerID
GROUP BY c.CustomerID;




-- ================================
-- 9) SAMPLE CALLS to test procedures / views
-- ================================
SELECT TotalAmountSpent(1);
CALL get_bookings_by_customer(1);
CALL calculate_package_total_cost(301);
SELECT * FROM vw_booking_details LIMIT 20;
SELECT * FROM vw_package_transport LIMIT 20;
