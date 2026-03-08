"""Tests for the progress module."""

import pytest
from progress import ProgressTracker, ProgressStage, ProgressStatus


class TestProgressStatus:
    """Tests for ProgressStatus dataclass."""
    
    def test_status_creation(self):
        status = ProgressStatus(
            stage=ProgressStage.GENERATING_AUDIO,
            message="Testing",
            percent=50.0
        )
        assert status.stage == ProgressStage.GENERATING_AUDIO
        assert status.message == "Testing"
        assert status.percent == 50.0
    
    def test_status_to_dict(self):
        status = ProgressStatus(
            stage=ProgressStage.COMPLETED,
            message="Done",
            percent=100.0,
            current_step=5,
            total_steps=5
        )
        d = status.to_dict()
        assert d["stage"] == "completed"
        assert d["message"] == "Done"
        assert d["percent"] == 100.0
        assert d["current_step"] == 5


class TestProgressTracker:
    """Tests for ProgressTracker class."""
    
    def test_tracker_start(self):
        tracker = ProgressTracker()
        tracker.start()
        assert tracker.current_status is not None
        assert tracker.current_status.stage == ProgressStage.INITIALIZING
    
    def test_tracker_update_stage(self):
        tracker = ProgressTracker()
        tracker.start()
        tracker.update(ProgressStage.GENERATING_SCRIPT, "Generating...")
        assert tracker.current_status.stage == ProgressStage.GENERATING_SCRIPT
        assert tracker.current_status.message == "Generating..."
    
    def test_tracker_update_step(self):
        tracker = ProgressTracker()
        tracker.start()
        tracker.update(ProgressStage.GENERATING_AUDIO, "Audio")
        tracker.update_step(3, 10, "Segment 3 of 10")
        assert tracker.current_status.current_step == 3
        assert tracker.current_status.total_steps == 10
    
    def test_tracker_complete(self):
        tracker = ProgressTracker()
        tracker.start()
        tracker.complete()
        assert tracker.current_status.stage == ProgressStage.COMPLETED
        assert tracker.current_status.percent == 100.0
    
    def test_tracker_fail(self):
        tracker = ProgressTracker()
        tracker.start()
        tracker.update(ProgressStage.GENERATING_AUDIO, "Working")
        tracker.fail("Something went wrong")
        assert tracker.current_status.stage == ProgressStage.FAILED
        assert tracker.current_status.error == "Something went wrong"
    
    def test_tracker_callback(self):
        updates = []
        def callback(status):
            updates.append(status)
        
        tracker = ProgressTracker(on_progress=callback)
        tracker.start()
        tracker.update(ProgressStage.GENERATING_SCRIPT, "Script")
        tracker.complete()
        
        assert len(updates) == 3
        assert updates[0].stage == ProgressStage.INITIALIZING
        assert updates[1].stage == ProgressStage.GENERATING_SCRIPT
        assert updates[2].stage == ProgressStage.COMPLETED
    
    def test_percent_increases_with_stages(self):
        tracker = ProgressTracker()
        tracker.start()
        
        percentages = [tracker.current_status.percent]
        
        for stage in [ProgressStage.EXTRACTING_CONTENT, 
                      ProgressStage.GENERATING_SCRIPT,
                      ProgressStage.GENERATING_AUDIO]:
            tracker.update(stage, "Testing")
            percentages.append(tracker.current_status.percent)
        
        # Each stage should increase percentage
        for i in range(1, len(percentages)):
            assert percentages[i] >= percentages[i-1]
    
    def test_elapsed_time_tracked(self):
        import time
        tracker = ProgressTracker()
        tracker.start()
        time.sleep(0.1)  # Small delay
        tracker.update(ProgressStage.GENERATING_SCRIPT, "Test")
        assert tracker.current_status.elapsed_seconds >= 0.1
