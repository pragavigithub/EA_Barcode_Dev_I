# MySQL Setup Guide for Replit WMS

## Current Issue
Your WMS is configured to use "localhost" as MySQL host, which doesn't work in Replit. The app is falling back to PostgreSQL, so your GRN and Inventory Transfer data is being stored there instead of MySQL.

## Solution
You need to update your MySQL configuration to use an external MySQL server.

### Step 1: Update MySQL Host
In your Replit Secrets, update `MYSQL_HOST` from "localhost" to your external MySQL server address.

**Examples of valid MySQL hosts:**
- `your-domain.com` (if you have a domain pointing to your MySQL server)
- `db.your-hosting-provider.com` (common for shared hosting)
- `mysql.your-website.com` (subdomain setup)
- `192.168.1.100` (direct IP address if accessible from internet)

### Step 2: Ensure MySQL Server is Internet-Accessible
Your MySQL server must:
- Accept connections from external IPs (not just localhost)
- Have proper firewall rules allowing connections on port 3306
- Be configured to accept remote connections

### Step 3: Test Connection
After updating the host, run:
```bash
python mysql_complete_migration.py
```

This will test your MySQL connection and create the required tables.

### Step 4: Restart Application
After successful MySQL connection, restart your application to start using MySQL for all data storage.

## Current Configuration
- Host: localhost (❌ Won't work in Replit)
- User: root
- Database: wms_db_dev
- Password: ******** (configured)

## What Happens After Fix
- ✅ All GRN data will be stored in MySQL
- ✅ All Inventory Transfer data will be stored in MySQL  
- ✅ All user data will be stored in MySQL
- ✅ SAP B1 integration will work with MySQL backend

## Need Help?
If you don't have an external MySQL server:
1. Consider using a hosting provider like:
   - DigitalOcean Managed Databases
   - AWS RDS
   - Google Cloud SQL
   - Shared hosting with MySQL (cPanel, etc.)

2. Or set up a local MySQL server that accepts external connections

## Migration Status
- [x] App configured to prioritize MySQL over PostgreSQL
- [x] Fallback system working (currently using PostgreSQL)
- [ ] External MySQL host configured
- [ ] MySQL connection successful
- [ ] All data flowing to MySQL