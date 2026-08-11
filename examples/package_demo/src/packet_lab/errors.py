class PacketError(Exception):
    """Base exception exposed by packet_lab."""


class PacketFormatError(PacketError):
    """The input is not a valid packet_lab wire value."""
