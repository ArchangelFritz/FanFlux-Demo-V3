import pyodbc
import sys

# Connection string - REPLACE 'YourPassword' with your actual password
conn_str = (
    "Driver={ODBC Driver 18 for SQL Server};"
    "Server=fanflux-sql-server.database.windows.net;"
    "Database=Audience-Acuity-Summary;"
    "Uid=fanfluxadmin;"
    "Pwd=Cougar@2013;"  # <- PUT YOUR ACTUAL PASSWORD HERE
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
)

try:
    print("Connecting to database...")
    conn = pyodbc.connect(conn_str, timeout=7200)
    cursor = conn.cursor()
    
    print("\n1/3: Adding TEAM_NAME_IDX column (this takes ~10 minutes)...")
    cursor.execute("""
        ALTER TABLE V3.TEAM_CITY_INTEREST_METRICS_FINAL_FOR_AZURE_SQL 
        ADD TEAM_NAME_IDX AS CAST(TEAM_NAME AS NVARCHAR(100)) PERSISTED;
    """)
    conn.commit()
    print("✓ TEAM_NAME_IDX added!")
    
    print("\n2/3: Adding INTEREST_IDX column (this takes ~10 minutes)...")
    cursor.execute("""
        ALTER TABLE V3.TEAM_CITY_INTEREST_METRICS_FINAL_FOR_AZURE_SQL 
        ADD INTEREST_IDX AS CAST(INTEREST AS NVARCHAR(255)) PERSISTED;
    """)
    conn.commit()
    print("✓ INTEREST_IDX added!")
    
    print("\n3/3: Creating index (this takes ~15 minutes)...")
    cursor.execute("""
        CREATE NONCLUSTERED INDEX IX_Team_Interest_City
        ON V3.TEAM_CITY_INTEREST_METRICS_FINAL_FOR_AZURE_SQL 
        (TEAM_NAME_IDX, INTEREST_IDX, CITY_LAT, CITY_LON)
        INCLUDE (INTEREST_FAN_COUNT, TOTAL_FAN_COUNT, AVID_FAN_COUNT, AVG_INCOME, CITY_NAME, STATE_NAME);
    """)
    conn.commit()
    print("✓ Index created!")
    
    print("\n✅ ALL DONE! Your queries should be fast now.")
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    sys.exit(1)