# Peripherals

Track monitors, keyboards, headsets, docking stations, and other peripheral devices with assignment history and custom properties.

## Peripheral types

Common peripheral categories: monitors, keyboards, mice, headsets, webcams, docking stations, cables, adapters. Categories are configurable.

## Assigning peripherals

1. Navigate to **Core Inventory → Peripherals**.
2. Click **Add Peripheral**.
3. Provide: name, type, serial number, and condition.
   Brand and model come from the shared lists described in [Brands & Models](brands-models.md).
4. Assign to a user — creates a `PeripheralAssignment` record tracking who has the peripheral and since when.
5. Transfers between users close the current assignment and create a new one, preserving full history.

## Custom properties

Peripherals support custom fields (via `CustomPropertiesMixin`), just like hardware assets. Define fields in **Administration → Configuration → Custom Fields**.
