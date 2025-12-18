"""Tests for the scanner service."""

import pytest
import tempfile
import os
from pathlib import Path

from app.services.scanner import (
    Scanner,
    ScannedProject,
    cluster_projects,
    update_cluster_scores,
)
from app.services.scorer import (
    calculate_signal_score,
    extract_keywords_from_filename,
    ScoringFactors,
)


class TestFilenameExtraction:
    """Tests for filename parsing."""
    
    def test_extract_key_major(self):
        scanner = Scanner()
        assert scanner._extract_key("Track_C_140") == "C"
        assert scanner._extract_key("Song_Am_Beat") == "Am"
        assert scanner._extract_key("Dm_Track") == "Dm"
    
    def test_extract_key_with_modifier(self):
        scanner = Scanner()
        assert scanner._extract_key("Track_Cm_140") == "Cm"
        assert scanner._extract_key("Track_C_minor_beat") == "Cm"
        assert scanner._extract_key("Track_C_min") == "Cm"
    
    def test_extract_key_sharp_flat(self):
        scanner = Scanner()
        assert scanner._extract_key("Track_Bb_140") == "Bb"
        assert scanner._extract_key("Track_F#m") == "F#m"
    
    def test_extract_bpm(self):
        scanner = Scanner()
        assert scanner._extract_bpm("Track_140_bpm") == 140
        assert scanner._extract_bpm("128bpm_house") == 128
        assert scanner._extract_bpm("Song_174") == 174
    
    def test_extract_bpm_invalid(self):
        scanner = Scanner()
        # Out of reasonable range
        assert scanner._extract_bpm("Track_10_test") is None
        assert scanner._extract_bpm("Track_300_fast") is None


class TestKeywordExtraction:
    """Tests for keyword extraction."""
    
    def test_diamond_keywords(self):
        diamond, gold = extract_keywords_from_filename("Final_RENDER_Track")
        assert "FINAL" in diamond
        assert "RENDER" in diamond
    
    def test_gold_keywords(self):
        diamond, gold = extract_keywords_from_filename("FIRE_track_GOOD DRUMS")
        assert "FIRE" in gold
        assert "GOOD DRUMS" in gold
    
    def test_case_insensitive(self):
        diamond, gold = extract_keywords_from_filename("final_render_fire")
        assert "FINAL" in diamond
        assert "RENDER" in diamond
        assert "FIRE" in gold


class TestSignalScoring:
    """Tests for signal scoring algorithm."""
    
    def test_base_score(self):
        factors = ScoringFactors(
            diamond_keywords=[],
            gold_keywords=[],
            time_spent_days=None,
            backup_count=0,
            cluster_size=1
        )
        score = calculate_signal_score(factors)
        assert score == 20  # Base score
    
    def test_diamond_bonus(self):
        factors = ScoringFactors(
            diamond_keywords=["FINAL"],
            gold_keywords=[],
            time_spent_days=None,
            backup_count=0,
            cluster_size=1
        )
        score = calculate_signal_score(factors)
        assert score == 50  # 20 base + 30 diamond
    
    def test_gold_bonus(self):
        factors = ScoringFactors(
            diamond_keywords=[],
            gold_keywords=["FIRE"],
            time_spent_days=None,
            backup_count=0,
            cluster_size=1
        )
        score = calculate_signal_score(factors)
        assert score == 35  # 20 base + 15 gold
    
    def test_time_spent_bonus(self):
        factors = ScoringFactors(
            diamond_keywords=[],
            gold_keywords=[],
            time_spent_days=10,
            backup_count=0,
            cluster_size=1
        )
        score = calculate_signal_score(factors)
        assert score == 40  # 20 base + (10 * 2) time
    
    def test_time_spent_cap(self):
        factors = ScoringFactors(
            diamond_keywords=[],
            gold_keywords=[],
            time_spent_days=100,  # Very high
            backup_count=0,
            cluster_size=1
        )
        score = calculate_signal_score(factors)
        assert score == 60  # 20 base + 40 cap
    
    def test_backup_bonus(self):
        factors = ScoringFactors(
            diamond_keywords=[],
            gold_keywords=[],
            time_spent_days=None,
            backup_count=10,  # Above threshold
            cluster_size=1
        )
        score = calculate_signal_score(factors)
        assert score == 30  # 20 base + 10 backup bonus
    
    def test_cluster_bonus(self):
        factors = ScoringFactors(
            diamond_keywords=[],
            gold_keywords=[],
            time_spent_days=None,
            backup_count=0,
            cluster_size=3
        )
        score = calculate_signal_score(factors)
        assert score == 35  # 20 base + (3 * 5) cluster
    
    def test_max_score(self):
        factors = ScoringFactors(
            diamond_keywords=["FINAL", "RENDER"],
            gold_keywords=["FIRE"],
            time_spent_days=100,
            backup_count=20,
            cluster_size=10
        )
        score = calculate_signal_score(factors)
        assert score == 100  # Capped at max


class TestClusterGeneration:
    """Tests for project clustering."""
    
    def test_cluster_id_generation(self):
        scanner = Scanner()
        
        # Version numbers should be stripped
        assert scanner._generate_cluster_id("Track_v1") == "track"
        assert scanner._generate_cluster_id("Track_v2") == "track"
        
        # FINAL should be stripped
        assert scanner._generate_cluster_id("Track_FINAL") == "track"
        
        # Mix variations should be stripped
        assert scanner._generate_cluster_id("Track_mix1") == "track"
    
    def test_cluster_grouping(self):
        projects = [
            ScannedProject(
                project_path="/test/Track_v1.als",
                project_name="Track_v1",
                cluster_id="track"
            ),
            ScannedProject(
                project_path="/test/Track_v2.als",
                project_name="Track_v2",
                cluster_id="track"
            ),
            ScannedProject(
                project_path="/test/Other.als",
                project_name="Other",
                cluster_id="other"
            ),
        ]
        
        clusters = cluster_projects(projects)
        
        assert "track" in clusters
        assert len(clusters["track"]) == 2
        assert "other" in clusters
        assert len(clusters["other"]) == 1


class TestBackupAnalysis:
    """Tests for backup folder analysis."""
    
    def test_no_backup_folder(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = Scanner()
            result = scanner._analyze_backup_folder(Path(tmpdir))
            
            assert result["backup_count"] == 0
            assert result["time_spent_days"] is None
    
    def test_with_backups(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create backup folder with files
            backup_dir = Path(tmpdir) / "Backup"
            backup_dir.mkdir()
            
            for i in range(5):
                (backup_dir / f"backup_{i}.als").touch()
            
            scanner = Scanner()
            result = scanner._analyze_backup_folder(Path(tmpdir))
            
            assert result["backup_count"] == 5


class TestAudioPreview:
    """Tests for audio preview detection."""
    
    def test_no_preview(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = Scanner()
            result = scanner._find_audio_preview(Path(tmpdir))
            assert result is None
    
    def test_wav_preview(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            wav_file = Path(tmpdir) / "export.wav"
            wav_file.touch()
            
            scanner = Scanner()
            result = scanner._find_audio_preview(Path(tmpdir))
            assert result == str(wav_file)
    
    def test_prefer_render_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create multiple files
            (Path(tmpdir) / "random.wav").touch()
            render_file = Path(tmpdir) / "render.wav"
            render_file.touch()
            
            scanner = Scanner()
            result = scanner._find_audio_preview(Path(tmpdir))
            
            # Should prefer the render file
            assert "render" in result.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

