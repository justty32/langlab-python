import unittest

from packet_lab import Packet, PacketFormatError, decode, encode


class CodecTests(unittest.TestCase):
    def test_round_trip_binary_payload(self) -> None:
        packet = Packet(kind="data", payload=b"\x00hello\xff")
        self.assertEqual(decode(encode(packet)), packet)

    def test_encoding_is_deterministic(self) -> None:
        packet = Packet(kind="ping", payload=b"hello")
        self.assertEqual(
            encode(packet),
            b'{"kind":"ping","payload_base64":"aGVsbG8="}',
        )

    def test_decode_translates_json_error(self) -> None:
        with self.assertRaises(PacketFormatError) as context:
            decode(b"not json")
        self.assertIsNotNone(context.exception.__cause__)

    def test_decode_rejects_invalid_base64(self) -> None:
        with self.assertRaises(PacketFormatError):
            decode(b'{"kind":"data","payload_base64":"%%%"}')


if __name__ == "__main__":
    unittest.main()
