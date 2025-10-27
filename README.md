# Orei HDMI Matrix - Home Assistant Custom Integration

Control your **Orei HDMI Matrix** switch directly from **Home Assistant** via Telnet.

Supports power control, input/output switching, live state updates, and manual refresh.  
Compatible with multiple Orei models such as **UHD48-EX230-K**, etc.

---

## ✨ Features

- 🧠 **Automatic model detection** (`r type!`)
- 🔌 **Global power control** (on/off)
- 🎛 **Per-zone source selection** as media players
- 🔄 **Manual refresh service** (`orei_matrix.refresh`)
- 🧩 **Dynamic device grouping** (all entities under one device)
- 🪄 **Config Flow setup** (no YAML required)
- 🧰 **Support for 4x4, 8x8, and other Orei matrix models**

---

## 🖼 Example UI

When configured, you’ll see a single device in Home Assistant:

> **Orei UHD48-EX230-K**
>
> - 🔌 `switch.orei_matrix_power`
> - 🎚 `media_player.living_room`
> - 🎚 `media_player.bedroom`
> - 🎚 `media_player.office`
> - 🎚 `media_player.patio`

---

## ⚙️ Installation

### 🧩 HACS (Recommended)

1. Go to **HACS → Integrations → Custom Repositories**
2. Add this repository URL https://github.com/taysuus/hass-orei-matrix as type **Integration**
3. Search for **Orei HDMI Matrix** and install it.
4. Restart Home Assistant.

### 📦 Manual

1. Copy the `custom_components/orei_matrix` folder into: <config>/custom_components/orei_matrix/
2. Restart Home Assistant.

---

## 🧠 Configuration

Set up via the **Home Assistant UI**:

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Orei HDMI Matrix**
3. Enter:

- **Host** (IP of your Orei Matrix)
- **Port** (default: 23)
- **Source Names** (e.g. `"Apple TV"`, `"Blu-ray"`, `"PC"`, `"Game Console"`)
- **Zone Names** (e.g. `"Living Room"`, `"Bedroom"`, `"Patio"`, `"Office"`)

That’s it — entities will be created automatically.

---

## 🧩 Entities

| Entity                     | Description                                          |
| -------------------------- | ---------------------------------------------------- |
| `switch.orei_matrix_power` | Controls main matrix power                           |
| `media_player.<zone>`      | Represents each output zone (allows input selection) |

Each media player exposes:

- **Current source**
- **Source selection list** (using configured names)
- **Availability** (grayed out when matrix power is off)

---

## 🧰 Services

### `orei_matrix.refresh`

Manually refreshes all matrix states immediately — power, model, and routing.

#### Example usage (Developer Tools → Services)

```yaml
service: orei_matrix.refresh
```
