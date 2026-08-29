from flask import Flask, render_template, jsonify, request, send_file
from flask_socketio import SocketIO, emit

from datetime import datetime
from pathlib import Path

import node_manager
import config_manager
import telemetry_manager
import sensor_manager
import database
import firmware_manager
import ota_manager
from communication_manager import communication_manager
from mesh_manager import mesh_manager
from routing_manager import routing_manager
from chat_manager import (
    send_message as chat_send_message,
    get_message as chat_get_message,
    mark_delivered as chat_mark_delivered,
    mark_seen as chat_mark_seen,
    get_conversations as chat_get_conversations,
    get_messages as chat_get_messages,
    get_chat_users
)

app = Flask(
    __name__,
    template_folder="../dashboard/templates",
    static_folder="../dashboard/static"
)

socketio = SocketIO(
    app,
    cors_allowed_origins="*"
)


# ============================================================
# SYSTEM LOG HELPER
# ============================================================

def create_log(
    severity="info",
    source="SYSTEM",
    message="",
    node_id=None
):
    try:

        connection = database.get_connection()

        connection.execute(
            """
            INSERT INTO logs
            (
                timestamp,
                severity,
                source,
                message,
                node_id
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                datetime.now().isoformat(),
                severity,
                source,
                message,
                node_id
            )
        )

        connection.commit()
        connection.close()

    except Exception as error:

        print(
            "Log creation error:",
            error
        )

# ============================================================
# LIVE NODE DATA
# ============================================================

nodes = {}


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/")
def dashboard():

    return render_template("index.html")
@app.route("/system-overview")
def system_overview():
    return render_template("system-overview.html")


@app.route("/nodes")
def nodes_page():
    return render_template("nodes.html")


@app.route("/sensors")
def sensors_page():
    return render_template("sensors.html")


@app.route("/communication")
def communication_page():
    return render_template("communication.html")

@app.route("/chat")
def chat_page():

    return render_template(
        "chat.html"
    )


@app.route("/system")
def system_page():
    return render_template("system.html")


@app.route("/logs")
def logs_page():
    return render_template("logs.html")

# ============================================================
# FIRMWARE / OTA API
# ============================================================

@app.route("/firmware")
def firmware_page():
    return render_template("firmware.html")


# ============================================================
# FIRMWARE API
# ============================================================

def firmware_error(error, status_code=400):
    return jsonify({
        "success": False,
        "error": str(error)
    }), status_code


def get_form_bool(value):
    return str(value or "").lower() in (
        "1",
        "true",
        "yes",
        "on"
    )


def get_firmware_device_rows():
    states = {
        device["node_id"]: device
        for device in ota_manager.list_device_states()
    }

    for node in node_manager.get_all_nodes():
        node_id = node.get("node_id")

        if node_id in states:
            continue

        states[node_id] = {
            "node_id": node_id,
            "hardware_family": node.get("mcu_family"),
            "hardware_model": node.get("mcu_model"),
            "hardware_revision": node.get("hardware_revision"),
            "current_version": node.get("firmware_version"),
            "current_build": 0,
            "target_release_id": None,
            "target_version": None,
            "target_build": None,
            "ota_state": "IDLE",
            "channel": "stable",
            "last_check_at": None,
            "last_update_at": node.get("updated_at"),
            "rollback_release_id": None,
            "failure_count": 0,
            "last_error": None,
            "updated_at": node.get("updated_at")
        }

    return sorted(
        states.values(),
        key=lambda device: device.get("node_id") or ""
    )


@app.route("/api/firmware/releases", methods=["GET"])
def api_firmware_releases():
    try:
        return jsonify({
            "success": True,
            "releases": firmware_manager.list_releases()
        })
    except Exception as error:
        return firmware_error(error, 500)


@app.route("/api/firmware/releases", methods=["POST"])
def api_create_firmware_release():
    try:
        firmware_manager.ensure_storage()

        upload = request.files.get("firmware")

        if upload is None:
            return firmware_error(
                "Firmware file is required",
                400
            )

        original_filename = Path(
            upload.filename or "firmware.bin"
        ).name

        if not original_filename:
            return firmware_error(
                "Invalid firmware filename",
                400
            )

        staging_name = (
            f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}-"
            f"{original_filename}"
        )
        staging_path = firmware_manager.STAGING_DIR / staging_name
        upload.save(staging_path)

        try:
            release = firmware_manager.create_release(
                source_path=staging_path,
                original_filename=original_filename,
                version=request.form.get("version"),
                build=request.form.get("build"),
                hardware_family=request.form.get("hardware_family"),
                hardware_model=request.form.get("hardware_model"),
                hardware_revision=request.form.get("hardware_revision"),
                channel=request.form.get("channel") or "stable",
                release_notes=request.form.get("release_notes") or "",
                mandatory=get_form_bool(
                    request.form.get("mandatory")
                ),
                minimum_bootloader=request.form.get(
                    "minimum_bootloader"
                ),
                security_version=request.form.get(
                    "security_version"
                ) or 0,
                signature=request.form.get("signature")
            )
        finally:
            try:
                staging_path.unlink(
                    missing_ok=True
                )
            except Exception:
                pass

        create_log(
            severity="info",
            source="FIRMWARE",
            message=f"Firmware release {release['release_id']} uploaded"
        )

        return jsonify({
            "success": True,
            "release": release,
            "validation": {
                "valid": True,
                "sha256": release["sha256"],
                "file_size": release["file_size"],
                "manifest": "manifest.json"
            }
        }), 201

    except Exception as error:
        return firmware_error(error, 400)


@app.route("/api/firmware/releases/<release_id>", methods=["GET"])
def api_firmware_release(release_id):
    try:
        release = firmware_manager.get_release(
            release_id
        )

        if release is None:
            return firmware_error(
                "Release not found",
                404
            )

        return jsonify({
            "success": True,
            "release": release
        })
    except Exception as error:
        return firmware_error(error, 400)


@app.route("/api/firmware/releases/<release_id>/status", methods=["POST"])
def api_firmware_release_status(release_id):
    try:
        payload = request.get_json(
            silent=True
        ) or {}
        release = firmware_manager.update_release_status(
            release_id,
            payload.get("status")
        )

        if release is None:
            return firmware_error(
                "Release not found",
                404
            )

        create_log(
            severity="info",
            source="FIRMWARE",
            message=(
                f"Firmware release {release_id} moved "
                f"to {release['status']}"
            )
        )

        return jsonify({
            "success": True,
            "release": release
        })
    except Exception as error:
        return firmware_error(error, 400)


@app.route("/api/firmware/devices", methods=["GET"])
def api_firmware_devices():
    try:
        return jsonify({
            "success": True,
            "devices": get_firmware_device_rows()
        })
    except Exception as error:
        return firmware_error(error, 500)


@app.route("/api/firmware/devices/<node_id>", methods=["GET"])
def api_firmware_device(node_id):
    try:
        for device in get_firmware_device_rows():
            if device["node_id"] == node_id:
                return jsonify({
                    "success": True,
                    "device": device
                })

        return firmware_error(
            "Device not found",
            404
        )
    except Exception as error:
        return firmware_error(error, 400)


@app.route("/api/firmware/check", methods=["POST"])
def api_firmware_check():
    try:
        payload = request.get_json(
            silent=True
        ) or {}
        result = ota_manager.check_for_update(
            payload
        )
        release = result["release"]

        if not release:
            return jsonify({
                "success": True,
                "update_available": False
            })

        return jsonify({
            "success": True,
            "update_available": True,
            "release": {
                "release_id": release["release_id"],
                "version": release["version"],
                "build": release["build"],
                "download_url": release["download_url"],
                "size": release["file_size"],
                "sha256": release["sha256"]
            }
        })
    except Exception as error:
        return firmware_error(error, 400)


@app.route("/api/firmware/update", methods=["POST"])
def api_firmware_update():
    try:
        payload = request.get_json(
            silent=True
        ) or {}
        node_id = payload.get("node_id")
        release_id = payload.get("release_id")

        if not node_id or not release_id:
            return firmware_error(
                "node_id and release_id are required",
                400
            )

        job = ota_manager.create_update_job(
            node_id=node_id,
            release_id=release_id,
            authorized=get_form_bool(
                payload.get("authorized", True)
            )
        )

        return jsonify({
            "success": True,
            "job": job
        }), 201
    except Exception as error:
        return firmware_error(error, 400)


@app.route("/api/firmware/jobs", methods=["GET"])
def api_firmware_jobs():
    try:
        return jsonify({
            "success": True,
            "jobs": ota_manager.list_jobs(),
            "events": ota_manager.list_events()
        })
    except Exception as error:
        return firmware_error(error, 500)


@app.route("/api/firmware/jobs/<job_id>", methods=["GET"])
def api_firmware_job(job_id):
    try:
        job = ota_manager.get_job(
            job_id
        )

        if job is None:
            return firmware_error(
                "Job not found",
                404
            )

        return jsonify({
            "success": True,
            "job": job
        })
    except Exception as error:
        return firmware_error(error, 400)


@app.route("/api/firmware/jobs/<job_id>/state", methods=["POST"])
def api_firmware_job_state(job_id):
    try:
        payload = request.get_json(
            silent=True
        ) or {}
        job = ota_manager.update_job_state(
            job_id=job_id,
            state=payload.get("state"),
            progress=payload.get("progress"),
            result=payload.get("result"),
            error=payload.get("error")
        )

        if job is None:
            return firmware_error(
                "Job not found",
                404
            )

        return jsonify({
            "success": True,
            "job": job
        })
    except Exception as error:
        return firmware_error(error, 400)


@app.route("/api/firmware/device/<node_id>/check", methods=["POST"])
def api_firmware_device_check(node_id):
    try:
        payload = request.get_json(
            silent=True
        ) or {}
        node = node_manager.get_node(
            node_id
        )

        if node is None:
            return firmware_error(
                "Device not found",
                404
            )

        payload.update({
            "node_id": node_id,
            "hardware_family": (
                payload.get("hardware_family")
                or node.get("mcu_family")
            ),
            "hardware_model": (
                payload.get("hardware_model")
                or node.get("mcu_model")
            ),
            "hardware_revision": (
                payload.get("hardware_revision")
                or node.get("hardware_revision")
            ),
            "firmware_version": (
                payload.get("firmware_version")
                or node.get("firmware_version")
                or "0.0.0"
            ),
            "build": payload.get("build") or 0,
            "ota_protocol_version": (
                payload.get("ota_protocol_version") or 1
            )
        })

        result = ota_manager.check_for_update(
            payload
        )
        release = result["release"]

        return jsonify({
            "success": True,
            "update_available": bool(release),
            "release": release
        })
    except Exception as error:
        return firmware_error(error, 400)


@app.route("/api/firmware/download/<release_id>", methods=["GET"])
def api_firmware_download(release_id):
    try:
        release = firmware_manager.get_release(
            release_id
        )

        if release is None:
            return firmware_error(
                "Release not found",
                404
            )

        if release["status"] not in (
            "ACTIVE",
            "APPROVED",
            "TESTING"
        ):
            return firmware_error(
                "Release is not available for download",
                403
            )

        firmware_path = firmware_manager.firmware_path_for_release(
            release_id
        )

        return send_file(
            firmware_path,
            as_attachment=True,
            download_name="firmware.bin",
            mimetype="application/octet-stream"
        )
    except FileNotFoundError as error:
        return firmware_error(error, 404)
    except Exception as error:
        return firmware_error(error, 400)



# ============================================================
# FIRMWARE OTA CONFIGURATION
# ============================================================

@app.route("/api/firmware/config", methods=["GET"])
def api_firmware_config_get():

    try:

        return jsonify({
            "success": True,
            "config": ota_manager.get_ota_config()
        })

    except Exception as error:

        return firmware_error(
            error,
            500
        )


@app.route("/api/firmware/config", methods=["PUT"])
def api_firmware_config_put():

    try:

        payload = request.get_json(
            silent=True
        ) or {}

        config = ota_manager.save_ota_config(
            payload
        )

        create_log(
            severity="info",
            source="FIRMWARE",
            message="OTA configuration updated"
        )

        return jsonify({
            "success": True,
            "config": config
        })

    except Exception as error:

        return firmware_error(
            error,
            400
        )


# ============================================================
# LOGS API
# ============================================================

@app.route("/api/logs", methods=["GET"])
def get_logs():

    try:

        severity = request.args.get("severity", "").strip()
        search = request.args.get("search", "").strip()
        date_value = request.args.get("date", "").strip()

        connection = database.get_connection()
        cursor = connection.cursor()

        query = """
            SELECT
                id,
                timestamp,
                severity,
                source,
                message,
                node_id
            FROM logs
            WHERE 1=1
        """

        params = []

        if severity and severity.lower() != "all":

            query += """
                AND LOWER(severity) = LOWER(?)
            """

            params.append(severity)


        if search:

            query += """
                AND (
                    message LIKE ?
                    OR source LIKE ?
                    OR node_id LIKE ?
                )
            """

            search_value = f"%{search}%"

            params.extend([
                search_value,
                search_value,
                search_value
            ])


        if date_value:

            query += """
                AND DATE(timestamp) = DATE(?)
            """

            params.append(date_value)


        query += """
            ORDER BY timestamp DESC
            LIMIT 500
        """


        cursor.execute(
            query,
            params
        )


        rows = cursor.fetchall()

        connection.close()


        logs = [
            dict(row)
            for row in rows
        ]


        return jsonify({
            "success": True,
            "logs": logs
        })


    except Exception as error:

        print(
            "Logs API error:",
            error
        )

        return jsonify({
            "success": False,
            "error": str(error),
            "logs": []
        }), 500

# ============================================================
# SERVER STATUS
# ============================================================

@app.route("/api/status")
def status():

    return jsonify({
        "server": "SELVARITHIK'S LORA GATEWAY",
        "status": "online",
        "time": datetime.now().isoformat(),
        "nodes": len(node_manager.get_all_nodes())
    })


# ============================================================
# GET ALL NODES
# ============================================================

@app.route("/api/nodes", methods=["GET"])
def api_get_nodes():

    # Keep database status current whenever the dashboard or another page
    # polls the node list. This avoids stale ONLINE states without adding
    # another background worker.
    try:
        offline_nodes = node_manager.check_offline_nodes()
        for node in offline_nodes:
            create_log(
                severity="warning",
                source="NODE",
                message=f"Node offline: {node['name']} ({node['node_id']})",
                node_id=node["node_id"]
            )
    except Exception as error:
        print("Offline status check error:", error)

    return jsonify(
        node_manager.get_all_nodes()
    )


# ============================================================
# GET SINGLE NODE
# ============================================================

@app.route("/api/nodes/<node_id>", methods=["GET"])
def api_get_node(node_id):

    node = node_manager.get_node(node_id)

    if node is None:

        return jsonify({
            "success": False,
            "error": "Node not found"
        }), 404

    return jsonify(node)


# ============================================================
# ADD NODE
# ============================================================

@app.route("/api/nodes", methods=["POST"])
def api_add_node():

    data = request.get_json()

    try:

        node_manager.add_node(

            node_id=data["node_id"],

            name=data["name"],

            mcu_family=data.get(
                "mcu_family",
                ""
            ),

            mcu_model=data.get(
                "mcu_model",
                ""
            ),

            hardware_revision=data.get(
                "hardware_revision",
                ""
            ),

            firmware_version=data.get(
                "firmware_version",
                "v1.0.0"
            ),

            communication_type=data[
                "communication_type"
            ],

            communication_config=data.get(
                "communication_config",
                {}
            ),

            node_address=data.get(
                "node_address",
                ""
            ),

            enabled=bool(
                data.get(
                    "enabled",
                    True
                )
            )
        )

        create_log(
            severity="info",
            source="NODE",
            message=f"Node added: {data['name']} ({data['node_id']})",
            node_id=data["node_id"]
        )

        return jsonify({
            "success": True,
            "message": "Node added successfully"
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "error": str(error)
        }), 400


# ============================================================
# EDIT NODE
# ============================================================

@app.route(
    "/api/nodes/<node_id>",
    methods=["PUT"]
)
def api_update_node(node_id):

    data = request.get_json()

    if node_manager.get_node(node_id) is None:

        return jsonify({
            "success": False,
            "error": "Node not found"
        }), 404

    try:

        node_manager.update_node(

            node_id=node_id,

            name=data["name"],

            mcu_family=data.get(
                "mcu_family",
                ""
            ),

            mcu_model=data.get(
                "mcu_model",
                ""
            ),

            hardware_revision=data.get(
                "hardware_revision",
                ""
            ),

            firmware_version=data.get(
                "firmware_version",
                "v1.0.0"
            ),

            communication_type=data[
                "communication_type"
            ],

            communication_config=data.get(
                "communication_config",
                {}
            ),

            node_address=data.get(
                "node_address",
                ""
            ),

            enabled=bool(
                data.get(
                    "enabled",
                    True
                )
            )
        )
        create_log(
            severity="info",
            source="NODE",
            message=f"Node updated: {data['name']} ({node_id})",
            node_id=node_id
        )

        return jsonify({
            "success": True,
            "message": "Node updated successfully"
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "error": str(error)
        }), 400


# ============================================================
# DELETE NODE
# ============================================================

@app.route(
    "/api/nodes/<node_id>",
    methods=["DELETE"]
)
def api_delete_node(node_id):

    node = node_manager.get_node(node_id)

    if node is None:

        return jsonify({
            "success": False,
            "error": "Node not found"
        }), 404

    # Get name before deleting
    if isinstance(node, dict):
        node_name = node.get("name", node_id)
    else:
        try:
            node_name = node["name"]
        except Exception:
            node_name = node_id

    # Delete node
    node_manager.delete_node(node_id)

    # Create deletion log
    create_log(
        severity="warning",
        source="NODE",
        message=f"Node deleted: {node_name} ({node_id})",
        node_id=node_id
    )

    return jsonify({
        "success": True,
        "message": "Node deleted successfully"
    })
    
# ============================================================
# ENABLE / DISABLE NODE
# ============================================================

@app.route(
    "/api/nodes/<node_id>/enable",
    methods=["POST"]
)
def api_enable_node(node_id):

    data = request.get_json() or {}

    enabled = bool(
        data.get(
            "enabled",
            True
        )
    )

    if node_manager.get_node(node_id) is None:

        return jsonify({
            "success": False,
            "error": "Node not found"
        }), 404

    node_manager.set_node_enabled(
        node_id,
        enabled
    )

    return jsonify({
        "success": True,
        "enabled": enabled
    })

# ============================================================
# NODE CONFIGURATION API
# ============================================================

@app.route(
    "/api/nodes/<node_id>/config",
    methods=["GET"]
)
def api_get_node_config(node_id):

    config = config_manager.get_node_config_with_defaults(
        node_id
    )

    if config is None:

        return jsonify({
            "success": False,
            "error": "Node not found"
        }), 404

    return jsonify({
        "success": True,
        "config": config
    })


# ============================================================
# SAVE NODE CONFIGURATION
# ============================================================

@app.route(
    "/api/nodes/<node_id>/config",
    methods=["PUT"]
)
def api_save_node_config(node_id):

    data = request.get_json()

    config = data.get(
        "config",
        {}
    )

    success = config_manager.save_node_config(
        node_id,
        config
    )

    if not success:

        return jsonify({
            "success": False,
            "error": "Node not found"
        }), 404

    return jsonify({
        "success": True,
        "message": "Configuration saved"
    })


# ============================================================
# RESET DEFAULT CONFIGURATION
# ============================================================

@app.route(
    "/api/nodes/<node_id>/config/reset",
    methods=["POST"]
)
def api_reset_node_config(node_id):

    success = config_manager.reset_node_config(
        node_id
    )

    if not success:

        return jsonify({
            "success": False,
            "error": "Node not found"
        }), 404

    config = config_manager.load_node_config(
        node_id
    )

    return jsonify({
        "success": True,
        "message": "Configuration reset",
        "config": config
    })


# ============================================================
# SYSTEM MAINTENANCE API
# ============================================================

@app.route("/api/system/reboot", methods=["POST"])
def api_system_reboot():

    # Development/web-dashboard safe behavior: record the request instead
    # of terminating the Flask process. Real hardware reboot should be
    # implemented by the firmware/platform integration layer.
    create_log(
        severity="warning",
        source="SYSTEM",
        message="Gateway reboot requested"
    )

    return jsonify({
        "success": True,
        "message": "Reboot request accepted (development mode)"
    })


@app.route("/api/system/factory-reset", methods=["POST"])
def api_system_factory_reset():

    data = request.get_json() or {}

    if data.get("confirm") is not True:
        return jsonify({
            "success": False,
            "error": "Factory reset confirmation required"
        }), 400

    reset_count = 0

    for node in node_manager.get_all_nodes():
        if config_manager.reset_node_config(node["node_id"]):
            reset_count += 1

    create_log(
        severity="warning",
        source="SYSTEM",
        message=f"Gateway configuration factory reset completed for {reset_count} node(s)"
    )

    return jsonify({
        "success": True,
        "message": "Gateway configuration reset to defaults",
        "nodes_reset": reset_count
    })


# ============================================================
# SENSOR DATA MANAGEMENT
# ============================================================


@app.route(
    "/api/nodes/<node_id>/parameters",
    methods=["GET"]
)
def api_get_parameters(node_id):

    if node_manager.get_node(node_id) is None:

        return jsonify({
            "success": False,
            "error": "Node not found"
        }), 404


    return jsonify({
        "success": True,
        "parameters":
            sensor_manager.get_parameters(
                node_id
            )
    })


# ============================================================
# ADD PARAMETER
# ============================================================

@app.route(
    "/api/nodes/<node_id>/parameters",
    methods=["POST"]
)
def api_add_parameter(node_id):

    data = request.get_json() or {}


    try:

        sensor_manager.add_parameter(

            node_id=node_id,

            parameter_id=data[
                "parameter_id"
            ],

            parameter_name=data[
                "parameter_name"
            ],

            parameter_type=data[
                "parameter_type"
            ],

            data_type=data[
                "data_type"
            ],

            unit=data.get(
                "unit",
                ""
            ),

            sensor_id=data.get(
                "sensor_id"
            ),

            description=data.get(
                "description",
                ""
            ),

            enabled=data.get(
                "enabled",
                True
            ),

            display_enabled=data.get(
                "display_enabled",
                True
            ),

            graph_enabled=data.get(
                "graph_enabled",
                False
            ),

            decimal_places=data.get(
                "decimal_places",
                2
            ),

            min_value=data.get(
                "min_value"
            ),

            max_value=data.get(
                "max_value"
            ),

            alarm_enabled=data.get(
                "alarm_enabled",
                False
            ),

            low_alarm=data.get(
                "low_alarm"
            ),

            high_alarm=data.get(
                "high_alarm"
            )

        )


        return jsonify({
            "success": True,
            "message":
                "Parameter added successfully"
        })


    except Exception as error:

        return jsonify({
            "success": False,
            "error": str(error)
        }), 400


# ============================================================
# GET ONE PARAMETER
# ============================================================

@app.route(
    "/api/nodes/<node_id>/parameters/<parameter_id>",
    methods=["GET"]
)
def api_get_parameter(
    node_id,
    parameter_id
):

    parameter = sensor_manager.get_parameter(
            node_id,
            parameter_id
        )


    if parameter is None:

        return jsonify({
            "success": False,
            "error": "Parameter not found"
        }), 404


    return jsonify({
        "success": True,
        "parameter": parameter
    })


# ============================================================
# UPDATE PARAMETER
# ============================================================

@app.route(
    "/api/nodes/<node_id>/parameters/<parameter_id>",
    methods=["PUT"]
)
def api_update_parameter(
    node_id,
    parameter_id
):

    data = request.get_json() or {}


    success = sensor_manager.update_parameter(
            node_id,
            parameter_id,
            data
        )


    if not success:

        return jsonify({
            "success": False,
            "error": "Parameter not found"
        }), 404


    return jsonify({
        "success": True,
        "message":
            "Parameter updated successfully"
    })


# ============================================================
# DELETE PARAMETER
# ============================================================

@app.route(
    "/api/nodes/<node_id>/parameters/<parameter_id>",
    methods=["DELETE"]
)
def api_delete_parameter(
    node_id,
    parameter_id
):

    success = sensor_manager.delete_parameter(
            node_id,
            parameter_id
        )


    if not success:

        return jsonify({
            "success": False,
            "error": "Parameter not found"
        }), 404


    return jsonify({
        "success": True,
        "message":
            "Parameter deleted successfully"
    })


# ============================================================
# ENABLE / DISABLE PARAMETER
# ============================================================

@app.route(
    "/api/nodes/<node_id>/parameters/<parameter_id>/enable",
    methods=["POST"]
)
def api_enable_parameter(
    node_id,
    parameter_id
):

    data = request.get_json() or {}


    enabled = bool(
            data.get(
                "enabled",
                True
            )
        )


    success =  sensor_manager.set_parameter_enabled(
            node_id,
            parameter_id,
            enabled
        )


    if not success:

        return jsonify({
            "success": False,
            "error": "Parameter not found"
        }), 404


    return jsonify({
        "success": True,
        "enabled": enabled
    })


# ============================================================
# DEFAULT PARAMETER CATALOG
# ============================================================

@app.route(
    "/api/parameters/defaults",
    methods=["GET"]
)
def api_default_parameters():

    return jsonify({
        "success": True,
        "parameters":
            sensor_manager.get_default_parameters()
    })


# ============================================================
# GRAPH CONFIGURATION
# ============================================================

@app.route(
    "/api/nodes/<node_id>/parameters/<parameter_id>/graph",
    methods=["GET"]
)
def api_get_graph(
    node_id,
    parameter_id
):

    if sensor_manager.get_parameter(
        node_id,
        parameter_id
    ) is None:

        return jsonify({
            "success": False,
            "error": "Parameter not found"
        }), 404


    graph = sensor_manager.get_graph_config(
            node_id,
            parameter_id
        )


    return jsonify({
        "success": True,
        "graph": graph
    })


# ============================================================
# SAVE GRAPH CONFIG
# ============================================================

@app.route(
    "/api/nodes/<node_id>/parameters/<parameter_id>/graph",
    methods=["PUT"]
)
def api_save_graph(
    node_id,
    parameter_id
):

    data = request.get_json() or {}


    if sensor_manager.get_parameter(
        node_id,
        parameter_id
    ) is None:

        return jsonify({
            "success": False,
            "error": "Parameter not found"
        }), 404


    sensor_manager.update_graph_config(
        node_id,
        parameter_id,
        data
    )


    return jsonify({
        "success": True,
        "message":
            "Graph configuration saved"
    })


# ============================================================
# SAVE GENERIC TELEMETRY
# ============================================================

@app.route(
    "/api/telemetry",
    methods=["POST"]
)
def api_save_telemetry():

    data = request.get_json() or {}


    node_id = data.get("node_id")


    if not node_id:

        return jsonify({
            "success": False,
            "error": "node_id is required"
        }), 400


    parameters =  data.get(
            "parameters",
            {}
        )


    timestamp = data.get(
            "timestamp"
        )


    saved = telemetry_manager.save_parameters(
            node_id,
            parameters,
            timestamp
        )


    return jsonify({
        "success": True,
        "saved": saved
    })

# ============================================================
# LATEST PARAMETER VALUES
# ============================================================

@app.route(
    "/api/nodes/<node_id>/parameters/latest",
    methods=["GET"]
)
def api_latest_parameters(node_id):

    if node_manager.get_node(node_id) is None:

        return jsonify({
            "success": False,
            "error": "Node not found"
        }), 404

    data = telemetry_manager.get_latest_values(
        node_id
    )

    return jsonify({
        "success": True,
        "node_id": node_id,
        "parameters": data
    })


# ============================================================
# ALL PARAMETER STATISTICS
# ============================================================

@app.route(
    "/api/nodes/<node_id>/parameters/statistics",
    methods=["GET"]
)
def api_all_parameter_statistics(node_id):

    if node_manager.get_node(node_id) is None:

        return jsonify({
            "success": False,
            "error": "Node not found"
        }), 404

    limit = request.args.get(
        "limit",
        300,
        type=int
    )

    data = telemetry_manager.get_all_statistics(
        node_id,
        limit
    )

    return jsonify({
        "success": True,
        "node_id": node_id,
        "statistics": data
    })


# ============================================================
# ONE PARAMETER STATISTICS
# ============================================================

@app.route(
    "/api/nodes/<node_id>/parameters/<parameter_id>/statistics",
    methods=["GET"]
)
def api_parameter_statistics(
    node_id,
    parameter_id
):

    if sensor_manager.get_parameter(
        node_id,
        parameter_id
    ) is None:

        return jsonify({
            "success": False,
            "error": "Parameter not found"
        }), 404

    limit = request.args.get(
        "limit",
        300,
        type=int
    )

    data = telemetry_manager.get_statistics(
        node_id,
        parameter_id,
        limit
    )

    return jsonify({
        "success": True,
        "node_id": node_id,
        "parameter_id": parameter_id,
        "statistics": data
    })

# ============================================================
# TELEMETRY HISTORY
# ============================================================

@app.route(
    "/api/nodes/<node_id>/telemetry/<parameter_id>",
    methods=["GET"]
)
def api_parameter_history(
    node_id,
    parameter_id
):

    limit = request.args.get(
            "limit",
            300,
            type=int
        )


    history = telemetry_manager.get_history(
            node_id,
            parameter_id,
            limit
        )


    return jsonify({
        "success": True,
        "node_id": node_id,
        "parameter_id": parameter_id,
        "data": history
    })


# ============================================================
# TELEMETRY COMPARE / PIVOT
# ============================================================

@app.route(
    "/api/nodes/<node_id>/telemetry/compare",
    methods=["GET"]
)
def api_compare_telemetry(
    node_id
):

    parameter_ids = request.args.get(
            "parameters",
            ""
        )


    if not parameter_ids:

        return jsonify({
            "success": False,
            "error":
                "parameters query is required"
        }), 400


    parameter_list = [
            item.strip()
            for item in
            parameter_ids.split(",")
            if item.strip()
        ]


    limit = request.args.get(
            "limit",
            300,
            type=int
        )


    data = telemetry_manager.get_compare_data(
            node_id,
            parameter_list,
            limit
        )


    return jsonify({
        "success": True,
        "node_id": node_id,
        "parameters": parameter_list,
        "data": data
    })

# ============================================================
# COMMUNICATION CENTER
# ============================================================

# ------------------------------------------------------------
# GET COMMUNICATION STATUS
# ------------------------------------------------------------

@app.route(
    "/api/communication/status",
    methods=["GET"]
)
def api_communication_status():

    try:

        return jsonify({
            "success": True,
            "master_node_id":
                mesh_manager.get_master(),

            "gateway_connection":
                mesh_manager.get_gateway_connection(),

            "mesh_settings":
                mesh_manager.get_settings(),

            "statistics":
                communication_manager.get_statistics()
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


# ------------------------------------------------------------
# GET MESH TOPOLOGY
# ------------------------------------------------------------

@app.route(
    "/api/communication/mesh",
    methods=["GET"]
)
def api_communication_mesh():

    try:

        return jsonify({
            "success": True,
            "mesh":
                mesh_manager.get_topology()
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


# ------------------------------------------------------------
# GET MESH SETTINGS
# ------------------------------------------------------------

@app.route(
    "/api/communication/settings",
    methods=["GET"]
)
def api_communication_settings():

    try:

        return jsonify({
            "success": True,
            "settings":
                mesh_manager.get_settings()
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


# ------------------------------------------------------------
# UPDATE MESH SETTINGS
# ------------------------------------------------------------

@app.route(
    "/api/communication/settings",
    methods=["PUT"]
)
def api_update_communication_settings():

    try:

        data = request.get_json(
            silent=True
        ) or {}

        settings = (
            mesh_manager.update_settings(
                data
            )
        )

        return jsonify({
            "success": True,
            "settings": settings
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "error": str(error)
        }), 400


# ------------------------------------------------------------
# SET MASTER NODE
# ------------------------------------------------------------

@app.route(
    "/api/communication/master",
    methods=["PUT"]
)
def api_set_communication_master():

    try:

        data = request.get_json(
            silent=True
        ) or {}

        node_id = data.get(
            "node_id"
        )

        if not node_id:

            return jsonify({
                "success": False,
                "error":
                    "node_id is required"
            }), 400

        mesh_manager.set_master(
            node_id
        )

        return jsonify({
            "success": True,
            "master_node_id":
                mesh_manager.get_master()
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "error": str(error)
        }), 400


# ------------------------------------------------------------
# GET MASTER NODE
# ------------------------------------------------------------

@app.route(
    "/api/communication/master",
    methods=["GET"]
)
def api_get_communication_master():

    try:

        return jsonify({
            "success": True,
            "master_node_id":
                mesh_manager.get_master()
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


# ------------------------------------------------------------
# GATEWAY CONNECTION
# ------------------------------------------------------------

@app.route(
    "/api/communication/gateway",
    methods=["GET"]
)
def api_get_gateway_connection():

    try:

        return jsonify({
            "success": True,
            "gateway":
                mesh_manager.get_gateway_connection()
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


# ------------------------------------------------------------
# UPDATE GATEWAY CONNECTION
# ------------------------------------------------------------

@app.route(
    "/api/communication/gateway",
    methods=["PUT"]
)
def api_update_gateway_connection():

    try:

        data = request.get_json(
            silent=True
        ) or {}

        connection_type = data.get(
            "type"
        )

        if not connection_type:

            return jsonify({
                "success": False,
                "error":
                    "Gateway connection type is required"
            }), 400

        mesh_manager.set_gateway_connection(
            connection_type,
            enabled=data.get(
                "enabled",
                True
            ),
            config=data.get(
                "config",
                {}
            )
        )

        return jsonify({
            "success": True,
            "gateway":
                mesh_manager.get_gateway_connection()
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "error": str(error)
        }), 400


# ------------------------------------------------------------
# REGISTER MESH NODE
# ------------------------------------------------------------

@app.route(
    "/api/communication/mesh/nodes",
    methods=["POST"]
)
def api_register_mesh_node():

    try:

        data = request.get_json(
            silent=True
        ) or {}

        node_id = data.get(
            "node_id"
        )

        if not node_id:

            return jsonify({
                "success": False,
                "error":
                    "node_id is required"
            }), 400

        role = data.get(
            "role",
            "NODE"
        )

        node = mesh_manager.register_node(
            node_id,
            role
        )

        return jsonify({
            "success": True,
            "node": node
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "error": str(error)
        }), 400


# ------------------------------------------------------------
# REMOVE MESH NODE
# ------------------------------------------------------------

@app.route(
    "/api/communication/mesh/nodes/<node_id>",
    methods=["DELETE"]
)
def api_remove_mesh_node(
    node_id
):

    try:

        removed = (
            mesh_manager.remove_node(
                node_id
            )
        )

        if not removed:

            return jsonify({
                "success": False,
                "error":
                    "Mesh node not found"
            }), 404

        return jsonify({
            "success": True,
            "message":
                "Mesh node removed"
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "error": str(error)
        }), 400


# ------------------------------------------------------------
# UPDATE NODE-TO-NODE LINK
# ------------------------------------------------------------

@app.route(
    "/api/communication/mesh/link",
    methods=["POST"]
)
def api_update_mesh_link():

    try:

        data = request.get_json(
            silent=True
        ) or {}

        node_id = data.get(
            "node_id"
        )

        neighbor_id = data.get(
            "neighbor_id"
        )

        if not node_id or not neighbor_id:

            return jsonify({
                "success": False,
                "error":
                    "node_id and neighbor_id are required"
            }), 400

        link = mesh_manager.update_link(
            node_id,
            neighbor_id,
            rssi=data.get("rssi"),
            snr=data.get("snr"),
            success_rate=data.get(
                "success_rate"
            ),
            packet_loss=data.get(
                "packet_loss"
            ),
            latency_ms=data.get(
                "latency_ms"
            ),
            retries=data.get(
                "retries"
            )
        )

        return jsonify({
            "success": True,
            "link": link
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "error": str(error)
        }), 400


# ------------------------------------------------------------
# GET NODE NEIGHBORS
# ------------------------------------------------------------

@app.route(
    "/api/communication/mesh/<node_id>/neighbors",
    methods=["GET"]
)
def api_get_mesh_neighbors(
    node_id
):

    try:

        return jsonify({
            "success": True,
            "node_id": node_id,
            "neighbors":
                mesh_manager.get_neighbors(
                    node_id
                )
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


# ------------------------------------------------------------
# SELECT ROUTE
# ------------------------------------------------------------

@app.route(
    "/api/communication/route",
    methods=["GET"]
)
def api_select_communication_route():

    try:

        source = request.args.get(
            "source"
        )

        destination = request.args.get(
            "destination"
        )

        direction = request.args.get(
            "direction",
            "downlink"
        )

        if not source or not destination:

            return jsonify({
                "success": False,
                "error":
                    "source and destination are required"
            }), 400

        route = routing_manager.select_route(
            source,
            destination,
            direction
        )

        return jsonify({
            "success": True,
            "route": route
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "error": str(error)
        }), 400


# ------------------------------------------------------------
# CREATE + SEND COMMUNICATION PACKET
# ------------------------------------------------------------

@app.route(
    "/api/communication/send",
    methods=["POST"]
)
def api_communication_send():

    try:

        data = request.get_json(
            silent=True
        ) or {}

        packet_type = data.get(
            "packet_type"
        )

        source = data.get(
            "source"
        )

        destination = data.get(
            "destination"
        )

        payload = data.get(
            "payload",
            {}
        )

        direction = data.get(
            "direction"
        )

        require_ack = bool(
            data.get(
                "require_ack",
                True
            )
        )

        if not packet_type:

            return jsonify({
                "success": False,
                "error":
                    "packet_type is required"
            }), 400

        if not source:

            return jsonify({
                "success": False,
                "error":
                    "source is required"
            }), 400

        if not destination:

            return jsonify({
                "success": False,
                "error":
                    "destination is required"
            }), 400

        packet = (
            communication_manager
            .create_message(
                packet_type,
                source,
                destination,
                payload
            )
        )

        # Chat/control/etc. can request ACK.
        packet.setdefault(
            "flags",
            {}
        )[
            "ack_required"
        ] = require_ack

        result = (
            communication_manager.send(
                packet,
                direction=direction,
                require_ack=require_ack
            )
        )

        return jsonify({
            "success":
                result.get(
                    "success",
                    False
                ),

            "packet": packet,

            "result": result
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "error": str(error)
        }), 400


# ------------------------------------------------------------
# RECEIVE / TEST PACKET
# ------------------------------------------------------------

@app.route(
    "/api/communication/receive",
    methods=["POST"]
)
def api_communication_receive():

    try:

        data = request.get_json(
            silent=True
        )

        if data is None:

            return jsonify({
                "success": False,
                "error":
                    "JSON packet is required"
            }), 400

        result = (
            communication_manager.receive(
                data
            )
        )

        status_code = (
            200
            if result.get(
                "success"
            )
            else 400
        )

        return jsonify(
            result
        ), status_code

    except Exception as error:

        return jsonify({
            "success": False,
            "error": str(error)
        }), 400


# ------------------------------------------------------------
# COMMUNICATION STATISTICS
# ------------------------------------------------------------

@app.route(
    "/api/communication/statistics",
    methods=["GET"]
)
def api_communication_statistics():

    try:

        return jsonify({
            "success": True,
            "statistics":
                communication_manager
                .get_statistics()
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


# ------------------------------------------------------------
# OUTGOING QUEUE
# ------------------------------------------------------------

@app.route(
    "/api/communication/queue/outgoing",
    methods=["GET"]
)
def api_communication_outgoing_queue():

    try:

        queue = (
            communication_manager
            .get_outgoing_queue()
        )

        return jsonify({
            "success": True,
            "count": len(queue),
            "queue": queue
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


# ------------------------------------------------------------
# INCOMING QUEUE
# ------------------------------------------------------------

@app.route(
    "/api/communication/queue/incoming",
    methods=["GET"]
)
def api_communication_incoming_queue():

    try:

        queue = (
            communication_manager
            .get_incoming_queue()
        )

        return jsonify({
            "success": True,
            "count": len(queue),
            "queue": queue
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


# ------------------------------------------------------------
# CLEAR TEST QUEUES
# ------------------------------------------------------------

@app.route(
    "/api/communication/queue/clear",
    methods=["POST"]
)
def api_communication_clear_queues():

    try:

        communication_manager.clear_queues()

        return jsonify({
            "success": True,
            "message":
                "Communication queues cleared"
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


# ============================================================
# PRIVATE CHAT
#
# IMPORTANT:
# - Gateway <-> registered node private chat only.
# - NO ESP32 <-> ESP32 M2M communication.
# - NO communication_manager.
# - Node names come from Node Management.
# ============================================================

def _chat_error(
    message,
    status_code=400
):

    return jsonify({
        "success": False,
        "error": message
    }), status_code


@app.route(
    "/api/chat/users",
    methods=["GET"]
)
def api_chat_users():

    try:

        users = get_chat_users()

        return jsonify({
            "success": True,
            "users": users
        })

    except Exception as error:

        print(
            "[CHAT] Users API error:",
            error
        )

        return _chat_error(
            str(error),
            500
        )


@app.route(
    "/api/chat/conversations",
    methods=["GET"]
)
def api_chat_conversations():

    try:

        user_id = (
            request.args
            .get(
                "user_id",
                "GATEWAY"
            )
            .strip()
        )

        conversations = chat_get_conversations(
                user_id
            )

        return jsonify({
            "success": True,
            "user_id": user_id,
            "conversations":
                conversations or []
        })

    except Exception as error:

        return _chat_error(
            str(error),
            500
        )


@app.route(
    "/api/chat/messages",
    methods=["GET"]
)
def api_chat_messages():

    try:

        user_id = (
            request.args
            .get(
                "user_id",
                "GATEWAY"
            )
            .strip()
        )

        with_user_id = (
            request.args
            .get(
                "with_user_id",
                ""
            )
            .strip()
        )

        if not with_user_id:

            return _chat_error(
                "with_user_id is required"
            )

        limit = request.args.get(
            "limit",
            200,
            type=int
        )

        limit = max(
            1,
            min(
                limit,
                500
            )
        )

        conversation_id = (
            ":".join(
                sorted(
                    [
                        user_id,
                        with_user_id
                    ]
                )
            )
        )

        messages = chat_get_messages(
                user_id,
                conversation_id,
                limit
            )

        return jsonify({
            "success": True,
            "user_id": user_id,
            "with_user_id":
                with_user_id,
            "messages":
                messages or []
        })

    except Exception as error:

        print(
            "[CHAT] Messages API error:",
            error
        )

        return _chat_error(
            str(error),
            500
        )


@app.route(
    "/api/chat/messages",
    methods=["POST"]
)
def api_chat_send_message():

    try:

        data = request.get_json(
                silent=True
            ) or {}

        sender_id = str(
            data.get(
                "sender_id",
                ""
            )
        ).strip()

        recipient_id = str(
            data.get(
                "recipient_id",
                ""
            )
        ).strip()

        content = str(
            data.get(
                "content",
                ""
            )
        ).strip()

        if sender_id != "GATEWAY":

            return _chat_error(
                "Invalid chat sender"
            )

        if not recipient_id:

            return _chat_error(
                "recipient_id is required"
            )

        if not content:

            return _chat_error(
                "Message cannot be empty"
            )

        message = chat_send_message(
                sender_id,
                recipient_id,
                content
            )

        try:

            socketio.emit(
                "chat_message",
                message
            )

        except Exception as socket_error:

            print(
                "[CHAT] Socket error:",
                socket_error
            )

        return jsonify({
            "success": True,
            "message":
                message
        })

    except Exception as error:

        print(
            "[CHAT] Send error:",
            error
        )

        return _chat_error(
            str(error),
            400
        )


@app.route(
    "/api/chat/messages/<message_id>",
    methods=["GET"]
)
def api_chat_get_message(
    message_id
):

    try:

        message = chat_get_message(
                message_id
            )

        if message is None:

            return _chat_error(
                "Message not found",
                404
            )

        return jsonify({
            "success": True,
            "message":
                message
        })

    except Exception as error:

        return _chat_error(
            str(error),
            500
        )


@app.route(
    "/api/chat/messages/<message_id>/delivered",
    methods=["POST"]
)
def api_chat_mark_delivered(
    message_id
):

    try:

        result = chat_mark_delivered(
                message_id
            )

        return jsonify({
            "success": True,
            "message_id":
                message_id,
            "result":
                result
        })

    except Exception as error:

        return _chat_error(
            str(error),
            400
        )


@app.route(
    "/api/chat/messages/<message_id>/seen",
    methods=["POST"]
)
def api_chat_mark_seen(
    message_id
):

    try:

        data = request.get_json(
                silent=True
            ) or {}

        receiver_id = str(
                data.get(
                    "receiver_id",
                    "GATEWAY"
                )
            ).strip()

        result = chat_mark_seen(
                message_id,
                receiver_id
            )

        return jsonify({
            "success": True,
            "message_id":
                message_id,
            "result":
                result
        })

    except Exception as error:

        return _chat_error(
            str(error),
            400
        )
# ============================================================
# TELEMETRY
# ============================================================

@socketio.on("telemetry")
def receive_telemetry(data):

    # ========================================================
    # BASIC VALIDATION
    # ========================================================

    if not isinstance(data, dict):
        print("[TELEMETRY] Ignored packet: invalid data")
        return

    node_id = data.get("node_id")

    if not node_id:
        print("[TELEMETRY] Ignored packet: missing node_id")
        return

    received_at = datetime.now().isoformat()

    # ========================================================
    # STORE LIVE DATA IN MEMORY
    # ========================================================

    nodes[node_id] = data

    # ========================================================
    # CHECK REGISTERED NODE
    # ========================================================

    node = node_manager.get_node(node_id)

    if node is None:

        print(
            f"[TELEMETRY] Unknown node received: {node_id}"
        )

    else:

        # Disabled node must never become ONLINE
        if node.get("enabled"):

            node_manager.update_node_status(
                node_id,
                "online",
                received_at
            )

        else:

            print(
                f"[TELEMETRY] Disabled node ignored: "
                f"{node_id}"
            )

    # ========================================================
    # EXTRACT TELEMETRY SECTIONS SAFELY
    # ========================================================

    sensor = data.get("sensor") or {}
    battery = data.get("battery") or {}
    lora = data.get("lora") or {}

    # ========================================================
    # NORMALIZED TELEMETRY VALUES
    # ========================================================

    field_map = {

        "temperature":
            sensor.get("temperature"),

        "humidity":
            sensor.get("humidity"),

        "battery_voltage":
            battery.get("voltage"),

        "battery_percent":
            battery.get("percent"),

        "current_ma":
            battery.get("current_ma"),

        "power_mw":
            battery.get("power_mw"),

        "rssi":
            lora.get("rssi"),

        "snr":
            lora.get("snr"),

        "packets_tx":
            lora.get("packets_tx"),

        "packets_rx":
            lora.get("packets_rx")
    }

    # ========================================================
    # GET REGISTERED PARAMETERS
    # ========================================================

    parameter_values = {}

    try:

        registered_parameters = (
            sensor_manager.get_parameters(node_id)
        )

        for parameter in registered_parameters:

            parameter_id = (
                parameter.get("parameter_id")
            )

            parameter_name = (
                parameter.get("parameter_name")
                or ""
            ).strip().lower()

            if not parameter_id:
                continue

            value = None

            # ------------------------------------------------
            # TEMPERATURE
            # ------------------------------------------------

            if (
                "temperature" in parameter_name
                or parameter_id.lower()
                in (
                    "temperature",
                    "temp"
                )
            ):

                value = field_map["temperature"]

            # ------------------------------------------------
            # HUMIDITY
            # ------------------------------------------------

            elif (
                "humidity" in parameter_name
                or parameter_id.lower()
                in (
                    "humidity",
                    "hum"
                )
            ):

                value = field_map["humidity"]

            # ------------------------------------------------
            # BATTERY VOLTAGE
            # ------------------------------------------------

            elif (
                "battery" in parameter_name
                and "voltage" in parameter_name
            ):

                value = (
                    field_map["battery_voltage"]
                )

            elif parameter_id.lower() in (
                "battery_voltage",
                "battery_voltage_v",
                "bat_voltage"
            ):

                value = (
                    field_map["battery_voltage"]
                )

            # ------------------------------------------------
            # BATTERY PERCENT
            # ------------------------------------------------

            elif (
                "battery" in parameter_name
                and (
                    "percent" in parameter_name
                    or "percentage" in parameter_name
                    or "level" in parameter_name
                    or "%" in parameter_name
                )
            ):

                value = (
                    field_map["battery_percent"]
                )

            elif parameter_id.lower() in (
                "battery_percent",
                "battery_percentage",
                "battery_level",
                "bat_percent"
            ):

                value = (
                    field_map["battery_percent"]
                )

            # ------------------------------------------------
            # CURRENT
            # ------------------------------------------------

            elif (
                "current" in parameter_name
                or parameter_id.lower()
                in (
                    "current",
                    "current_ma"
                )
            ):

                value = (
                    field_map["current_ma"]
                )

            # ------------------------------------------------
            # POWER
            # ------------------------------------------------

            elif (
                "power" in parameter_name
                or parameter_id.lower()
                in (
                    "power",
                    "power_mw"
                )
            ):

                value = (
                     field_map["power_mw"] / 1000
                     if field_map["power_mw"] is not None
                      else None
                     )

            # ------------------------------------------------
            # RSSI
            # ------------------------------------------------

            elif (
                "rssi" in parameter_name
                or parameter_id.lower()
                == "rssi"
            ):

                value = field_map["rssi"]

            # ------------------------------------------------
            # SNR
            # ------------------------------------------------

            elif (
                "snr" in parameter_name
                or parameter_id.lower()
                == "snr"
            ):

                value = field_map["snr"]

            # ------------------------------------------------
            # PACKETS TX
            # ------------------------------------------------

            elif (
                "packet" in parameter_name
                and "tx" in parameter_name
            ):

                value = (
                    field_map["packets_tx"]
                )

            elif parameter_id.lower() in (
                "packets_tx",
                "packet_tx"
            ):

                value = (
                    field_map["packets_tx"]
                )

            # ------------------------------------------------
            # PACKETS RX
            # ------------------------------------------------

            elif (
                "packet" in parameter_name
                and "rx" in parameter_name
            ):

                value = (
                    field_map["packets_rx"]
                )

            elif parameter_id.lower() in (
                "packets_rx",
                "packet_rx"
            ):

                value = (
                    field_map["packets_rx"]
                )

            # ------------------------------------------------
            # SAVE MATCHED VALUE
            # ------------------------------------------------

            if value is not None:

                parameter_values[
                    parameter_id
                ] = value

    except Exception as error:

        print(
            "[TELEMETRY] Parameter mapping error "
            f"for {node_id}: {error}"
        )

    # ========================================================
    # SAVE TELEMETRY HISTORY
    # ========================================================

    if parameter_values:

        try:

            saved = (
                telemetry_manager.save_parameters(
                    node_id,
                    parameter_values,
                    timestamp=received_at
                )
            )

            print(
                f"[TELEMETRY] {node_id} | "
                f"saved {saved} parameter values"
            )

        except Exception as error:

            print(
                "[TELEMETRY] Database save error "
                f"for {node_id}: {error}"
            )

    else:

        print(
            f"[TELEMETRY] {node_id} | "
            "no matching registered parameters"
        )

    # ========================================================
    # SAFE CONSOLE OUTPUT
    # ========================================================

    print(
        f"[TELEMETRY] {node_id} | "
        f"TEMP={sensor.get('temperature', '--')} C | "
        f"HUM={sensor.get('humidity', '--')} % | "
        f"BAT={battery.get('percent', '--')} % | "
        f"RSSI={lora.get('rssi', '--')} dBm"
    )

    # ========================================================
    # LIVE DASHBOARD UPDATE
    # ========================================================

    socketio.emit(
        "node_update",
        data
    )
# ============================================================
# SEND NODES TO DASHBOARD
# ============================================================

@socketio.on("get_nodes")
def send_nodes():

    database_nodes = (
        node_manager.get_all_nodes()
    )


    for node in database_nodes:

        emit(
            "registered_node",
            node
        )


    for data in nodes.values():

        emit(
            "node_update",
            data
        )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("=" * 60)

    print(
        "SELVARITHIK'S LORA GATEWAY"
    )

    print(
        "ESP32 / ESP8266 / Arduino "
        "Gateway Control Center"
    )

    print("=" * 60)

    print(
        "Dashboard: "
        "http://127.0.0.1:5000"
    )

    print("=" * 60)


    socketio.run(
        app,
        host="127.0.0.1",
        port=5000,
        debug=True,
        allow_unsafe_werkzeug=True
    )
