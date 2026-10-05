# Bluetooth capture (host-side)

This repo’s firmware does not enable the FM-1’s radio, but you may still want **Bluetooth capture** when debugging **Bluetooth MIDI** on your computer (e.g. BlueZ + a Bluetooth-MIDI device).

## Quick start (Linux / BlueZ)

Capture to `btsnoop` (Wireshark can open it directly):

```bash
sudo python3 tools/bt_capture.py --iface hci0 -o capture.btsnoop
```

Capture for 30 seconds and convert to `pcapng` (requires `editcap`):

```bash
sudo python3 tools/bt_capture.py --iface hci0 -d 30 --pcapng -o capture.pcapng
```

## Dependencies

- `btmon` (BlueZ; package often named `bluez`)
- `editcap` (optional, for pcapng conversion; package often `wireshark-common`)

## Notes

- This captures **host-side HCI traffic** (what your Linux machine’s Bluetooth controller sees).
- For over-the-air sniffing you typically need a dedicated sniffer; this tool does not provide that.

