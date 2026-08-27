import sqlite3

from datetime import datetime

from database import get_connection


# ============================================================
# DEFAULT PARAMETER TYPES
# ============================================================

DEFAULT_PARAMETERS = [

    {
        "parameter_type": "Temperature",
        "data_type": "FLOAT",
        "unit": "°C"
    },

    {
        "parameter_type": "Humidity",
        "data_type": "FLOAT",
        "unit": "%RH"
    },

    {
        "parameter_type": "Air Quality",
        "data_type": "INT",
        "unit": "AQI"
    },

    {
        "parameter_type": "Battery Voltage",
        "data_type": "FLOAT",
        "unit": "V"
    },

    {
        "parameter_type": "Battery Current",
        "data_type": "FLOAT",
        "unit": "mA"
    },

    {
        "parameter_type": "Battery Power",
        "data_type": "FLOAT",
        "unit": "W"
    },

    {
        "parameter_type": "Battery Level",
        "data_type": "FLOAT",
        "unit": "%"
    },

    {
        "parameter_type": "Pressure",
        "data_type": "FLOAT",
        "unit": "hPa"
    },

    {
        "parameter_type": "Current",
        "data_type": "FLOAT",
        "unit": "mA"
    },

    {
        "parameter_type": "Voltage",
        "data_type": "FLOAT",
        "unit": "V"
    },

    {
        "parameter_type": "Power",
        "data_type": "FLOAT",
        "unit": "W"
    },

    {
        "parameter_type": "RSSI",
        "data_type": "INT",
        "unit": "dBm"
    },

    {
        "parameter_type": "SNR",
        "data_type": "FLOAT",
        "unit": "dB"
    },

    {
        "parameter_type": "Network Status",
        "data_type": "ENUM",
        "unit": ""
    },

    {
        "parameter_type": "Wi-Fi Signal",
        "data_type": "INT",
        "unit": "dBm"
    },

    {
        "parameter_type": "CPU Temperature",
        "data_type": "FLOAT",
        "unit": "°C"
    },

    {
        "parameter_type": "Uptime",
        "data_type": "UINT32",
        "unit": "s"
    },

    {
        "parameter_type": "Free Memory",
        "data_type": "UINT32",
        "unit": "bytes"
    },

    {
        "parameter_type": "Sensor Status",
        "data_type": "ENUM",
        "unit": ""
    },

    {
        "parameter_type": "Device Status",
        "data_type": "ENUM",
        "unit": ""
    }

]


# ============================================================
# CHECK NODE
# ============================================================

def node_exists(node_id):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT node_id
        FROM nodes
        WHERE node_id = ?
        """,
        (node_id,)
    )

    result = cursor.fetchone()

    connection.close()

    return result is not None


# ============================================================
# GET PARAMETERS
# ============================================================

def get_parameters(node_id):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM sensor_parameters
        WHERE node_id = ?
        ORDER BY id
        """,
        (node_id,)
    )

    rows = cursor.fetchall()

    result = []

    for row in rows:

        parameter = dict(row)

        parameter["enabled"] = bool(
            parameter["enabled"]
        )

        parameter["display_enabled"] = bool(
            parameter["display_enabled"]
        )

        parameter["graph_enabled"] = bool(
            parameter["graph_enabled"]
        )

        parameter["alarm_enabled"] = bool(
            parameter["alarm_enabled"]
        )

        result.append(parameter)

    connection.close()

    return result


# ============================================================
# GET ONE PARAMETER
# ============================================================

def get_parameter(
    node_id,
    parameter_id
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM sensor_parameters
        WHERE node_id = ?
        AND parameter_id = ?
        """,
        (
            node_id,
            parameter_id
        )
    )

    row = cursor.fetchone()

    connection.close()

    if row is None:

        return None

    return dict(row)


# ============================================================
# ADD PARAMETER
# ============================================================

def add_parameter(
    node_id,
    parameter_id,
    parameter_name,
    parameter_type,
    data_type,
    unit="",
    sensor_id=None,
    description="",
    enabled=True,
    display_enabled=True,
    graph_enabled=False,
    decimal_places=2,
    min_value=None,
    max_value=None,
    alarm_enabled=False,
    low_alarm=None,
    high_alarm=None
):

    if not node_exists(node_id):

        raise ValueError(
            "Node not found"
        )


    now = datetime.now().isoformat()


    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        INSERT INTO sensor_parameters (

            node_id,
            parameter_id,
            sensor_id,
            parameter_name,
            parameter_type,
            data_type,
            unit,
            description,
            enabled,
            display_enabled,
            graph_enabled,
            decimal_places,
            min_value,
            max_value,
            alarm_enabled,
            low_alarm,
            high_alarm,
            created_at,
            updated_at

        )

        VALUES (

            ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?

        )
        """,

        (
            node_id,
            parameter_id,
            sensor_id,
            parameter_name,
            parameter_type,
            data_type,
            unit,
            description,
            int(enabled),
            int(display_enabled),
            int(graph_enabled),
            decimal_places,
            min_value,
            max_value,
            int(alarm_enabled),
            low_alarm,
            high_alarm,
            now,
            now
        )
    )


    connection.commit()

    connection.close()


    # Create default graph configuration

    create_default_graph(
        node_id,
        parameter_id,
        graph_enabled
    )


# ============================================================
# UPDATE PARAMETER
# ============================================================

def update_parameter(
    node_id,
    parameter_id,
    data
):

    if not get_parameter(
        node_id,
        parameter_id
    ):

        return False


    allowed = [

        "sensor_id",
        "parameter_name",
        "parameter_type",
        "data_type",
        "unit",
        "description",
        "enabled",
        "display_enabled",
        "graph_enabled",
        "decimal_places",
        "min_value",
        "max_value",
        "alarm_enabled",
        "low_alarm",
        "high_alarm"

    ]


    updates = []

    values = []


    for field in allowed:

        if field in data:

            value = data[field]


            if field in [

                "enabled",
                "display_enabled",
                "graph_enabled",
                "alarm_enabled"

            ]:

                value = int(bool(value))


            updates.append(
                f"{field} = ?"
            )

            values.append(value)


    if not updates:

        return True


    updates.append(
        "updated_at = ?"
    )

    values.append(
        datetime.now().isoformat()
    )


    values.extend([
        node_id,
        parameter_id
    ])


    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        f"""
        UPDATE sensor_parameters

        SET {", ".join(updates)}

        WHERE node_id = ?

        AND parameter_id = ?
        """,
        values
    )


    connection.commit()

    connection.close()


    return True


# ============================================================
# DELETE PARAMETER
# ============================================================

def delete_parameter(
    node_id,
    parameter_id
):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        DELETE FROM sensor_graphs
        WHERE node_id = ?
        AND parameter_id = ?
        """,
        (
            node_id,
            parameter_id
        )
    )


    cursor.execute(
        """
        DELETE FROM sensor_parameters
        WHERE node_id = ?
        AND parameter_id = ?
        """,
        (
            node_id,
            parameter_id
        )
    )


    connection.commit()

    deleted =  cursor.rowcount > 0

    connection.close()

    return deleted


# ============================================================
# ENABLE / DISABLE
# ============================================================

def set_parameter_enabled(
    node_id,
    parameter_id,
    enabled
):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        UPDATE sensor_parameters

        SET
            enabled = ?,
            updated_at = ?

        WHERE node_id = ?

        AND parameter_id = ?
        """,
        (
            int(bool(enabled)),
            datetime.now().isoformat(),
            node_id,
            parameter_id
        )
    )


    connection.commit()

    success =  cursor.rowcount > 0

    connection.close()

    return success


# ============================================================
# GRAPH DEFAULT
# ============================================================

def create_default_graph(
    node_id,
    parameter_id,
    graph_enabled=False
):

    now = datetime.now().isoformat()


    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        INSERT OR IGNORE INTO sensor_graphs (

            node_id,
            parameter_id,
            graph_type,
            time_range,
            auto_scale,
            show_grid,
            show_legend,
            show_points,
            smooth_line,
            animation_enabled,
            update_interval_ms,
            max_points,
            created_at,
            updated_at

        )

        VALUES (

            ?, ?, 'line', '1h', ?, 1, 1,
            1, 0, 1, 2000, 300, ?, ?

        )
        """,

        (
            node_id,
            parameter_id,
            int(bool(graph_enabled)),
            now,
            now
        )
    )


    connection.commit()

    connection.close()


# ============================================================
# GET GRAPH CONFIG
# ============================================================

def get_graph_config(
    node_id,
    parameter_id
):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT *
        FROM sensor_graphs

        WHERE node_id = ?

        AND parameter_id = ?
        """,
        (
            node_id,
            parameter_id
        )
    )


    row = cursor.fetchone()

    connection.close()


    if row is None:

        create_default_graph(
            node_id,
            parameter_id
        )

        return get_graph_config(
            node_id,
            parameter_id
        )


    result = dict(row)


    for field in [

        "auto_scale",
        "show_grid",
        "show_legend",
        "show_points",
        "smooth_line",
        "animation_enabled"

    ]:

        result[field] = bool(
            result[field]
        )


    return result


# ============================================================
# UPDATE GRAPH CONFIG
# ============================================================

def update_graph_config(
    node_id,
    parameter_id,
    data
):

    get_graph_config(
        node_id,
        parameter_id
    )


    allowed = [

        "graph_type",
        "time_range",
        "auto_scale",
        "y_min",
        "y_max",
        "show_grid",
        "show_legend",
        "show_points",
        "smooth_line",
        "animation_enabled",
        "update_interval_ms",
        "max_points"

    ]


    updates = []

    values = []


    for field in allowed:

        if field in data:

            value = data[field]


            if field in [

                "auto_scale",
                "show_grid",
                "show_legend",
                "show_points",
                "smooth_line",
                "animation_enabled"

            ]:

                value = int(bool(value))


            updates.append(
                f"{field} = ?"
            )

            values.append(value)


    if not updates:

        return True


    updates.append(
        "updated_at = ?"
    )

    values.append(
        datetime.now().isoformat()
    )


    values.extend([
        node_id,
        parameter_id
    ])


    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        f"""
        UPDATE sensor_graphs

        SET {", ".join(updates)}

        WHERE node_id = ?

        AND parameter_id = ?
        """,
        values
    )


    connection.commit()

    connection.close()


    return True


# ============================================================
# DEFAULT PARAMETER CATALOG
# ============================================================

def get_default_parameters():

    return DEFAULT_PARAMETERS