# Sweet Home Integration

A Home Assistant custom integration for controlling MCP23017 GPIO expander chips on Raspberry Pi. This integration provides button and binary sensor functionality for home automation projects.

## Features

- Support for multiple MCP23017 chips (addresses 0x20 and 0x21)
- Button press detection (single, double, triple, and long press)
- Binary sensor support for door/window sensors
- Real-time interrupt-based detection
- Device automation triggers

## Hardware Requirements

- Raspberry Pi with I2C enabled
- MCP23017 GPIO expander chip(s)
- Pull-up resistors for buttons/sensors (10kΩ recommended)
- Proper wiring for interrupt pins

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Go to "Integrations"
3. Click "Custom repositories"
4. Add `https://github.com/dautushenka/sweet_home` as an Integration
5. Install "Sweet Home"
6. Restart Home Assistant

### Manual Installation

1. Copy the `sweet_home` folder to your `custom_components` directory
2. Restart Home Assistant

## Configuration

### I2C Setup

First, enable I2C on your Raspberry Pi:

```bash
sudo raspi-config
# Navigate to Interfacing Options > I2C > Enable
```

### YAML Configuration

Add the following to your `configuration.yaml`:

```yaml
sweet_home:
  switches:
    - name: "Living Room Controls"
      id: "living_room"
      buttons:
        - address: "0x20"
          pin: "0"
          press_count: "single_press"
        - address: "0x20"
          pin: "1"
          press_count: "double_press"
        - address: "0x20"
          pin: "2"
          press_count: "triple_press"

    - name: "Kitchen Controls"
      id: "kitchen"
      buttons:
        - address: "0x21"
          pin: "0"
          press_count: "single_press"
```

### Binary Sensor Configuration

For door/window sensors:

```yaml
binary_sensor:
  - platform: sweet_home
    address: "0x20"
    pin: "3"
    device_class: door
```

## Wiring

### MCP23017 to Raspberry Pi

| MCP23017 Pin | Raspberry Pi Pin | Description |
|--------------|------------------|-------------|
| VDD          | 3.3V             | Power       |
| VSS          | GND              | Ground      |
| SCL          | GPIO 3 (SCL)     | I2C Clock   |
| SDA          | GPIO 2 (SDA)     | I2C Data    |
| INTA         | GPIO 27          | Interrupt A |
| INTB         | GPIO 22          | Interrupt B |

### Button Wiring

- Connect buttons between MCP23017 pins and GND
- Internal pull-up resistors are enabled automatically
- Use pins 0-15 for buttons (0-7 on Port A, 8-15 on Port B)

## Device Automation

The integration creates device triggers that can be used in automations:

```yaml
automation:
  - alias: "Living Room Light Toggle"
    trigger:
      platform: device
      domain: sweet_home
      device_id: living_room
      type: single_press
      subtype: button_1
    action:
      service: light.toggle
      target:
        entity_id: light.living_room
```

## Troubleshooting

### I2C Issues

Check if I2C is working:

```bash
sudo i2cdetect -y 1
```

You should see your MCP23017 chips at addresses 0x20 and/or 0x21.

### Permission Issues

Ensure Home Assistant has access to I2C:

```bash
sudo usermod -a -G i2c homeassistant
```

### GPIO Conflicts

Make sure no other integrations are using GPIO pins 27 and 22 for interrupts.

## Dependencies

- smbus-cffi
- pigpio
- RPi.GPIO

These are automatically installed when the integration is loaded.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and feature requests, please use the [GitHub Issues](https://github.com/dautushenka/sweet_home/issues) page.