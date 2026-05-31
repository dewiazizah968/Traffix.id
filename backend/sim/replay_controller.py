"""Dataset replay cursor controller for Traffix simulation ticks."""

from sim.dataset_loader import HybridTrafficDatasetLoader
from sim.dataset_models import DatasetRow


class ReplayController:
    """Sequential replay cursor over hybrid traffic dataset rows."""

    def __init__(
        self,
        dataset_loader: HybridTrafficDatasetLoader | None = None,
    ) -> None:
        """Initialize the replay controller.

        Args:
            dataset_loader: Optional dataset loader dependency.
        """
        self._dataset_loader = dataset_loader or HybridTrafficDatasetLoader()
        self._rows: list[DatasetRow] | None = None
        self._cursor = 0

    def _load_rows(self) -> list[DatasetRow]:
        """Load and cache replay rows.

        Returns:
            Cached dataset rows in replay order.
        """
        if self._rows is None:
            self._rows = self._dataset_loader.get_rows()
        return self._rows

    def reset(self) -> None:
        """Reset replay cursor to the beginning of the cached dataset."""
        self._cursor = 0

    def get_cursor(self) -> int:
        """Return current replay cursor position.

        Returns:
            Current zero-based cursor index.
        """
        return self._cursor

    def has_rows(self) -> bool:
        """Return whether the replay dataset has rows.

        Returns:
            True when at least one row is available.
        """
        return len(self._load_rows()) > 0

    def next_batch(self) -> list[DatasetRow]:
        """Return the next timestamp batch and advance the replay cursor.

        Returns:
            Rows sharing the next replay timestamp. Returns an empty list when
            the dataset has no rows.
        """
        rows = self._load_rows()
        if not rows:
            return []

        if self._cursor >= len(rows):
            self._cursor = 0

        current_timestamp = rows[self._cursor].timestamp
        batch: list[DatasetRow] = []

        while self._cursor < len(rows):
            row = rows[self._cursor]
            if row.timestamp != current_timestamp:
                break
            batch.append(row)
            self._cursor += 1

        return batch
