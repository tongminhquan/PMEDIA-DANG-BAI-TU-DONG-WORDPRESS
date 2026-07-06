from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from wp_auto_poster_gui.core.scheduler_service import ScheduleConfig, SchedulerService, _parse_time


class SchedulerServiceTest(unittest.TestCase):
    def test_save_and_load_config(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "schedule.json"
            service = SchedulerService(path)
            service.save_config(ScheduleConfig(enabled=True, excel_path="posts.xlsx", frequency="weekly", weekday="fri"))

            loaded = SchedulerService(path).config

            self.assertTrue(loaded.enabled)
            self.assertEqual(loaded.excel_path, "posts.xlsx")
            self.assertEqual(loaded.weekday, "fri")

    def test_parse_time_validation(self) -> None:
        self.assertEqual(_parse_time("23:59"), (23, 59))
        with self.assertRaises(ValueError):
            _parse_time("25:00")


if __name__ == "__main__":
    unittest.main()
