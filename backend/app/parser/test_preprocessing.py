from __future__ import annotations

import unittest

from .preprocessing import preprocess_log


class TestPreprocessing(unittest.TestCase):
    def test_hdfs_style_line(self) -> None:
        raw = (
            '081109 203615 148 INFO dfs.DataNode$PacketResponder: '
            'PacketResponder 1 for block blk_38865049064139660 terminating'
        )
        expected = 'dfs.datanode$packetresponder: packetresponder <*> for block <*> terminating'
        self.assertEqual(preprocess_log(raw), expected)

    def test_ip_and_hex_normalization(self) -> None:
        raw = '2026-04-06 12:00:03 ERROR request from 10.2.4.8 failed at 0x7fff for id 42'
        expected = 'request from <*> failed at <*> for id <*>'
        self.assertEqual(preprocess_log(raw), expected)

    def test_uuid_normalization(self) -> None:
        raw = '2026-04-06 12:00:03 WARN user uuid 550e8400-e29b-41d4-a716-446655440000 disconnected'
        expected = 'user uuid <*> disconnected'
        self.assertEqual(preprocess_log(raw), expected)


def run_preprocessing_examples() -> None:
    examples = [
        (
            '081109 203615 148 INFO dfs.DataNode$PacketResponder: PacketResponder 1 for block '
            'blk_38865049064139660 terminating',
            'dfs.datanode$packetresponder: packetresponder <*> for block <*> terminating',
        ),
        (
            '2026-04-06 12:00:03 ERROR request from 10.2.4.8 failed at 0x7fff for id 42',
            'request from <*> failed at <*> for id <*>',
        ),
    ]

    for raw, expected in examples:
        actual = preprocess_log(raw)
        print('RAW      :', raw)
        print('PROCESSED:', actual)
        print('EXPECTED :', expected)
        print('MATCH    :', actual == expected)
        print('-' * 80)


if __name__ == '__main__':
    unittest.main()
