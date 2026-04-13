# Charge-Up Data — Interpretation & Findings
**File:** `chargeup.txt`  
**Date Analyzed:** 13-Apr-2026  
**Source:** Charge-Up platform — real-time WebSocket/MQTT message stream

---

## 1. What Is This File?

This is a **live telemetry message stream** — each line is a JSON message prefixed with `"Received message:"`, fired by the Charge-Up tracking platform in real time. It is **not a CSV or a database export** — it's a raw IoT push feed (likely WebSocket or MQTT), captured as plain text.

- **Total lines (messages):** 38  
- **Capture window:** ~2 minutes (05:33:57 → 05:35:58 UTC, Oct 24, 2025 — 11:03 IST)
- **Ping frequency per vehicle:** ~30 seconds (very high resolution — same as your V3 CAN data)

---

## 2. Vehicles Observed

| Vehicle Name | Device ID | Tag | Odometer | Cycle Count | SOC | Location |
|---|---|---|---|---|---|---|
| `CGF25C0076` | 64892 | GreenFuel | 5381.761 km | 79 | 75% | Agra/Mathura area (27.5°N, 77.6°E) |
| `CGF25H0037` | 65461 | GreenFuel | 960.187 km | 10 | 98% | Jaipur area (26.9°N, 75.8°E) |
| `CIN25G0101` | 65702 | Inverted | 6882.999 km | 27 | 95% | Delhi NCR area (28.9°N, 77.0°E) |
| `CIN25G0102` | 65734 | Inverted | 5187.528 km | 56 | 55% | Gwalior area (26.2°N, 78.1°E) |
| `CIN25H0018` | 65749 | Inverted | 1712.038 km | 34 | 87% | Gwalior area (26.2°N, 78.1°E) |

**Fleet type:** Most likely **electric 3-wheelers (e-rickshaws)** — pack voltage ~52-54V (48V nominal), 16-cell LFP chemistry. ⚠️ *Note: vehicle type not explicitly stated in data. Inferred from: (1) "GreenFuel" and "Inverted" are well-known e-rickshaw battery brands in India, (2) GPS locations (Agra, Gwalior, Jaipur belt) are high e-rickshaw density zones, (3) 48V 16S LFP packs are the dominant e-rickshaw pack configuration.*  
**Two BMS firmware variants seen:**
- `eChargeup-GreenFuel_v1.1_030625` → GreenFuel tagged vehicles
- `eChargeup-Inverted_v1.1_03` / `eC_Inverted_DS_v4_250825-0` → Inverted tagged vehicles

---

## 3. Full Field Inventory

Every message has two main sections — `attributes` (current snapshot) and `attributehistory` (timestamped last-known values per field). The actual data fields are:

### 3a. Battery / BMS Fields

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `SOC` | int (%) | `75`, `87`, `95` | State of Charge → **your primary target** |
| `SOH` | int (%) | `99`, `100` | State of Health |
| `battVoltage` | float (V) | `52.95`, `54.24` | Pack voltage |
| `battCurrent` | float (A) | `-7.41`, `23.52` | Battery current (−=discharge, +=charge) |
| `battCapacity` | float/str (%) | `"75.000"`, `87.04` | Current capacity % (mirrors SOC in some FW) |
| `fullCapacity` | int | `100` | Full rated capacity flag |
| `battEnergy` | float/str (Wh) | `"3971.250"`, `4602.675` | Cumulative energy throughput |
| `cycleCount` | int | `10`, `34`, `56`, `79` | Charge cycle count |
| `calPower` | int/str (mW) | `1920`, `"-391.841"` | Calculated instantaneous power (mW units?) |
| `CharDischarState` | int | `0`, `1`, `2` | 0=idle, 1=charging, 2=discharging |
| `charMOS` | int | `1` | Charge MOSFET status (1=on) |
| `disCharMOS` | int | `1` | Discharge MOSFET status (1=on) |
| `loadStatus` | int | `0`, `1` | Load/motor connected status |
| `charTemp` | float (°C) | `0`, `29` | Charging temperature |
| `discharTemp` | float (°C) | `0`, `28`, `29` | Discharge temperature |

### 3b. Temperature Sensors (5 physical sensors!)

| Field | Example | Description |
|-------|---------|-------------|
| `temp1` | `34`, `34.9`, `37.4` | Primary thermal sensor (MOS or cell) |
| `mosTemp` | `34`, `34.9` | MOSFET temperature (usually mirrors temp1) |
| `temp2` | `29`, `29.3`, `33.8` | Secondary cell temp |
| `temp3` | `29`, `29.6`, `34.3` | Third cell temp |
| `temp4` | `29`, `29.4`, `34.3` | Fourth cell temp |
| `temp5` | `29`, `""` | Fifth temp (empty on Inverted FW variant) |
| `temp6` | `0`, `""` | Sixth temp (unused/empty on most) |
| `maxTemp` | `28`, `34` | Max temp across all sensors |
| `minTemp` | `0`, `29` | Min temp (often 0 = sensor not connected) |
| `tempCount` | `5` | Number of active temp sensors |

### 3c. Individual Cell Voltages (16 cells!)

`C1` through `C16` — individual LFP cell voltages in Volts.  
Example: `C1: 3.273, C2: 3.273 ... C16: 3.27` (range: ~3.24–3.38 V)

Also aggregated:
| Field | Example | Description |
|-------|---------|-------------|
| `maxCellVoltage` | `3.275` | Highest cell voltage |
| `minCellVoltage` | `3.266` | Lowest cell voltage |
| `cellVoltDiff` | `"0.009"` | Max−Min spread (imbalance indicator) |
| `cellCount` | `16` | Number of cells in pack |

### 3d. GPS & Motion

| Field | Example | Description |
|-------|---------|-------------|
| `latitude` | `27.56651` | GPS latitude |
| `longitude` | `77.68126` | GPS longitude |
| `speed` | `0`, `19.446`, `31.1136` | Speed in **km/h** (float) |
| `course` | `0` | Heading (degrees) |
| `motion` | `true/false` | Motion detection flag |
| `state` | `"moving"` | Vehicle state label |
| `fixTime` | `2025-10-24T11:03:39+0530` | GPS fix time (IST) |
| `deviceTime` | `2025-10-24T05:33:39Z` | Device UTC time |
| `lastupdate` | `2025-10-24T05:33:57Z` | Server receipt time |
| `sat` | `0`, `15`, `18`, `21` | GPS satellites locked |

### 3e. Odometry

| Field | Example | Description |
|-------|---------|-------------|
| `odometer` | `5381761` | Odometer in **meters** |
| `odokm` | `5381.761` | Odometer in **km** (= odometer / 1000) |

### 3f. Fault Flags (BMS)

| Field | Value | Meaning |
|-------|-------|---------|
| `COV` | 0 | Cell Over Voltage |
| `CUV` | 0 | Cell Under Voltage |
| `batOVA` / `batUVA` | 0 | Battery Over/Under Voltage Alarm |
| `batOTA` / `batUTA` | 0 | Battery Over/Under Temp Alarm |
| `charOCA` / `disOCA` | 0 | Over-current during charge/discharge |
| `charOTA` / `disOTA` | 0 | Over-temp during charge/discharge |
| `charUTA` / `disUTA` | 0 | Under-temp during charge/discharge |
| `mosOTA` | 0 | MOS Over Temp |
| `shortCircuit` | 0 | Short circuit |
| `thermRA` | 0 | Thermal runaway alarm |
| `PRLF` | 0 | PCB Relay Latch Fault |
| `OCCD` | 0 | Over-current in charging direction |
| `OTA` / `UTA` | 0 | Over/Under Temp Alarm |
| `cellDiffFault` | 0 | Cell voltage difference fault |
| `cellConnectionBroken` | 0 | Cell connection broken |
| `cvSensingFailure` | 0 | Cell voltage sensing failure |
| `tempSensorFail` | 0 | Temperature sensor failure |
| `softMOSlock` | `""` | Software MOS lock string |

### 3g. Device / Tracker Metadata

| Field | Example | Description |
|-------|---------|-------------|
| `name` | `CGF25C0076` | Vehicle registration/name |
| `uniqueid` | `864524076251200` | IMEI of GPS tracker |
| `bmsID` | `"14131211"` | BMS hardware ID |
| `battSerialNumber` | `"GFLP3001I25CU027"` | Battery serial number |
| `fwVersion` | `eChargeup-GreenFuel_v1.1_030625` | BMS firmware version |
| `swVersion` | `""`, `"4"`, `"J"` | Software version |
| `type` | `"evbasic"` | Device profile type |
| `rssi` | `-61`, `-81` | Signal strength (dBm) |
| `CANBusStatus` | `0`, `4` | CAN Bus status code |
| `CANStatus` | `0`, `1`, `4` | CAN communication status |
| `tot_rst` | `5`, `79`, `122`, `1438` | Total system resets |
| `rst_rsn` | `1`, `4`, `11` | Last reset reason code |
| `devicetags` | `["GreenFuel"]` | Fleet grouping tag |

### 3h. Raw CAN Packet

Each message also contains a `data` field with the full raw IOBOT NMEA-style packet:
```
$IOBOT,<IMEI>,<date>,<time>,<lat>,N,<lon>,E,<speed>,<heading>,<flags...>,<hex CAN frames>,<counters>#
```
This is the original BMS CAN frame dump — useful if you need to decode fields not parsed by the platform.

---

## 4. Feature Map: V3 Model → Charge-Up Data

| V3 Feature | Status | Charge-Up Field | Notes |
|------------|--------|-----------------|-------|
| `battery_voltage` | ✅ **Direct** | `battVoltage` | Already float (V) |
| `current` | ✅ **Direct** | `battCurrent` | Already float (A), negative=discharge |
| `soc` | ✅ **Direct** | `SOC` | Already int (%), no parsing needed |
| `soh` | ✅ **Direct** | `SOH` | Already int (%) |
| `power` | ✅ **Derivable** | Compute `battVoltage × battCurrent` | Or use `calPower` (mW-scale, needs unit check) |
| `speed` | ✅ **Direct** | `speed` | Already float (km/h) |
| `distance_km` | ✅ **Derivable** | `odokm` diff between pings | Use Δodokm per window, more accurate than speed×time |
| `cell_temperature_01` | ✅ **Direct** | `temp1` or `mosTemp` | Primary thermal sensor |
| `cell_temperature_02` | ✅ **Direct** | `temp2` | Second sensor — no zero-fill needed! |
| `cell_temperature_03` | ✅ **Direct** | `temp3` | Third sensor — no zero-fill needed! |
| `hour` | ✅ **Derivable** | Extract from `deviceTime` or `lastupdate` | Standard timestamp parsing |
| `day_of_week` | ✅ **Derivable** | Extract from `deviceTime` | Standard timestamp parsing |
| `month` | ✅ **Derivable** | Extract from `deviceTime` | Standard timestamp parsing |
| `minute_of_day` | ✅ **Derivable** | Extract from `deviceTime` | Standard timestamp parsing |
| `ignstatus` | ✅ **Derivable** | `motion` (bool) or `speed > 0` | `motion=True` → 1 |
| `allow_charging` | ✅ **Direct** | `charMOS` | 1 = charge MOSFET open = charging allowed |
| `allow_discharging` | ✅ **Direct** | `disCharMOS` | 1 = discharge MOSFET open = discharging allowed |

**Result: 17/17 features — 100% coverage. All V3 features are available in Charge-Up data.**

---

## 5. Charge-Up Bonus Features (not in V3)

These exist in Charge-Up but were NOT used in V3 training — adding them could improve your model:

| Bonus Field | Potential Value for Model |
|-------------|--------------------------|
| `temp2`, `temp3`, `temp4` | Multiple real temp sensors (V3 only had 1!) |
| `mosTemp` | MOSFET temperature — indicates electrical load |
| `cycleCount` | Charge cycles — captures battery ageing directly |
| `battEnergy` | Cumulative Wh throughput — long-term degradation |
| `C1`–`C16` | Individual cell voltages — detect imbalance |
| `cellVoltDiff` | Pre-computed cell imbalance metric |
| `maxCellVoltage` / `minCellVoltage` | Cell health extremes |
| `CharDischarState` | Clean 3-state flag (idle/charge/discharge) |
| `calPower` | Instantaneous power (mW or W — verify scale) |
| `loadStatus` | Motor load connected/disconnected |
| `odokm` | Lifetime km — vehicle-level degradation proxy |
| `tot_rst` | Total system resets — device reliability signal |

---

## 6. Data Quality Assessment

| Concern | Finding |
|---------|---------|
| **Ping frequency** | ~30 seconds — same as V3 CAN data ✅ |
| **GPS coverage** | `sat=0` on `CGF25C0076` (speed=0 anyway) — no GPS fix when parked. Others: 15–21 sats locked ✅ |
| **Missing fields** | `temp5`, `temp6` empty on Inverted FW variant — use `tempCount` to detect ⚠️ |
| **Data types** | `battCapacity` and `battEnergy` are strings on GreenFuel FW, floats on Inverted FW — needs type normalization ⚠️ |
| **`calPower` units** | Values like `1920`, `720` (GreenFuel) vs `"-391.841"`, `"1275.725"` (Inverted) — likely mW vs W — normalize! ⚠️ |
| **`maxCellVoltage` units** | GreenFuel: `3.275` (Volts) vs Inverted: `3307` (millivolts) — firmware inconsistency! Must normalize ⚠️ |
| **`OTA`, `OCCD`, `UTA`, `PRLF`** | Empty string `""` on Inverted FW (vs `0` on GreenFuel) — cast to int with fallback ⚠️ |
| **`SOC` values** | Clean integers (54, 55, 75, 87, 95, 98) — no string parsing needed ✅ |
| **Two FW variants** | GreenFuel vs Inverted behave differently for several fields — preprocess separately or add FW-type flag |

---

## 7. Comparison: Charge-Up vs Evify 2.0 vs V3

| Capability | V3 (original) | Evify 2.0 | Charge-Up |
|------------|--------------|-----------|-----------|
| **SOC** | ✅ | ✅ (string parse) | ✅ (int, no parse) |
| **SOH** | ✅ | ✅ (string parse) | ✅ (int, no parse) |
| **Pack Voltage** | ✅ | ✅ (string parse) | ✅ (float, clean) |
| **Battery Current** | ✅ | ✅ (string parse) | ✅ (float, clean) |
| **Speed** | ✅ (from GPS) | ✅ (float) | ✅ (float) |
| **Temp Sensor 1** | ✅ | ✅ (string parse) | ✅ (float, clean) |
| **Temp Sensor 2** | ❌ (zero-fill) | ❌ (zero-fill) | ✅ **Real data!** |
| **Temp Sensor 3** | ❌ (zero-fill) | ❌ (zero-fill) | ✅ **Real data!** |
| **allow_charging flag** | ✅ | ⚠️ proxy | ✅ **Exact** (`charMOS`) |
| **allow_discharging flag** | ✅ | ⚠️ proxy | ✅ **Exact** (`disCharMOS`) |
| **Ignition status** | ✅ (from GPS) | ✅ | ✅ (`motion` field) |
| **Individual cell voltages** | ❌ | ❌ | ✅ **16 cells!** |
| **Cycle count** | ❌ | ❌ | ✅ |
| **Ping frequency** | ~30s CAN / 5min GPS | ~30–60s | ~30s |
| **V3 feature coverage** | 17/17 | 13/17 | **17/17 (100%)** |
| **Data format** | CSV (zipped) | JSON (MongoDB) | JSON lines (stream) |

---

## 8. Conclusion

**Charge-Up is the best data source of all three for retraining V3.**

- **100% V3 feature coverage** — no proxies or zero-fills needed
- **Multiple real temperature sensors** — where V3 had to zero-fill cells 2 & 3, Charge-Up has up to 5 real sensors
- **Exact BMS flags** — `charMOS` and `disCharMOS` are the actual allow_charging/allow_discharging signals V3 used
- **30-second ping rate** — matches V3's CAN resolution exactly, so the same 5-minute resampling pipeline applies directly
- **16 individual cell voltages** — bonus data for detecting imbalance, far richer than Evify

### Preprocessing Steps Needed Before Training
1. **Normalize data types** — `battCapacity`, `battEnergy` → cast to float (remove string quotes)
2. **Normalize `calPower` units** — GreenFuel (mW) vs Inverted (W?) — multiply/divide as needed
3. **Normalize `maxCellVoltage`/`minCellVoltage`** — GreenFuel (V) vs Inverted (mV) — divide Inverted values by 1000
4. **Handle empty fault fields** — replace `""` with `0` for `OTA`, `OCCD`, etc. on Inverted FW
5. **Parse timestamp** — use `deviceTime` (UTC) as the canonical time column
6. **Resample to 5-minute windows** — same pipeline as V3 (aggregate per vehicle per window)
7. **Filter active driving** — `speed >= 1.0` and `abs(battCurrent) > 0.1`

### Sample Parsing Code (Quick Start)
```python
import json, re
import pandas as pd

records = []
with open("chargeup.txt", "r") as f:
    for line in f:
        line = line.strip()
        if line.startswith("Received message:"):
            json_str = line[len("Received message:"):].strip()
            data = json.loads(json_str)
            attr = data.get("attributes", {})
            records.append({
                "vehicle_id"    : data.get("name"),
                "time"          : pd.to_datetime(data.get("deviceTime")),
                "soc"           : attr.get("SOC"),
                "soh"           : attr.get("SOH"),
                "battVoltage"   : attr.get("battVoltage"),
                "battCurrent"   : attr.get("battCurrent"),
                "speed"         : data.get("speed"),
                "odokm"         : attr.get("odokm"),
                "temp1"         : attr.get("temp1"),
                "temp2"         : attr.get("temp2"),
                "temp3"         : attr.get("temp3"),
                "charMOS"       : attr.get("charMOS"),
                "disCharMOS"    : attr.get("disCharMOS"),
                "motion"        : int(attr.get("motion", False)),
                "cycleCount"    : attr.get("cycleCount"),
                "CharDischarState": attr.get("CharDischarState"),
                "cellVoltDiff"  : float(attr.get("cellVoltDiff", 0) or 0),
            })

df = pd.DataFrame(records)
df["power"] = df["battVoltage"] * df["battCurrent"]
df["hour"]  = df["time"].dt.hour
df["day_of_week"] = df["time"].dt.dayofweek
df["month"] = df["time"].dt.month
df["minute_of_day"] = df["time"].dt.hour * 60 + df["time"].dt.minute
```

---
*Trickee Project | 13-Apr-2026*
