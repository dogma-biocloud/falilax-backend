from __future__ import annotations

import logging
import os
import sys
import time

from app.workers.alert_delivery_worker import AlertDeliveryWorker

log = logging.getLogger(__name__)


def _configure_logging() -> None:
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )


def main() -> int:
    _configure_logging()

    poll_seconds = float(os.getenv("ALERT_WORKER_POLL_SECONDS", "5"))
    batch_limit = int(os.getenv("ALERT_WORKER_BATCH_LIMIT", "50"))

    log.info("Alert worker starting (poll=%ss batch_limit=%s)", poll_seconds, batch_limit)

    worker = AlertDeliveryWorker()

    while True:
        try:
            delivered = worker.deliver_pending(limit=batch_limit)
            if delivered:
                log.info("Delivered batch count=%s", delivered)
            time.sleep(poll_seconds)

        except KeyboardInterrupt:
            log.info("Alert worker stopped (KeyboardInterrupt)")
            return 0

        except Exception:
            # Keep running even if something fails
            log.exception("Alert worker loop error")
            time.sleep(max(poll_seconds, 2))

    # unreachable
    # return 0


if __name__ == "__main__":
    raise SystemExit(main())