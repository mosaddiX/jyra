"""
Integration tests for FFmpeg functionality
"""

import os
import unittest
import subprocess
from pydub import AudioSegment

class TestFFmpeg(unittest.TestCase):
    """Test FFmpeg installation and functionality."""
    
    def setUp(self):
        """Set up the test environment."""
        # Set path to FFmpeg binaries
        self.ffmpeg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'jyra', 'bin')
        if os.path.exists(self.ffmpeg_path):
            os.environ["PATH"] = self.ffmpeg_path + os.pathsep + os.environ["PATH"]
    
    def test_ffmpeg_available(self):
        """Test that FFmpeg is available."""
        try:
            # Try to run ffmpeg -version
            result = subprocess.run(
                ["ffmpeg", "-version"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            self.assertEqual(result.returncode, 0, "FFmpeg command failed")
            self.assertIn("ffmpeg version", result.stdout, "FFmpeg version not found in output")
        except Exception as e:
            self.fail(f"Error running FFmpeg: {str(e)}")
    
    def test_pydub_with_ffmpeg(self):
        """Test that pydub can use FFmpeg."""
        try:
            # Create a simple silent audio segment
            silent_audio = AudioSegment.silent(duration=1000)  # 1 second of silence
            
            # Export to mp3 (requires FFmpeg)
            output_file = "test_audio.mp3"
            silent_audio.export(output_file, format="mp3")
            
            # Check if the file was created
            self.assertTrue(os.path.exists(output_file), f"Failed to create {output_file}")
            
            # Clean up
            os.remove(output_file)
        except Exception as e:
            self.fail(f"Error testing pydub with FFmpeg: {str(e)}")

if __name__ == '__main__':
    unittest.main()
