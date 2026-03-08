"""
Progress tracking for long-running operations.

Provides callbacks and status updates for podcast generation.
"""

import logging
from typing import Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class ProgressStage(Enum):
    """Stages of podcast generation."""
    INITIALIZING = "initializing"
    EXTRACTING_CONTENT = "extracting_content"
    GENERATING_SCRIPT = "generating_script"
    GENERATING_AUDIO = "generating_audio"
    MERGING_AUDIO = "merging_audio"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ProgressStatus:
    """Current progress status."""
    stage: ProgressStage
    message: str
    percent: float = 0.0
    current_step: int = 0
    total_steps: int = 0
    elapsed_seconds: float = 0.0
    error: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "stage": self.stage.value,
            "message": self.message,
            "percent": round(self.percent, 1),
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "elapsed_seconds": round(self.elapsed_seconds, 1),
            "error": self.error,
        }


class ProgressTracker:
    """
    Track progress of podcast generation.
    
    Usage:
        tracker = ProgressTracker(on_progress=lambda p: print(p.message))
        tracker.start()
        tracker.update(ProgressStage.EXTRACTING_CONTENT, "Extracting PDF...")
        tracker.update_step(1, 5, "Processing segment 1 of 5")
        tracker.complete()
    """
    
    def __init__(self, on_progress: Optional[Callable[[ProgressStatus], Any]] = None):
        self.on_progress = on_progress
        self.start_time: Optional[datetime] = None
        self.current_status: Optional[ProgressStatus] = None
        
        # Stage weights for overall progress calculation
        self._stage_weights = {
            ProgressStage.INITIALIZING: 5,
            ProgressStage.EXTRACTING_CONTENT: 10,
            ProgressStage.GENERATING_SCRIPT: 25,
            ProgressStage.GENERATING_AUDIO: 50,
            ProgressStage.MERGING_AUDIO: 8,
            ProgressStage.FINALIZING: 2,
        }
        self._stage_order = list(self._stage_weights.keys())
    
    def start(self) -> None:
        """Start tracking progress."""
        self.start_time = datetime.now()
        self.update(ProgressStage.INITIALIZING, "Starting podcast generation...")
    
    def update(self, stage: ProgressStage, message: str) -> None:
        """Update progress to a new stage."""
        elapsed = self._elapsed_seconds()
        percent = self._calculate_percent(stage, 0, 1)
        
        self.current_status = ProgressStatus(
            stage=stage,
            message=message,
            percent=percent,
            elapsed_seconds=elapsed,
        )
        
        logger.info(f"[{stage.value}] {message} ({percent:.0f}%)")
        self._notify()
    
    def update_step(self, current: int, total: int, message: str) -> None:
        """Update progress within current stage."""
        if not self.current_status:
            return
        
        stage = self.current_status.stage
        percent = self._calculate_percent(stage, current, total)
        
        self.current_status = ProgressStatus(
            stage=stage,
            message=message,
            percent=percent,
            current_step=current,
            total_steps=total,
            elapsed_seconds=self._elapsed_seconds(),
        )
        
        logger.info(f"[{stage.value}] {message} ({current}/{total}) - {percent:.0f}%")
        self._notify()
    
    def complete(self, message: str = "Podcast generated successfully!") -> None:
        """Mark progress as completed."""
        self.current_status = ProgressStatus(
            stage=ProgressStage.COMPLETED,
            message=message,
            percent=100.0,
            elapsed_seconds=self._elapsed_seconds(),
        )
        logger.info(f"[completed] {message} (took {self._elapsed_seconds():.1f}s)")
        self._notify()
    
    def fail(self, error: str) -> None:
        """Mark progress as failed."""
        self.current_status = ProgressStatus(
            stage=ProgressStage.FAILED,
            message="Generation failed",
            percent=self.current_status.percent if self.current_status else 0,
            elapsed_seconds=self._elapsed_seconds(),
            error=error,
        )
        logger.error(f"[failed] {error}")
        self._notify()
    
    def _elapsed_seconds(self) -> float:
        if not self.start_time:
            return 0.0
        return (datetime.now() - self.start_time).total_seconds()
    
    def _calculate_percent(self, stage: ProgressStage, current_step: int, total_steps: int) -> float:
        """Calculate overall percentage based on stage and step within stage."""
        if stage == ProgressStage.COMPLETED:
            return 100.0
        if stage == ProgressStage.FAILED:
            return self.current_status.percent if self.current_status else 0
        
        # Calculate base percentage from completed stages
        base_percent = 0.0
        for s in self._stage_order:
            if s == stage:
                break
            base_percent += self._stage_weights.get(s, 0)
        
        # Add progress within current stage
        stage_weight = self._stage_weights.get(stage, 0)
        if total_steps > 0:
            step_progress = (current_step / total_steps) * stage_weight
        else:
            step_progress = 0
        
        return min(base_percent + step_progress, 99.9)
    
    def _notify(self) -> None:
        """Notify callback of progress update."""
        if self.on_progress and self.current_status:
            try:
                self.on_progress(self.current_status)
            except Exception as e:
                logger.warning(f"Progress callback error: {e}")


# Convenience function for Streamlit
def create_streamlit_progress_tracker(status_text, progress_bar):
    """
    Create a progress tracker that updates Streamlit components.
    
    Usage:
        status = st.empty()
        progress = st.progress(0)
        tracker = create_streamlit_progress_tracker(status, progress)
    """
    def update_streamlit(status: ProgressStatus):
        status_text.text(f"{status.message} ({status.percent:.0f}%)")
        progress_bar.progress(int(status.percent))
    
    return ProgressTracker(on_progress=update_streamlit)
