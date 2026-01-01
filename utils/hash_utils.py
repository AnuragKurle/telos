"""Perceptual hashing utilities for screenshot comparison."""

from PIL import Image
import imagehash
from typing import Optional


class ScreenshotHasher:
    """Manages perceptual hashing for screenshot comparison."""

    def __init__(self):
        self.last_hash: Optional[imagehash.ImageHash] = None

    def compute_hash(self, image_path: str) -> imagehash.ImageHash:
        """Compute perceptual hash of an image."""
        img = Image.open(image_path)
        return imagehash.phash(img)

    def is_duplicate(self, image_path: str, threshold: int = 0) -> bool:
        """Check if image is duplicate of last screenshot.

        Args:
            image_path: Path to the screenshot
            threshold: Hamming distance threshold (0 = exact match, higher = more tolerant)

        Returns:
            True if duplicate, False otherwise
        """
        current_hash = self.compute_hash(image_path)

        if self.last_hash is None:
            self.last_hash = current_hash
            return False

        hamming_distance = current_hash - self.last_hash

        if hamming_distance <= threshold:
            return True

        self.last_hash = current_hash
        return False

    def reset(self) -> None:
        """Reset the last hash (useful when resuming after idle)."""
        self.last_hash = None
