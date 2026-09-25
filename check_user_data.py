"""
Script to check which users have data in the system.
Shows data availability across all major tables.
"""

import pymysql
from tabulate import tabulate
from datetime import datetime
import json

# Database configuration
DB_CONFIG = {
    "host": "mysql-database.cc98ouaycdke.us-east-1.rds.amazonaws.com",
    "port": 3306,
    "user": "admin",
    "password": "Shahrul@123",
    "database": "pulse_mysql",
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
}


def get_connection():
    """Create database connection."""
    return pymysql.connect(**DB_CONFIG)


def check_user_data():
    """Check data availability for all users."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            print("\n" + "="*100)
            print("USER DATA AVAILABILITY REPORT")
            print("="*100 + "\n")
            
            # Get all users
            cursor.execute("SELECT user_id, username, email, created_at FROM users ORDER BY user_id")
            users = cursor.fetchall()
            
            if not users:
                print("❌ No users found in database")
                return
            
            user_data_summary = []
            
            for user in users:
                user_id = user.get("user_id")
                username = user.get("username", "N/A")
                
                # Count skin scans
                cursor.execute("SELECT COUNT(*) as count FROM skin_scans WHERE user_id = %s", (user_id,))
                skin_scans_count = cursor.fetchone().get("count", 0)
                
                # Count terra activity data
                cursor.execute("SELECT COUNT(*) as count FROM terra_activity_data WHERE user_id = %s", (user_id,))
                terra_count = cursor.fetchone().get("count", 0)
                
                # Count menstrual cycles
                cursor.execute("SELECT COUNT(*) as count FROM menstrual_cycles WHERE user_id = %s", (user_id,))
                cycles_count = cursor.fetchone().get("count", 0)
                
                # Count health metrics
                cursor.execute("SELECT COUNT(*) as count FROM health_metrics WHERE user_id = %s", (user_id,))
                health_count = cursor.fetchone().get("count", 0)
                
                # Get latest skin scan date
                cursor.execute(
                    "SELECT MAX(created_at) as latest FROM skin_scans WHERE user_id = %s",
                    (user_id,)
                )
                latest_scan = cursor.fetchone().get("latest")
                
                # Get latest terra data date
                cursor.execute(
                    "SELECT MAX(created_at) as latest FROM terra_activity_data WHERE user_id = %s",
                    (user_id,)
                )
                latest_terra = cursor.fetchone().get("latest")
                
                # Check if user has active data
                has_data = any([skin_scans_count, terra_count, cycles_count, health_count])
                status = "✅ HAS DATA" if has_data else "❌ NO DATA"
                
                user_data_summary.append({
                    "User ID": user_id,
                    "Username": username,
                    "Skin Scans": skin_scans_count,
                    "Terra Data": terra_count,
                    "Cycles": cycles_count,
                    "Health Metrics": health_count,
                    "Latest Scan": str(latest_scan)[:10] if latest_scan else "N/A",
                    "Latest Terra": str(latest_terra)[:10] if latest_terra else "N/A",
                    "Status": status,
                })
            
            # Print summary table
            print(tabulate(user_data_summary, headers="keys", tablefmt="grid"))
            
            # Print detailed data for users with data
            print("\n" + "="*100)
            print("DETAILED DATA BREAKDOWN")
            print("="*100 + "\n")
            
            for user in users:
                user_id = user.get("user_id")
                username = user.get("username", "N/A")
                
                cursor.execute("SELECT COUNT(*) as count FROM terra_activity_data WHERE user_id = %s", (user_id,))
                terra_count = cursor.fetchone().get("count", 0)
                
                if terra_count > 0:
                    print(f"\n📊 USER {user_id} ({username}) - Terra Activity Data:")
                    print("-" * 80)
                    
                    # Get sample terra data
                    cursor.execute(
                        """
                        SELECT 
                            type,
                            DATE(created_at) as date,
                            JSON_EXTRACT(payload, '$.MET_data.avg_level') as avg_met,
                            JSON_EXTRACT(payload, '$.scores.sleep') as sleep_score,
                            JSON_EXTRACT(payload, '$.scores.recovery') as recovery_score
                        FROM terra_activity_data
                        WHERE user_id = %s
                        ORDER BY created_at DESC
                        LIMIT 5
                        """,
                        (user_id,)
                    )
                    terra_data = cursor.fetchall()
                    
                    terra_summary = []
                    for record in terra_data:
                        terra_summary.append({
                            "Type": record.get("type"),
                            "Date": record.get("date"),
                            "Avg MET": record.get("avg_met"),
                            "Sleep Score": record.get("sleep_score"),
                            "Recovery Score": record.get("recovery_score"),
                        })
                    
                    print(tabulate(terra_summary, headers="keys", tablefmt="simple"))
                
                # Check skin scans
                cursor.execute("SELECT COUNT(*) as count FROM skin_scans WHERE user_id = %s", (user_id,))
                skin_count = cursor.fetchone().get("count", 0)
                
                if skin_count > 0:
                    print(f"\n🔍 USER {user_id} ({username}) - Skin Scans:")
                    print("-" * 80)
                    
                    cursor.execute(
                        """
                        SELECT 
                            scan_id,
                            DATE(created_at) as date,
                            overall_score,
                            JSON_EXTRACT(findings, '$.moisture') as moisture,
                            JSON_EXTRACT(findings, '$.texture') as texture,
                            JSON_EXTRACT(findings, '$.elasticity') as elasticity
                        FROM skin_scans
                        WHERE user_id = %s
                        ORDER BY created_at DESC
                        LIMIT 3
                        """,
                        (user_id,)
                    )
                    skin_data = cursor.fetchall()
                    
                    scan_summary = []
                    for record in skin_data:
                        scan_summary.append({
                            "Scan ID": record.get("scan_id"),
                            "Date": record.get("date"),
                            "Overall Score": record.get("overall_score"),
                            "Moisture": record.get("moisture"),
                            "Texture": record.get("texture"),
                        })
                    
                    print(tabulate(scan_summary, headers="keys", tablefmt="simple"))
            
            # Summary statistics
            print("\n" + "="*100)
            print("SYSTEM STATISTICS")
            print("="*100 + "\n")
            
            cursor.execute("SELECT COUNT(*) as count FROM users")
            total_users = cursor.fetchone().get("count", 0)
            
            cursor.execute("SELECT COUNT(*) as count FROM skin_scans")
            total_scans = cursor.fetchone().get("count", 0)
            
            cursor.execute("SELECT COUNT(*) as count FROM terra_activity_data")
            total_terra = cursor.fetchone().get("count", 0)
            
            cursor.execute("SELECT COUNT(*) as count FROM menstrual_cycles")
            total_cycles = cursor.fetchone().get("count", 0)
            
            cursor.execute("SELECT COUNT(DISTINCT user_id) as count FROM terra_activity_data")
            users_with_terra = cursor.fetchone().get("count", 0)
            
            cursor.execute("SELECT COUNT(DISTINCT user_id) as count FROM skin_scans")
            users_with_scans = cursor.fetchone().get("count", 0)
            
            stats = [
                ["Total Users", total_users],
                ["Users with Skin Scans", users_with_scans],
                ["Users with Terra Data", users_with_terra],
                ["Total Skin Scans", total_scans],
                ["Total Terra Records", total_terra],
                ["Total Menstrual Cycles", total_cycles],
            ]
            
            print(tabulate(stats, headers=["Metric", "Count"], tablefmt="grid"))
            
            print("\n✅ Report complete!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_user_data()
