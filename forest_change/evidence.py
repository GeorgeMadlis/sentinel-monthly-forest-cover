import hashlib
import json
from pathlib import Path

import yaml

NON_CLAIMS = [
    "Monthly/seasonal disturbance is not automatically legal deforestation.",
    "Hansen annual loss is not monthly ground truth; external/annual reconciliation remains necessary.",
    "Optical anomalies can reflect phenology, clouds, fire, agriculture, moisture or other causes.",
    "SAR changes depend on moisture, geometry, terrain and acquisition conditions.",
    "S1/S2 agreement increases screening confidence but does not establish causal attribution.",
    "Outputs are provisional candidates, not persistence-confirmed forest state or causal loss labels.",
    "Terrain flattening and speckle filtering must be supplied upstream; this workflow does not implement them.",
    "Pixel-centre AOI rasterization approximates boundary area at the configured resolution.",
    "Optical quality masks are applied on the target grid; bilinear reprojection can mix values near cloud-mask boundaries.",
]
# Forest Cover Lab concepts whose meaning the statements above restate; never redefined here.
CLAIM_IDS = ["claim:monthly-non-truth"]
SENSOR_CONCEPTS = {"observation:optical-vegetation-state": "optical", "observation:sar-backscatter-state": "sar"}
EVIDENCE_MODES = {
    "optical_only": "Optical-only evidence: SAR does not enter the disturbance decision.",
    "sar_only": "Degraded SAR-only mode: no optical evidence enters the decision; SAR backscatter alone is not diagnostic of forest loss.",
    "optical_and_sar": "Optical AND SAR: pixels lacking either sensor remain nodata.",
    "optical_or_sar": "Optical OR SAR: pixels lacking either sensor remain nodata.",
    "weighted_confidence": "Weighted candidate vote (not calibrated probability): pixels lacking either sensor remain nodata.",
}


def load(path):
    return yaml.safe_load(Path(path).read_text())


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")


def geometry_hash(geometry):
    return hashlib.sha256(json.dumps(geometry, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def checksum(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()
