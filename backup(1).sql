-- MySQL dump 10.13  Distrib 8.0.46, for Linux (x86_64)
--
-- Host: localhost    Database: cityscope_accounts
-- ------------------------------------------------------
-- Server version	8.0.46

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `advances`
--

DROP TABLE IF EXISTS `advances`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `advances` (
  `id` int NOT NULL AUTO_INCREMENT,
  `employee_id` int NOT NULL,
  `advance_type` enum('SALARY','COMMISSION') NOT NULL,
  `amount` double NOT NULL,
  `advance_date` date NOT NULL,
  `reason` text,
  `status` enum('ACTIVE','SETTLED') NOT NULL DEFAULT 'ACTIVE',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `employee_id` (`employee_id`),
  CONSTRAINT `advances_ibfk_1` FOREIGN KEY (`employee_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `advances`
--

LOCK TABLES `advances` WRITE;
/*!40000 ALTER TABLE `advances` DISABLE KEYS */;
/*!40000 ALTER TABLE `advances` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `commission_payments`
--

DROP TABLE IF EXISTS `commission_payments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `commission_payments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `transaction_id` int NOT NULL,
  `party` enum('BUYER','SELLER') NOT NULL,
  `amount` double NOT NULL,
  `payment_date` date NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `transaction_id` (`transaction_id`),
  CONSTRAINT `commission_payments_ibfk_1` FOREIGN KEY (`transaction_id`) REFERENCES `transactions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=76 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `commission_payments`
--

LOCK TABLES `commission_payments` WRITE;
/*!40000 ALTER TABLE `commission_payments` DISABLE KEYS */;
INSERT INTO `commission_payments` VALUES (73,39,'BUYER',17500,'2026-09-13','2026-09-13 16:47:13'),(74,39,'SELLER',17500,'2026-09-13','2026-09-13 16:47:13'),(75,41,'SELLER',35000,'2026-06-17','2026-09-18 16:25:50');
/*!40000 ALTER TABLE `commission_payments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `commission_payouts`
--

DROP TABLE IF EXISTS `commission_payouts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `commission_payouts` (
  `id` int NOT NULL AUTO_INCREMENT,
  `transaction_id` int NOT NULL,
  `employee_id` int NOT NULL,
  `amount` double NOT NULL,
  `paid_date` date NOT NULL,
  `notes` text,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `transaction_id` (`transaction_id`),
  KEY `employee_id` (`employee_id`),
  CONSTRAINT `commission_payouts_ibfk_1` FOREIGN KEY (`transaction_id`) REFERENCES `transactions` (`id`) ON DELETE CASCADE,
  CONSTRAINT `commission_payouts_ibfk_2` FOREIGN KEY (`employee_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `commission_payouts`
--

LOCK TABLES `commission_payouts` WRITE;
/*!40000 ALTER TABLE `commission_payouts` DISABLE KEYS */;
/*!40000 ALTER TABLE `commission_payouts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `leave_requests`
--

DROP TABLE IF EXISTS `leave_requests`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `leave_requests` (
  `id` int NOT NULL AUTO_INCREMENT,
  `employee_id` int NOT NULL,
  `date_of_leave` date NOT NULL,
  `applied_on` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `reason` text,
  `status` enum('PENDING','APPROVED','REJECTED') NOT NULL DEFAULT 'PENDING',
  `blocked` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `employee_id` (`employee_id`),
  CONSTRAINT `leave_requests_ibfk_1` FOREIGN KEY (`employee_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `leave_requests`
--

LOCK TABLES `leave_requests` WRITE;
/*!40000 ALTER TABLE `leave_requests` DISABLE KEYS */;
INSERT INTO `leave_requests` VALUES (4,3,'2026-09-22','2026-09-19 09:56:23','Personal work','APPROVED',0),(5,8,'2026-09-24','2026-09-21 16:13:48','Out of city','APPROVED',0),(9,5,'2026-09-25','2026-09-22 18:30:07','Half day in second half','APPROVED',0),(10,4,'2026-10-18','2026-09-25 10:06:55','Out of baroda for Nivedh puja','APPROVED',0),(11,4,'2026-10-19','2026-09-25 10:07:11','Out of baroda for Nivedh puja','APPROVED',0),(12,4,'2026-10-20','2026-09-25 10:07:27','Out of baroda for Nivedh puja','APPROVED',0),(14,10,'2026-10-03','2026-09-30 21:41:18','I\'m taking a leave on 3rd of October,2026\r\n(SATURDAY) due to some personal reasons.','APPROVED',0);
/*!40000 ALTER TABLE `leave_requests` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `transactions`
--

DROP TABLE IF EXISTS `transactions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `transactions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `property_id` varchar(255) NOT NULL,
  `property_name` varchar(255) NOT NULL,
  `cityscope_commission` double NOT NULL,
  `buyer_commission_amount` double NOT NULL DEFAULT '0',
  `seller_commission_amount` double NOT NULL DEFAULT '0',
  `gst_applied` tinyint(1) NOT NULL DEFAULT '0',
  `net_commission` double NOT NULL,
  `employee_commission` double NOT NULL,
  `payment_status` enum('PENDING','PARTIAL','DONE') NOT NULL DEFAULT 'PENDING',
  `transaction_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `month` int NOT NULL,
  `year` int NOT NULL,
  `quarter` int NOT NULL,
  `employee_id` int NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `buyer_commission_received` double NOT NULL DEFAULT '0',
  `buyer_commission_date` date DEFAULT NULL,
  `seller_commission_received` double NOT NULL DEFAULT '0',
  `seller_commission_date` date DEFAULT NULL,
  `basic_price` double NOT NULL DEFAULT '0',
  `buyer_gst_applied` tinyint(1) NOT NULL DEFAULT '0',
  `seller_gst_applied` tinyint(1) NOT NULL DEFAULT '0',
  `buyer_name` varchar(255) DEFAULT NULL,
  `seller_name` varchar(255) DEFAULT NULL,
  `buyer_is_broker` tinyint(1) NOT NULL DEFAULT '0',
  `seller_is_broker` tinyint(1) NOT NULL DEFAULT '0',
  `emp_payout_status` enum('UNPAID','PAID') NOT NULL DEFAULT 'UNPAID',
  PRIMARY KEY (`id`),
  KEY `employee_id` (`employee_id`),
  CONSTRAINT `transactions_ibfk_1` FOREIGN KEY (`employee_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=47 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `transactions`
--

LOCK TABLES `transactions` WRITE;
/*!40000 ALTER TABLE `transactions` DISABLE KEYS */;
INSERT INTO `transactions` VALUES (38,'CSID4387','A-3 Jay Shree Narayan Nagar',137000,137000,0,0,0,0,'PENDING','2026-09-04 00:00:00',9,2026,2,10,'2026-09-12 16:58:56','2026-09-12 16:58:56',0,NULL,0,NULL,6850000,0,0,'Raju Ravidas','Akshar Estate[Bhavesh M Jadav]',0,1,'UNPAID'),(39,'CSID2786','B-403 Gangotri Green',35000,17500,17500,0,35000,5133.1,'DONE','2026-09-05 00:00:00',9,2026,2,12,'2026-09-12 17:03:17','2026-09-24 10:44:43',17500,'2026-09-13',17500,'2026-09-13',17500,0,0,'Mineshwari Jadav','Jasmine Kaur Nagi',0,0,'UNPAID'),(40,'CSID4459','85-86 Gulmohar West',30000,15000,15000,0,0,0,'PENDING','2026-09-07 00:00:00',9,2026,2,12,'2026-09-12 17:03:57','2026-09-12 17:03:57',0,NULL,0,NULL,15000,0,0,'Sanjay Parmar','Sudhaker Dev',0,0,'UNPAID'),(41,'CSID4441','B-24 Avalons Greenwoods',70000,0,70000,0,35000,5133.1,'PARTIAL','2026-09-09 00:00:00',9,2026,2,12,'2026-09-12 17:07:19','2026-09-24 10:44:43',0,NULL,35000,'2026-06-17',75000,0,0,'Dhruv Patel','Jay Pratap Sinh',1,0,'UNPAID'),(42,'CSID3486','18 Shree Hari Residency',340000,170000,170000,0,0,0,'PENDING','2026-09-14 00:00:00',9,2026,2,4,'2026-09-17 10:48:22','2026-09-17 10:48:22',0,NULL,0,NULL,8500000,0,0,'Lalit Dwivedi','Madhvi Pradhan',0,0,'UNPAID'),(43,'CSID1','D-802 Darshanam Prospera',72000,0,72000,0,0,0,'PENDING','2026-09-17 00:00:00',9,2026,2,7,'2026-09-18 16:23:41','2026-09-18 16:23:41',0,NULL,0,NULL,3600000,0,0,'Rahul Solanki','Builder',0,0,'UNPAID'),(44,'CSID2045','A-69 Darshanam Revanta',30000,15000,15000,0,0,0,'PENDING','2026-09-23 00:00:00',9,2026,2,12,'2026-09-24 10:44:43','2026-09-24 10:44:43',0,NULL,0,NULL,15000,0,0,'Nikunj Kavan','Manav Gupta',0,0,'UNPAID'),(45,'CSID2','GF-B30/1 Sonal Park Society',32000,16000,16000,0,0,0,'PENDING','2026-09-25 00:00:00',9,2026,2,13,'2026-09-28 09:55:12','2026-09-28 09:55:12',0,NULL,0,NULL,16000,0,0,'Nirmal Patel','Rajendra Pawar',0,0,'UNPAID'),(46,'CSID3','B-301 Samipya Enclave',17000,17000,0,0,0,0,'PENDING','2026-09-15 00:00:00',9,2026,2,11,'2026-09-28 10:03:06','2026-09-28 10:03:06',0,NULL,0,NULL,17000,0,0,'Sabita Manoj Bangera',NULL,0,1,'UNPAID');
/*!40000 ALTER TABLE `transactions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` enum('ADMIN','EMPLOYEE') NOT NULL DEFAULT 'EMPLOYEE',
  `team_type` enum('CORE_TEAM','NORMAL_TEAM','RENT_TEAM') DEFAULT NULL,
  `salary` double NOT NULL DEFAULT '0',
  `target_multiplier` double NOT NULL DEFAULT '7',
  `commission_rate` double NOT NULL DEFAULT '0.2',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'Admin','admin@cityscope.in','scrypt:32768:8:1$qstOqSHQrxYhEtFB$cb8f0361bf61c46a4d2e22cf5d5650d534802c5ad3cca3e843f8df9dbc398b3949168dffe7619311f240c11ba08421102ca4c67aaaa26f3600f3d2da29450908','ADMIN',NULL,0,7,0.2,'2026-08-29 10:06:42'),(2,'D Mistry','dmistry@cityscope.in','scrypt:32768:8:1$0lRiJ9lBoiOmMxcH$067e2d1b89b30580e6ef88ba7e920975873cc10d58c6291e6ae8a477136c9867ed0e4a54518402893c018db7f06409d435aa7b701c1a614a0227ccfc99917db4','ADMIN',NULL,0,7,0.2,'2026-08-29 10:28:08'),(3,'Hiral','hiralpatel.co.in@gmail.com','scrypt:32768:8:1$KEsV9LPRtlKIE02f$95488f38573cffbcd251c4ad4fc24b52c6589f7375e3c39a32cb2d787a1d4f88ff85673ab210edf6d5eafa00e82ededd846154f47a8a7ede8686d6d7971656c7','EMPLOYEE','CORE_TEAM',35000,10,0.3,'2026-08-29 10:35:26'),(4,'Rahul','rahul.barot2306@gmail.com','scrypt:32768:8:1$Ew5oNb9MLEhRNgX0$da6b7a51ba2d31abbe326caba09b7b02ffb5ac24359e089150639dff0cf4dc2dca9871afd4dfd717454f2399ec618ad3beac116733db1e44868d4154b6c1c54e','EMPLOYEE','CORE_TEAM',25000,10,0.3,'2026-08-29 10:45:37'),(5,'Gaurav','gaurav.a.d.mistry@gmail.com','scrypt:32768:8:1$KyViVaONuCsa2i1e$9f2f2d461de5e1b9d120dfa7d4bb7726ae643523b018d14aee8cf41882e0cffae5f24528382b5e502ad0ba1dad4fbe7c249fbf143737c77b21795fec44eb8220','EMPLOYEE','CORE_TEAM',20000,10,0.3,'2026-08-29 10:46:24'),(6,'Test-1','test@gmail.com','scrypt:32768:8:1$fsoOQP9BQPVoWIbX$75dbb9efdff20f071bca0e7afd1a4a61487c1aa1d144eadaf5fe348b075a07dbf3a40f195d58ab6cfd9f9bc7f6e4123e90e61936e42391c2e3aca1b7fea681ba','EMPLOYEE','CORE_TEAM',20000,10,0.3,'2026-08-29 11:34:59'),(7,'Abhijit','parmarabhijit2712@gmail.com','scrypt:32768:8:1$xA8FjcacV6l6wsKu$f7d78fc1232de9bb41e5d29c0f8bc19cc51c8e9f2330b13a84712e6d914e2c94e988d925dde00fc0aef7f2c3465c6d208b88b2fa3ace253120553881d0536a1c','EMPLOYEE','NORMAL_TEAM',18000,7,0.2,'2026-08-29 11:48:22'),(8,'Vinay','vinayprajapati9714@gmail.com','scrypt:32768:8:1$x3X15GeOZL77ZlB0$4f92dbd9bfb95416c5287f067bbe294a093c7d712b495e43cb532828175ed4afae757041a2ae8e4fd0e27df2b884317db65e109fa8925a5dfd3cfc6541f814c2','EMPLOYEE','RENT_TEAM',15000,5,0.2,'2026-08-30 11:15:56'),(9,'Test-2','cityscope.in@gmail.com','scrypt:32768:8:1$hAbsfFB8cmECseOq$ad07e8411e0984962ea8fb1c7dfe6bd2e2c012b2cd87b394badb097e6b3ee83ab0ca7dd5c8b8e122dd085ccfab75f6e23d4079940385d1b6309831853d926ac5','EMPLOYEE','CORE_TEAM',25000,10,0.3,'2026-08-31 10:26:33'),(10,'Bhavita','kavyaa.koshta@gmail.com','scrypt:32768:8:1$vLiq2Dw9s2i6NudK$6f3c01e15b42d0b6ba56960256fd352bb91bf9278132301d6e23916662b410de4ed09850e235d0e2c9da8d527a5e2c3c82f6314d22b35845d708747762bcb6b3','EMPLOYEE','NORMAL_TEAM',18000,7,0.2,'2026-09-05 10:31:05'),(11,'Kartik','kartiksinh1245@gmail.com','scrypt:32768:8:1$CpW9Vq9huKKjaOQN$667b7d955962bcbebc8038edd9815542d0cbf85da4e0ffa28b5cdf0c5ca47e330edf8a1ecd9db121b512bf0ccfecb9620bbbb4cf88fd0383a620eed6748221fc','EMPLOYEE','RENT_TEAM',14000,5,0.2,'2026-09-07 14:54:36'),(12,'Sujal','sujalmistry2401@gmail.com','scrypt:32768:8:1$vFcxqgPSaJ8yW100$fcd2e8b33845b549ace4ba0942f3c83d3bfb37044a792d11e4cd0e15213cafecc7076acb919f56e971deb11d40ad15e5bfb9a80a7f49b9ae9f8cc7230e613788','EMPLOYEE','RENT_TEAM',15000,5,0.2,'2026-09-07 14:59:15'),(13,'Lalit','lalit.makwana2710@gmail.com','scrypt:32768:8:1$pDWRvnekj6aRBWOM$fa38d074b201d67ec3c1e5ed8b24a67f135b2a93e6baffdaaf54c230315f86d94b044e4d4bef6c630b6168bba3a4635363b460fdaa1edbc1e5af80d966c2241b','EMPLOYEE','NORMAL_TEAM',20000,7,0.2,'2026-09-07 15:50:35');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-10-01 16:21:15
