import sqlite3
from pathlib import Path
from datetime import datetime


# ============================================================
# DATABASE PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"

DATABASE = DATA_DIR / "gateway.db"


# ============================================================
# CONNECTION
# ============================================================

def get_connection():

    DATA_DIR.mkdir(exist_ok=True)

    connection = sqlite3.connect(
        DATABASE,
        check_same_thread=False
    )

    connection.row_factory = sqlite3.Row

    return connection

   
    
# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database():

    connection = get_connection()

    cursor = connection.cursor()

    # ========================================================
    # PRIVATE CHAT CONVERSATIONS
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_conversations (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            conversation_id TEXT UNIQUE NOT NULL,

            node_a TEXT NOT NULL,

            node_b TEXT NOT NULL,

            created_at TEXT NOT NULL,

            updated_at TEXT NOT NULL,

            UNIQUE(node_a, node_b)

        )
    """)


    # ========================================================
    # PRIVATE CHAT MESSAGES
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            message_id TEXT UNIQUE NOT NULL,

            conversation_id TEXT NOT NULL,

            sender_node_id TEXT NOT NULL,

            receiver_node_id TEXT NOT NULL,

            message_text TEXT NOT NULL,

            status TEXT DEFAULT 'SENT',

            created_at TEXT NOT NULL,

            sent_at TEXT,

            delivered_at TEXT,

            seen_at TEXT,

            packet_id TEXT,

            FOREIGN KEY (
                conversation_id
            )
            REFERENCES chat_conversations(
                conversation_id
            )

        )
    """)


    # ========================================================
    # CHAT INDEXES
    # ========================================================

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_chat_messages_conversation

        ON chat_messages (
            conversation_id,
            created_at
        )
    """)


    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_chat_messages_receiver_status

        ON chat_messages (
            receiver_node_id,
            status
        )
    """)


    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_chat_messages_message_id

        ON chat_messages (
            message_id
        )
    """)

    # ========================================================
    # NODES
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nodes (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            node_id TEXT UNIQUE NOT NULL,

            name TEXT NOT NULL,

            mcu_family TEXT,

            mcu_model TEXT,

            hardware_revision TEXT,

            firmware_version TEXT,

            communication_type TEXT,

            communication_config TEXT,

            node_address TEXT,

            enabled INTEGER DEFAULT 1,

            status TEXT DEFAULT 'offline',

            last_seen TEXT,

            created_at TEXT,

            updated_at TEXT

        )
    """)


    # ========================================================
    # LEGACY SENSOR TABLE
    # Keep this because your project already uses it.
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sensors (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            node_id TEXT NOT NULL,

            sensor_id TEXT NOT NULL,

            sensor_type TEXT NOT NULL,

            sensor_name TEXT,

            interface_type TEXT,

            gpio INTEGER,

            unit TEXT,

            interval_ms INTEGER DEFAULT 2000,

            enabled INTEGER DEFAULT 1,

            created_at TEXT,

            updated_at TEXT,

            UNIQUE(node_id, sensor_id)

        )
    """)


    # ========================================================
    # SENSOR PARAMETERS
    #
    # A physical sensor can have multiple parameters.
    #
    # DHT11
    #   -> Temperature
    #   -> Humidity
    #
    # INA219
    #   -> Voltage
    #   -> Current
    #   -> Power
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sensor_parameters (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            node_id TEXT NOT NULL,

            parameter_id TEXT NOT NULL,

            sensor_id TEXT,

            parameter_name TEXT NOT NULL,

            parameter_type TEXT NOT NULL,

            data_type TEXT NOT NULL,

            unit TEXT DEFAULT "",

            description TEXT DEFAULT "",

            enabled INTEGER DEFAULT 1,

            display_enabled INTEGER DEFAULT 1,

            graph_enabled INTEGER DEFAULT 0,

            decimal_places INTEGER DEFAULT 2,

            min_value REAL,

            max_value REAL,

            alarm_enabled INTEGER DEFAULT 0,

            low_alarm REAL,

            high_alarm REAL,

            created_at TEXT,

            updated_at TEXT,

            UNIQUE(node_id, parameter_id)

        )
    """)


    # ========================================================
    # GRAPH CONFIGURATION
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sensor_graphs (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            node_id TEXT NOT NULL,

            parameter_id TEXT NOT NULL,

            graph_type TEXT DEFAULT 'line',

            time_range TEXT DEFAULT '1h',

            auto_scale INTEGER DEFAULT 1,

            y_min REAL,

            y_max REAL,

            show_grid INTEGER DEFAULT 1,

            show_legend INTEGER DEFAULT 1,

            show_points INTEGER DEFAULT 1,

            smooth_line INTEGER DEFAULT 0,

            animation_enabled INTEGER DEFAULT 1,

            update_interval_ms INTEGER DEFAULT 2000,

            max_points INTEGER DEFAULT 300,

            created_at TEXT,

            updated_at TEXT,

            UNIQUE(node_id, parameter_id)

        )
    """)


    # ========================================================
    # GENERIC TELEMETRY VALUES
    #
    # One row = one parameter value.
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS telemetry_values (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            node_id TEXT NOT NULL,

            parameter_id TEXT NOT NULL,

            timestamp TEXT NOT NULL,

            value REAL,

            text_value TEXT,

            data_type TEXT,

            quality TEXT DEFAULT 'GOOD',

            status TEXT DEFAULT 'NORMAL',

            source TEXT DEFAULT 'telemetry'

        )
    """)


    # ========================================================
    # INDEXES
    # ========================================================

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_telemetry_node_parameter_time

        ON telemetry_values (
            node_id,
            parameter_id,
            timestamp
        )
    """)


    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_parameters_node

        ON sensor_parameters (
            node_id
        )
    """)


    # ========================================================
    # COMMAND HISTORY
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS commands (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            command_id TEXT UNIQUE,

            node_id TEXT,

            command TEXT,

            parameters TEXT,

            status TEXT,

            response TEXT,

            created_at TEXT,

            completed_at TEXT

        )
    """)


    # ========================================================
    # EXISTING TELEMETRY TABLE
    # Keep for compatibility with current simulator.
    # ========================================================
    # ========================================================
    # SYSTEM LOGS
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            timestamp TEXT NOT NULL,

            severity TEXT DEFAULT 'info',

            source TEXT DEFAULT 'SYSTEM',

            message TEXT NOT NULL,

            node_id TEXT

        )
    """)


    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_logs_timestamp

        ON logs (
            timestamp
        )
    """)


    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_logs_severity

        ON logs (
            severity
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS telemetry (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            node_id TEXT,

            timestamp TEXT,

            temperature REAL,

            humidity REAL,

            battery_voltage REAL,

            battery_percent REAL,

            current_ma REAL,

            power_mw REAL,

            rssi REAL,

            snr REAL,

            packets_tx INTEGER,

            packets_rx INTEGER

        )
    """)


    # ========================================================
    # FIRMWARE RELEASES
    # Metadata only. Firmware binaries are stored on disk under
    # data/firmware/releases/<release_id>/firmware.bin.
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS firmware_releases (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            release_id TEXT UNIQUE NOT NULL,

            version TEXT NOT NULL,

            build INTEGER NOT NULL,

            hardware_family TEXT NOT NULL,

            hardware_model TEXT NOT NULL,

            hardware_revision TEXT NOT NULL,

            filename TEXT NOT NULL,

            file_size INTEGER NOT NULL,

            sha256 TEXT NOT NULL,

            signature TEXT,

            channel TEXT DEFAULT 'stable',

            release_notes TEXT DEFAULT '',

            minimum_bootloader TEXT,

            security_version INTEGER DEFAULT 0,

            mandatory INTEGER DEFAULT 0,

            status TEXT DEFAULT 'DRAFT',

            created_at TEXT NOT NULL,

            approved_at TEXT,

            retired_at TEXT,

            revoked_at TEXT

        )
    """)


    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_firmware_releases_lookup

        ON firmware_releases (
            hardware_family,
            hardware_model,
            hardware_revision,
            channel,
            status,
            build
        )
    """)


    # ========================================================
    # DEVICE FIRMWARE STATE
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS device_firmware (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            node_id TEXT UNIQUE NOT NULL,

            hardware_family TEXT,

            hardware_model TEXT,

            hardware_revision TEXT,

            current_version TEXT,

            current_build INTEGER DEFAULT 0,

            target_release_id TEXT,

            target_version TEXT,

            target_build INTEGER,

            ota_state TEXT DEFAULT 'IDLE',

            channel TEXT DEFAULT 'stable',

            last_check_at TEXT,

            last_update_at TEXT,

            rollback_release_id TEXT,

            failure_count INTEGER DEFAULT 0,

            last_error TEXT,

            updated_at TEXT NOT NULL

        )
    """)


    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_device_firmware_state

        ON device_firmware (
            ota_state,
            channel,
            updated_at
        )
    """)


    # ========================================================
    # FIRMWARE UPDATE JOBS
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS firmware_update_jobs (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            job_id TEXT UNIQUE NOT NULL,

            node_id TEXT NOT NULL,

            release_id TEXT NOT NULL,

            from_version TEXT,

            from_build INTEGER,

            target_version TEXT NOT NULL,

            target_build INTEGER NOT NULL,

            state TEXT DEFAULT 'APPROVED',

            progress INTEGER DEFAULT 0,

            authorized INTEGER DEFAULT 0,

            started_at TEXT,

            completed_at TEXT,

            result TEXT,

            error TEXT,

            created_at TEXT NOT NULL,

            updated_at TEXT NOT NULL

        )
    """)


    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_firmware_update_jobs_node

        ON firmware_update_jobs (
            node_id,
            created_at
        )
    """)


    # ========================================================
    # FIRMWARE UPDATE EVENTS
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS firmware_update_events (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            event_id TEXT UNIQUE NOT NULL,

            job_id TEXT,

            node_id TEXT,

            release_id TEXT,

            event_type TEXT NOT NULL,

            state TEXT,

            progress INTEGER,

            message TEXT,

            error TEXT,

            created_at TEXT NOT NULL

        )
    """)


    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_firmware_update_events_job

        ON firmware_update_events (
            job_id,
            created_at
        )
    """)


    connection.commit()

    connection.close()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    initialize_database()

    print("Database initialized:")

    print(DATABASE)
