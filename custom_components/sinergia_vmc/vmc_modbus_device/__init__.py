"""Device library for Sinergia VMC units (CPRO3OEM-K electronics) over Modbus RTU."""

from .device import (
    Alarms,
    Command,
    CompressorStatusCode,
    DamperStatusCode,
    DigitalIO,
    Enables,
    FanSpeeds,
    FanStatusCode,
    Maintenance,
    ModeStatusCode,
    Outputs,
    Probes,
    RecircDamperStatusCode,
    Setpoints,
    Status,
    UnitStatusCode,
    VmcDevice,
)

__all__ = [
    "Alarms",
    "Command",
    "CompressorStatusCode",
    "DamperStatusCode",
    "DigitalIO",
    "Enables",
    "FanSpeeds",
    "FanStatusCode",
    "Maintenance",
    "ModeStatusCode",
    "Outputs",
    "Probes",
    "RecircDamperStatusCode",
    "Setpoints",
    "Status",
    "UnitStatusCode",
    "VmcDevice",
]

__version__ = "0.1.0"
