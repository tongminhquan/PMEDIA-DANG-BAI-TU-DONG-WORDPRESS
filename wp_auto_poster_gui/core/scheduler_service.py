from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
import json
from typing import Callable


@dataclass
class ScheduleConfig:
    enabled: bool = False
    excel_path: str = ""
    image_folder: str = ""
    frequency: str = "daily"
    time: str = "09:00"
    run_at: str = ""
    weekday: str = "mon"
    cron_expression: str = ""
    max_images_per_post: int = 2
    image_alignment: str = "aligncenter"
    image_display_size: str = "auto"
    image_custom_width: int = 800
    last_run_at: str | None = None
    last_result: str | None = None


class SchedulerService:
    def __init__(self, config_path: str | Path = "config/schedule.json"):
        self.config_path = Path(config_path)
        self.config = self.load_config()
        self._scheduler = None
        self._job = None

    def load_config(self) -> ScheduleConfig:
        if not self.config_path.exists():
            return ScheduleConfig()
        data = json.loads(self.config_path.read_text(encoding="utf-8-sig"))
        return ScheduleConfig(**{**asdict(ScheduleConfig()), **data})

    def save_config(self, config: ScheduleConfig | None = None) -> None:
        if config is not None:
            self.config = config
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(
            json.dumps(asdict(self.config), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def start(self, job_callback: Callable[[], str | None]) -> None:
        if not self.config.enabled:
            self.stop()
            return
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
        except ImportError as exc:  # pragma: no cover - depends on environment
            raise RuntimeError("APScheduler is required for automatic scheduling") from exc

        self.stop()
        self._scheduler = BackgroundScheduler()
        self._job = self._scheduler.add_job(self._run_job, self._build_trigger(), args=[job_callback], id="auto_post")
        self._scheduler.start()

    def stop(self) -> None:
        if self._scheduler:
            self._scheduler.shutdown(wait=False)
        self._scheduler = None
        self._job = None

    def next_run_time(self) -> str | None:
        if self._job and self._job.next_run_time:
            return self._job.next_run_time.isoformat(timespec="minutes")
        return None

    def _run_job(self, job_callback: Callable[[], str | None]) -> None:
        self.config.last_run_at = datetime.now().isoformat(timespec="seconds")
        try:
            self.config.last_result = job_callback() or "Completed"
            if self.config.frequency == "once":
                self.config.enabled = False
        except Exception as exc:
            self.config.last_result = f"Failed: {exc}"
            raise
        finally:
            self.save_config()

    def _build_trigger(self):
        from apscheduler.triggers.cron import CronTrigger
        from apscheduler.triggers.date import DateTrigger

        if self.config.frequency == "once":
            run_at = _parse_run_at(self.config.run_at)
            if run_at <= datetime.now():
                raise ValueError("Scheduled run time must be in the future")
            return DateTrigger(run_date=run_at)
        hour, minute = _parse_time(self.config.time)
        if self.config.frequency == "daily":
            return CronTrigger(hour=hour, minute=minute)
        if self.config.frequency == "weekly":
            return CronTrigger(day_of_week=self.config.weekday, hour=hour, minute=minute)
        if self.config.frequency == "custom":
            return CronTrigger.from_crontab(self.config.cron_expression)
        raise ValueError(f"Unsupported schedule frequency: {self.config.frequency}")


def _parse_time(value: str) -> tuple[int, int]:
    try:
        hour, minute = value.split(":", 1)
        parsed = int(hour), int(minute)
    except Exception as exc:
        raise ValueError("Time must use HH:MM format") from exc
    if not (0 <= parsed[0] <= 23 and 0 <= parsed[1] <= 59):
        raise ValueError("Time must use HH:MM format")
    return parsed


def _parse_run_at(value: str) -> datetime:
    if not value:
        raise ValueError("Scheduled run time is required")
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("Scheduled run time must use ISO format") from exc
