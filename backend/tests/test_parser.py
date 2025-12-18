"""Tests for the Ableton XML parser."""

import pytest
import tempfile
import gzip
from pathlib import Path

from app.utils.xml_parser import AbletonProjectParser, validate_project_dependencies


# Sample minimal Ableton XML content
SAMPLE_ALS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Ableton MajorVersion="5" MinorVersion="11.0" SchemaChangeCount="3">
    <LiveSet>
        <Tempo>
            <Manual Value="128.0"/>
        </Tempo>
        <Tracks>
            <AudioTrack Id="0">
                <Name Value="Track 1"/>
            </AudioTrack>
            <MidiTrack Id="1">
                <Name Value="Track 2"/>
            </MidiTrack>
        </Tracks>
    </LiveSet>
</Ableton>
"""

SAMPLE_ALS_WITH_REFS = """<?xml version="1.0" encoding="UTF-8"?>
<Ableton MajorVersion="5" MinorVersion="11.0">
    <LiveSet>
        <Tracks>
            <AudioTrack Id="0">
                <DeviceChain>
                    <MainSequencer>
                        <Sample>
                            <SampleRef>
                                <FileRef>
                                    <Path Value="/Users/test/external_sample.wav"/>
                                </FileRef>
                            </SampleRef>
                        </Sample>
                    </MainSequencer>
                </DeviceChain>
            </AudioTrack>
        </Tracks>
    </LiveSet>
</Ableton>
"""


def create_test_als(content: str, tmpdir: Path, filename: str = "test.als") -> Path:
    """Create a test .als file with gzipped XML content."""
    als_path = tmpdir / filename
    with gzip.open(als_path, 'wt', encoding='utf-8') as f:
        f.write(content)
    return als_path


class TestAbletonProjectParser:
    """Tests for AbletonProjectParser class."""
    
    def test_parse_valid_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            als_path = create_test_als(SAMPLE_ALS_XML, Path(tmpdir))
            
            parser = AbletonProjectParser(str(als_path))
            result = parser.parse()
            
            assert result is True
    
    def test_parse_invalid_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a non-gzip file
            als_path = Path(tmpdir) / "invalid.als"
            als_path.write_text("not valid content")
            
            parser = AbletonProjectParser(str(als_path))
            result = parser.parse()
            
            # Should fail gracefully
            assert result is False
    
    def test_get_bpm(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            als_path = create_test_als(SAMPLE_ALS_XML, Path(tmpdir))
            
            parser = AbletonProjectParser(str(als_path))
            parser.parse()
            bpm = parser.get_bpm()
            
            assert bpm == 128.0
    
    def test_get_track_count(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            als_path = create_test_als(SAMPLE_ALS_XML, Path(tmpdir))
            
            parser = AbletonProjectParser(str(als_path))
            parser.parse()
            count = parser.get_track_count()
            
            assert count == 2  # 1 audio + 1 midi
    
    def test_get_project_info(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            als_path = create_test_als(SAMPLE_ALS_XML, Path(tmpdir))
            
            parser = AbletonProjectParser(str(als_path))
            info = parser.get_project_info()
            
            assert info["track_count"] == 2
            assert info["bpm"] == 128.0
            assert info["external_refs_count"] == 0


class TestExternalReferences:
    """Tests for external file reference detection."""
    
    def test_detect_external_refs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            als_path = create_test_als(SAMPLE_ALS_WITH_REFS, Path(tmpdir))
            
            parser = AbletonProjectParser(str(als_path))
            parser.parse()
            refs = parser.get_external_file_references()
            
            assert len(refs) > 0
            assert "/Users/test/external_sample.wav" in refs
    
    def test_has_external_dependencies(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            als_path = create_test_als(SAMPLE_ALS_WITH_REFS, Path(tmpdir))
            
            parser = AbletonProjectParser(str(als_path))
            parser.parse()
            has_deps = parser.has_external_dependencies()
            
            assert has_deps is True
    
    def test_no_external_dependencies(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            als_path = create_test_als(SAMPLE_ALS_XML, Path(tmpdir))
            
            parser = AbletonProjectParser(str(als_path))
            parser.parse()
            has_deps = parser.has_external_dependencies()
            
            assert has_deps is False


class TestDependencyValidation:
    """Tests for the validate_project_dependencies function."""
    
    def test_validate_self_contained(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            als_path = create_test_als(SAMPLE_ALS_XML, Path(tmpdir))
            
            result = validate_project_dependencies(str(als_path))
            
            assert result["valid"] is True
            assert len(result["external_refs"]) == 0
    
    def test_validate_with_external(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            als_path = create_test_als(SAMPLE_ALS_WITH_REFS, Path(tmpdir))
            
            result = validate_project_dependencies(str(als_path))
            
            # File doesn't exist, so it won't show in external_refs
            # (only existing external files are flagged)
            assert "external_refs" in result
    
    def test_validate_nonexistent_file(self):
        result = validate_project_dependencies("/nonexistent/path.als")
        
        assert result["valid"] is False
        assert "error" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

