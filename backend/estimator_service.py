import os
import tempfile
from datetime import datetime
from importlib.machinery import SourceFileLoader


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


MOTOR_CONFIG = {
    "ofertas": {
        "module_name": "motor_ofertas",
        "file_name": "testeo_ofertas.py",
        "prefix": "ofertas",
    },
    "equipos": {
        "module_name": "motor_recuento",
        "file_name": "testeo_lista_equipos.py",
        "prefix": "equipos",
    },
}


def load_motor(mode: str):
    if mode not in MOTOR_CONFIG:
        raise ValueError(f"Unsupported mode: {mode}")

    config = MOTOR_CONFIG[mode]
    path = os.path.join(BASE_DIR, config["file_name"])

    if not os.path.exists(path):
        raise FileNotFoundError(f"Motor file not found: {config['file_name']}")

    module = SourceFileLoader(config["module_name"], path).load_module()

    if not hasattr(module, "ejecutar_estimacion"):
        raise AttributeError(f"{config['file_name']} does not expose ejecutar_estimacion")

    if not hasattr(module, "guardar_excel_estilizado"):
        raise AttributeError(f"{config['file_name']} does not expose guardar_excel_estilizado")

    return module


def build_output_name(original_name: str, mode: str) -> str:
    base = os.path.splitext(os.path.basename(original_name))[0]
    safe_base = "".join(
        c if c.isalnum() or c in ("-", "_") else "_"
        for c in base
    ).strip("_")

    date_part = datetime.utcnow().strftime("%Y%m%d")

    return f"stimation-{mode}-{safe_base}-{date_part}.xlsx"


def process_estimation(
    input_bytes: bytes,
    original_filename: str,
    mode: str,
    include_audit: bool = False,
) -> tuple[bytes, str]:
    """
    Receives uploaded Excel bytes, runs the Python motor, returns output Excel bytes
    and the recommended filename.
    """

    motor = load_motor(mode)
    output_name = build_output_name(original_filename, mode)

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, original_filename)
        output_path = os.path.join(tmpdir, output_name)

        with open(input_path, "wb") as f:
            f.write(input_bytes)

        comparativa_path = find_comparativa_file()

        motor.ejecutar_estimacion(
            input_path,
            comparativa_path,
            output_path,
        )

        if not os.path.exists(output_path):
            raise FileNotFoundError(
                "The motor did not generate the expected output Excel file."
            )

        with open(output_path, "rb") as f:
            output_bytes = f.read()

    return output_bytes, output_name


def find_comparativa_file() -> str:
    """
    Locate the standard comparison Excel file required by the motors.
    Replace the candidate names below with the real packaged file name at deployment.
    """

    candidates = [
        os.path.join(BASE_DIR, "data", "comparativa.xlsx"),
        os.path.join(BASE_DIR, "comparativa.xlsx"),
    ]

    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate

    raise FileNotFoundError(
        "Standard comparison file not found. Expected data/comparativa.xlsx or comparativa.xlsx"
    )
