from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import unittest

from wp_auto_poster_gui.core.scheduler_service import ScheduleConfig, SchedulerService, _parse_run_at, _parse_time


class SchedulerServiceTest(unittest.TestCase):
    def test_save_and_load_config(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "schedule.json"
            service = SchedulerService(path)
            service.save_config(
                ScheduleConfig(
                    enabled=True,
                    excel_path="posts.xlsx",
                    frequency="once",
                    run_at="2026-07-06T15:30:00",
                    weekday="fri",
                )
            )

            loaded = SchedulerService(path).config

            self.assertTrue(loaded.enabled)
            self.assertEqual(loaded.excel_path, "posts.xlsx")
            self.assertEqual(loaded.frequency, "once")
            self.assertEqual(loaded.run_at, "2026-07-06T15:30:00")
            self.assertEqual(loaded.weekday, "fri")

    def test_parse_time_validation(self) -> None:
        self.assertEqual(_parse_time("23:59"), (23, 59))
        with self.assertRaises(ValueError):
            _parse_time("25:00")

    def test_parse_run_at_validation(self) -> None:
        run_at = _parse_run_at("2026-07-06T15:30:00")
        self.assertEqual(run_at, datetime(2026, 7, 6, 15, 30))
        with self.assertRaises(ValueError):
            _parse_run_at("06/07/2026 15:30")

    def test_once_schedule_uses_date_trigger(self) -> None:
        service = SchedulerService()
        future = (datetime.now() + timedelta(hours=1)).isoformat(timespec="seconds")
        service.config = ScheduleConfig(enabled=True, frequency="once", run_at=future)

        trigger = service._build_trigger()

        self.assertEqual(trigger.__class__.__name__, "DateTrigger")


if __name__ == "__main__":
    unittest.main()
