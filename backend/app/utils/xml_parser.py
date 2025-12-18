"""Ableton Live Set XML parsing utilities."""

import gzip
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class AbletonProjectParser:
    """Parser for Ableton Live Set (.als) files."""
    
    def __init__(self, als_path: str):
        self.als_path = Path(als_path)
        self.xml_root: Optional[ET.Element] = None
        self._parsed = False
    
    def parse(self) -> bool:
        """
        Parse the .als file (GZIP-compressed XML).
        
        Returns:
            True if parsing was successful, False otherwise.
        """
        try:
            with gzip.open(self.als_path, 'rb') as f:
                content = f.read()
            self.xml_root = ET.fromstring(content)
            self._parsed = True
            return True
        except gzip.BadGzipFile:
            logger.warning(f"Not a valid gzip file: {self.als_path}")
            # Try reading as plain XML (older Ableton versions)
            try:
                self.xml_root = ET.parse(self.als_path).getroot()
                self._parsed = True
                return True
            except Exception as e:
                logger.error(f"Failed to parse as XML: {e}")
                return False
        except Exception as e:
            logger.error(f"Failed to parse {self.als_path}: {e}")
            return False
    
    def get_external_file_references(self) -> List[str]:
        """
        Extract all external file references (samples, presets) from the project.
        
        Returns:
            List of absolute file paths referenced by the project.
        """
        if not self._parsed:
            return []
        
        external_refs = []
        
        # Look for SampleRef elements (audio samples)
        for sample_ref in self.xml_root.iter('SampleRef'):
            file_ref = sample_ref.find('.//FileRef')
            if file_ref is not None:
                path = self._extract_file_path(file_ref)
                if path:
                    external_refs.append(path)
        
        # Look for FileRef elements in general (VST presets, etc.)
        for file_ref in self.xml_root.iter('FileRef'):
            path = self._extract_file_path(file_ref)
            if path and path not in external_refs:
                external_refs.append(path)
        
        return external_refs
    
    def _extract_file_path(self, file_ref: ET.Element) -> Optional[str]:
        """Extract the file path from a FileRef element."""
        # Check for Path element (older format)
        path_elem = file_ref.find('Path')
        if path_elem is not None and path_elem.get('Value'):
            return path_elem.get('Value')
        
        # Check for RelativePath and SearchHint (newer format)
        relative_path = file_ref.find('.//RelativePath')
        if relative_path is not None:
            rel_path_value = relative_path.get('Value', '')
            if rel_path_value:
                return rel_path_value
        
        # Check SearchHint for absolute path
        search_hint = file_ref.find('.//SearchHint')
        if search_hint is not None:
            path_hint = search_hint.find('.//PathHint')
            if path_hint is not None and path_hint.get('Value'):
                return path_hint.get('Value')
        
        return None
    
    def get_track_count(self) -> int:
        """Get the number of tracks in the project."""
        if not self._parsed:
            return 0
        
        count = 0
        
        # Count AudioTrack, MidiTrack, ReturnTrack, GroupTrack
        for track_type in ['AudioTrack', 'MidiTrack', 'ReturnTrack', 'GroupTrack']:
            tracks = self.xml_root.findall(f'.//{track_type}')
            count += len(tracks)
        
        return count
    
    def get_used_plugins(self) -> List[str]:
        """Get list of VST/AU plugins used in the project."""
        if not self._parsed:
            return []
        
        plugins = set()
        
        # Look for PluginDevice elements
        for plugin in self.xml_root.iter('PluginDevice'):
            name_elem = plugin.find('.//PlugName')
            if name_elem is not None:
                value = name_elem.get('Value')
                if value:
                    plugins.add(value)
        
        # Look for AuPluginDevice elements (Audio Units)
        for plugin in self.xml_root.iter('AuPluginDevice'):
            name_elem = plugin.find('.//Name')
            if name_elem is not None:
                value = name_elem.get('Value')
                if value:
                    plugins.add(value)
        
        return list(plugins)
    
    def get_bpm(self) -> Optional[float]:
        """Extract BPM from the project file."""
        if not self._parsed:
            return None
        
        # Look for Tempo element
        tempo = self.xml_root.find('.//Tempo')
        if tempo is not None:
            manual = tempo.find('.//Manual')
            if manual is not None:
                try:
                    return float(manual.get('Value', 0))
                except ValueError:
                    pass
        
        return None
    
    def has_external_dependencies(self) -> bool:
        """
        Check if the project has external file dependencies.
        
        This is used to validate if a project is "self-contained"
        (has used "Collect All and Save").
        """
        refs = self.get_external_file_references()
        project_dir = self.als_path.parent
        
        for ref in refs:
            ref_path = Path(ref)
            # Check if the reference is outside the project folder
            try:
                ref_path.relative_to(project_dir)
            except ValueError:
                # Path is not relative to project dir - it's external
                return True
        
        return False
    
    def get_project_info(self) -> Dict[str, Any]:
        """Get a summary of project information."""
        if not self._parsed:
            self.parse()
        
        return {
            'track_count': self.get_track_count(),
            'plugins': self.get_used_plugins(),
            'bpm': self.get_bpm(),
            'external_refs_count': len(self.get_external_file_references()),
            'has_external_dependencies': self.has_external_dependencies(),
        }


def analyze_dependency_health(xml_root: ET.Element, project_root_path: str) -> Dict[str, Any]:
    """
    Analyze dependency health of an Ableton Live project.
    
    Checks whether a project is "Self-Contained" (has performed "Collect All and Save")
    or if it references "External/Unsafe" files that could go missing.
    
    Args:
        xml_root: The parsed XML root element of the .als file
        project_root_path: Absolute path to the project folder
        
    Returns:
        Dictionary with hygiene status report:
        {
            "hygiene_status": "Secure" | "At Risk",
            "total_files": int,
            "collected_files": int,
            "external_files": int,
            "library_files": int,
            "missing_files_list": List[str]
        }
    """
    project_root = Path(project_root_path).resolve()
    collected_files = []
    external_files = []
    library_files = []
    missing_files = []
    
    # Normalize project root path for comparison (handle OS differences)
    project_root_normalized = str(project_root).replace('\\', '/')
    if not project_root_normalized.endswith('/'):
        project_root_normalized += '/'
    
    # Iterate through every FileRef element in the XML
    for file_ref in xml_root.iter('FileRef'):
        # Extract the absolute path from the Path child element
        path_elem = file_ref.find('Path')
        if path_elem is None:
            # Try alternative path extraction methods
            path = _extract_file_path_from_element(file_ref)
        else:
            path = path_elem.get('Value')
        
        if not path:
            # Skip if path is empty or relative (can't determine safety)
            continue
        
        # Normalize the path for OS-agnostic comparison
        path_normalized = path.replace('\\', '/')
        path_obj = Path(path)
        
        # Check if file exists (for missing files detection)
        file_exists = path_obj.exists()
        
        # Condition C: Check if it's a Library file (Ableton Core Library or Packs)
        if _is_library_path(path_normalized):
            library_files.append(path)
            continue
        
        # Condition A: Check if path starts with project_root_path (Collected/Safe)
        if _is_path_within_project(path_normalized, project_root_normalized):
            collected_files.append(path)
        else:
            # Condition B: Path is outside project (External/Risk)
            external_files.append(path)
            if not file_exists:
                missing_files.append(path)
    
    # Determine hygiene status
    hygiene_status = "Secure" if len(external_files) == 0 else "At Risk"
    
    return {
        "hygiene_status": hygiene_status,
        "total_files": len(collected_files) + len(external_files) + len(library_files),
        "collected_files": len(collected_files),
        "external_files": len(external_files),
        "library_files": len(library_files),
        "missing_files_list": missing_files
    }


def _extract_file_path_from_element(file_ref: ET.Element) -> Optional[str]:
    """Extract file path from a FileRef element using multiple strategies."""
    # Check for Path element (older format)
    path_elem = file_ref.find('Path')
    if path_elem is not None and path_elem.get('Value'):
        return path_elem.get('Value')
    
    # Check for RelativePath and SearchHint (newer format)
    relative_path = file_ref.find('.//RelativePath')
    if relative_path is not None:
        rel_path_value = relative_path.get('Value', '')
        if rel_path_value:
            return rel_path_value
    
    # Check SearchHint for absolute path
    search_hint = file_ref.find('.//SearchHint')
    if search_hint is not None:
        path_hint = search_hint.find('.//PathHint')
        if path_hint is not None and path_hint.get('Value'):
            return path_hint.get('Value')
    
    return None


def _is_library_path(path: str) -> bool:
    """
    Check if a path references Ableton Core Library or Factory Packs.
    
    Args:
        path: Normalized file path (forward slashes)
        
    Returns:
        True if the path is a library path
    """
    library_indicators = [
        '/App-Resources/',
        '/Factory Packs/',
        '/Core Library/',
        '/User Library/',
        '/Packs/',
    ]
    
    path_lower = path.lower()
    return any(indicator.lower() in path_lower for indicator in library_indicators)


def _is_path_within_project(file_path: str, project_root: str) -> bool:
    """
    Check if a file path is within the project root directory.
    
    Args:
        file_path: Normalized file path (forward slashes)
        project_root: Normalized project root path (forward slashes, ends with /)
        
    Returns:
        True if the file path starts with the project root path
    """
    # Ensure both paths are normalized and comparable
    file_path_normalized = file_path.replace('\\', '/')
    project_root_normalized = project_root.replace('\\', '/')
    
    if not project_root_normalized.endswith('/'):
        project_root_normalized += '/'
    
    # Check if file path starts with project root
    return file_path_normalized.startswith(project_root_normalized)


def validate_project_dependencies(als_path: str) -> Dict[str, Any]:
    """
    Validate that a project is self-contained for migration.
    
    Args:
        als_path: Path to the .als file
        
    Returns:
        Dictionary with validation results
    """
    parser = AbletonProjectParser(als_path)
    
    if not parser.parse():
        return {
            'valid': False,
            'error': 'Failed to parse project file',
            'external_refs': [],
        }
    
    external_refs = parser.get_external_file_references()
    project_dir = Path(als_path).parent
    
    # Find references that are outside the project folder
    external_files = []
    for ref in external_refs:
        ref_path = Path(ref)
        try:
            ref_path.relative_to(project_dir)
        except ValueError:
            # Check if the file actually exists
            if ref_path.exists():
                external_files.append(str(ref_path))
    
    return {
        'valid': len(external_files) == 0,
        'external_refs': external_files,
        'total_refs': len(external_refs),
    }

