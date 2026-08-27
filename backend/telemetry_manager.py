from datetime import datetime

from database import get_connection

from sensor_manager import get_parameter


# ============================================================
# SAVE ONE PARAMETER VALUE
# ============================================================

def save_value(
    node_id,
    parameter_id,
    value,
    quality="GOOD",
    status="NORMAL",
    timestamp=None
):

    parameter = get_parameter(
            node_id,
            parameter_id
        )


    if parameter is None:

        return False


    if timestamp is None:

        timestamp = datetime.now().isoformat()


    numeric_value = None

    text_value = None


    data_type = parameter["data_type"]


    if data_type in [

        "FLOAT",
        "DOUBLE",
        "INT",
        "UINT",
        "UINT32"

    ]:

        try:

            numeric_value = float(value)

        except (
            TypeError,
            ValueError
        ):

            text_value =str(value)

    else:

        text_value = str(value)


    connection = get_connection()


    cursor = connection.cursor()


    cursor.execute(
        """
        INSERT INTO telemetry_values (

            node_id,
            parameter_id,
            timestamp,
            value,
            text_value,
            data_type,
            quality,
            status,
            source

        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,

        (
            node_id,
            parameter_id,
            timestamp,
            numeric_value,
            text_value,
            data_type,
            quality,
            status,
            "telemetry"
        )
    )


    connection.commit()

    connection.close()


    return True


# ============================================================
# SAVE MULTIPLE VALUES
# ============================================================

def save_parameters(
    node_id,
    parameters,
    timestamp=None
):

    if timestamp is None:

        timestamp = datetime.now().isoformat()


    saved = 0


    for parameter_id, value in parameters.items():

        if save_value(
            node_id,
            parameter_id,
            value,
            timestamp=timestamp
        ):

            saved += 1


    return saved


# ============================================================
# GET HISTORY
# ============================================================

def get_history(
    node_id,
    parameter_id,
    limit=300
):

    connection = get_connection()


    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT

            id,
            node_id,
            parameter_id,
            timestamp,
            value,
            text_value,
            data_type,
            quality,
            status

        FROM telemetry_values

        WHERE node_id = ?

        AND parameter_id = ?

        ORDER BY timestamp DESC

        LIMIT ?
        """,

        (
            node_id,
            parameter_id,
            int(limit)
        )
    )


    rows = cursor.fetchall()


    connection.close()


    result = [dict(row) for row in rows]


    result.reverse()


    return result


# ============================================================
# GET MULTIPLE PARAMETERS
# ============================================================

def get_compare_data(
    node_id,
    parameter_ids,
    limit=300
):

    result = {}


    for parameter_id in parameter_ids:

        result[parameter_id] = get_history(
                node_id,
                parameter_id,
                limit
            )


    return result


# ============================================================
# LATEST VALUE
# ============================================================

def get_latest_value(
    node_id,
    parameter_id
):

    connection = get_connection()


    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT *

        FROM telemetry_values

        WHERE node_id = ?

        AND parameter_id = ?

        ORDER BY timestamp DESC

        LIMIT 1
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
# LATEST VALUES FOR ALL PARAMETERS
# ============================================================

def get_latest_values(node_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            p.parameter_id,
            p.parameter_name,
            p.parameter_type,
            p.data_type,
            p.unit,
            p.decimal_places,
            p.enabled,
            p.display_enabled,
            p.graph_enabled,
            p.alarm_enabled,
            p.low_alarm,
            p.high_alarm,
            t.timestamp,
            t.value,
            t.text_value,
            t.quality,
            t.status
        FROM sensor_parameters p
        LEFT JOIN telemetry_values t
            ON t.node_id = p.node_id
            AND t.parameter_id = p.parameter_id
            AND t.id = (
                SELECT MAX(t2.id)
                FROM telemetry_values t2
                WHERE t2.node_id = p.node_id
                AND t2.parameter_id = p.parameter_id
            )
        WHERE p.node_id = ?
        AND p.enabled = 1
        ORDER BY p.id
        """,
        (node_id,)
    )

    rows = cursor.fetchall()
    connection.close()

    result = []

    for row in rows:

        item = dict(row)

        item["enabled"] = bool(item["enabled"])
        item["display_enabled"] = bool(item["display_enabled"])
        item["graph_enabled"] = bool(item["graph_enabled"])
        item["alarm_enabled"] = bool(item["alarm_enabled"])

        item["alarm_status"] = calculate_alarm_status(
            item.get("value"),
            item.get("alarm_enabled"),
            item.get("low_alarm"),
            item.get("high_alarm"),
            item.get("quality"),
            item.get("timestamp")
        )

        result.append(item)

    return result


# ============================================================
# ALARM STATUS
# ============================================================

def calculate_alarm_status(
    value,
    alarm_enabled,
    low_alarm,
    high_alarm,
    quality,
    timestamp
):

    if timestamp is None:
        return "NO_DATA"

    if quality not in (None, "GOOD"):
        return "SENSOR_ERROR"

    if value is None:
        return "NO_DATA"

    if not alarm_enabled:
        return "NORMAL"

    if low_alarm is not None and value < low_alarm:
        return "LOW"

    if high_alarm is not None and value > high_alarm:
        return "HIGH"

    return "NORMAL"


# ============================================================
# PARAMETER STATISTICS
# ============================================================

def get_statistics(
    node_id,
    parameter_id,
    limit=300
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            value,
            timestamp
        FROM telemetry_values
        WHERE node_id = ?
        AND parameter_id = ?
        AND value IS NOT NULL
        ORDER BY timestamp DESC
        LIMIT ?
        """,
        (
            node_id,
            parameter_id,
            int(limit)
        )
    )

    rows = cursor.fetchall()
    connection.close()

    if not rows:
        return {
            "current": None,
            "minimum": None,
            "maximum": None,
            "average": None,
            "sample_count": 0,
            "last_update": None
        }

    values = [
        float(row["value"])
        for row in rows
        if row["value"] is not None
    ]

    if not values:
        return {
            "current": None,
            "minimum": None,
            "maximum": None,
            "average": None,
            "sample_count": 0,
            "last_update": None
        }

    return {
        "current": values[0],
        "minimum": min(values),
        "maximum": max(values),
        "average": sum(values) / len(values),
        "sample_count": len(values),
        "last_update": rows[0]["timestamp"]
    }


# ============================================================
# STATISTICS FOR ALL PARAMETERS
# ============================================================

def get_all_statistics(
    node_id,
    limit=300
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT parameter_id
        FROM sensor_parameters
        WHERE node_id = ?
        AND enabled = 1
        ORDER BY id
        """,
        (node_id,)
    )

    rows = cursor.fetchall()
    connection.close()

    result = {}

    for row in rows:

        parameter_id = row["parameter_id"]

        result[parameter_id] = get_statistics(
            node_id,
            parameter_id,
            limit
        )

    return result