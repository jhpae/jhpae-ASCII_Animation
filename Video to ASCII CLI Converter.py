#!/usr/bin/env python3
"""
Video to ASCII CLI Converter
A command-line tool to convert MP4 videos to ASCII animations with subtitle support.

Usage:
    python video_to_ascii_cli.py <video_file> <output_file> [options]

Examples:
    python video_to_ascii_cli.py video.mp4 animation.py
    python video_to_ascii_cli.py video.mp4 animation.py --resolution 100
    python video_to_ascii_cli.py video.mp4 animation.py --subtitles subtitles.srt --resolution 150
    python video_to_ascii_cli.py --help

Requirements:
    - opencv-python (pip install opencv-python)
    - numpy (pip install numpy)

Features:
    - Converts MP4 videos to ASCII animations
    - Full RGB color support for each ASCII character
    - Subtitle support with .srt files (positioned at bottom left)
    - Adjustable resolution (10-500 characters)
    - Maintains original frame rate
    - Generates standalone Python file
    - No file size limits
"""

import argparse
import cv2
import numpy as np
import os
import sys
import time
import re
from datetime import datetime, timedelta

class VideoToASCIIConverter:
    def __init__(self):
        # ASCII characters from darkest to lightest
        self.ascii_chars = "@%#*+=-:. "
        
    def parse_srt(self, srt_path):
        """Parse SRT subtitle file"""
        subtitles = []
        if not os.path.exists(srt_path):
            print(f"Warning: SRT file not found: {srt_path}")
            return subtitles
            
        try:
            with open(srt_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Split by double newlines to get subtitle blocks
            blocks = re.split(r'\n\s*\n', content.strip())
            
            for block in blocks:
                lines = block.strip().split('\n')
                if len(lines) >= 3:
                    # Parse time range
                    time_line = lines[1]
                    time_match = re.match(r'(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2}):(\d{2}):(\d{2}),(\d{3})', time_line)
                    if time_match:
                        start_h, start_m, start_s, start_ms = map(int, time_match.groups()[:4])
                        end_h, end_m, end_s, end_ms = map(int, time_match.groups()[4:])
                        
                        start_time = start_h * 3600 + start_m * 60 + start_s + start_ms / 1000
                        end_time = end_h * 3600 + end_m * 60 + end_s + end_ms / 1000
                        
                        # Join text lines
                        text = ' '.join(lines[2:])
                        subtitles.append((start_time, end_time, text))
                        
            print(f"Loaded {len(subtitles)} subtitles from {srt_path}")
                        
        except Exception as e:
            print(f"Error parsing SRT: {e}")
            
        return subtitles
        
    def pixel_to_ascii(self, pixel_value):
        """Convert pixel brightness to ASCII character"""
        return self.ascii_chars[pixel_value * len(self.ascii_chars) // 256]
        
    def rgb_to_ansi(self, r, g, b):
        """Convert RGB to ANSI color code"""
        return f"\033[38;2;{r};{g};{b}m"
        
    def frame_to_ascii(self, frame, width):
        """Convert frame to ASCII with RGB colors"""
        height, original_width = frame.shape[:2]
        aspect_ratio = height / original_width
        new_height = int(width * aspect_ratio * 0.55)  # Adjust for character aspect ratio
        
        # Resize frame
        resized = cv2.resize(frame, (width, new_height))
        
        ascii_frame = []
        for row in resized:
            ascii_row = ""
            for pixel in row:
                b, g, r = pixel  # OpenCV uses BGR
                brightness = int(0.299 * r + 0.587 * g + 0.114 * b)
                ascii_char = self.pixel_to_ascii(brightness)
                color_code = self.rgb_to_ansi(r, g, b)
                ascii_row += f"{color_code}{ascii_char}"
            ascii_frame.append(ascii_row + "\033[0m")  # Reset color at end of line
            
        return ascii_frame
        
    def show_progress(self, current, total, prefix="Progress"):
        """Display progress bar"""
        percent = (current / total) * 100
        bar_length = 50
        filled_length = int(bar_length * current // total)
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        print(f'\r{prefix}: |{bar}| {percent:.1f}% ({current}/{total})', end='', flush=True)
        
    def convert_video(self, video_path, output_path, srt_path=None, resolution=80):
        """Convert video to ASCII animation"""
        
        print(f"Converting video: {video_path}")
        print(f"Output file: {output_path}")
        print(f"Resolution: {resolution} characters")
        if srt_path:
            print(f"Subtitles: {srt_path}")
        print("-" * 50)
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise Exception(f"Could not open video file: {video_path}")
            
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        print(f"Video info: {total_frames} frames, {fps:.2f} FPS, {duration:.2f}s duration")
        
        # Parse subtitles if provided
        subtitles = []
        if srt_path:
            subtitles = self.parse_srt(srt_path)
            
        # Convert frames
        ascii_frames = []
        frame_count = 0
        
        print("Converting frames to ASCII...")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Convert frame to ASCII
            ascii_frame = self.frame_to_ascii(frame, resolution)
            
            # Add subtitle if applicable
            current_time = frame_count / fps
            subtitle_text = ""
            for start_time, end_time, text in subtitles:
                if start_time <= current_time <= end_time:
                    subtitle_text = text
                    break
                    
            ascii_frames.append((ascii_frame, subtitle_text))
            frame_count += 1
            
            # Show progress
            self.show_progress(frame_count, total_frames, "Converting")
            
        cap.release()
        print("\nFrame conversion completed!")
        
        # Generate Python file
        print("Generating Python animation file...")
        self.generate_python_file(ascii_frames, fps, output_path)
        
        print(f"\n✅ ASCII animation saved to: {output_path}")
        print(f"📁 File size: {os.path.getsize(output_path) / (1024*1024):.2f} MB")
        print(f"🎬 Total frames: {len(ascii_frames)}")
        print(f"⏱️  Duration: {duration:.2f} seconds")
        print(f"\nTo play the animation, run: python {output_path}")
        
    def generate_python_file(self, ascii_frames, fps, output_path):
        """Generate standalone Python file with ASCII animation"""
        
        python_code = f'''#!/usr/bin/env python3
"""
ASCII Video Animation
Generated by Video to ASCII CLI Converter
Original FPS: {fps}
Total Frames: {len(ascii_frames)}
Duration: {len(ascii_frames)/fps:.2f} seconds

Usage: python {os.path.basename(output_path)}
Controls: Press Ctrl+C to stop the animation
"""

import time
import os
import sys

# Animation data
FPS = {fps}
FRAME_DELAY = 1.0 / FPS

# ASCII frames data (frame, subtitle)
FRAMES = [
'''
        
        # Add frame data with progress
        total_frames = len(ascii_frames)
        for i, (frame, subtitle) in enumerate(ascii_frames):
            frame_str = repr(frame)
            subtitle_str = repr(subtitle)
            python_code += f"    ({frame_str}, {subtitle_str}),\n"
            
            # Show progress
            if i % 100 == 0 or i == total_frames - 1:
                self.show_progress(i + 1, total_frames, "Writing")
            
        python_code += f''']

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_frame(frame_data, subtitle):
    """Display a single frame with subtitle"""
    clear_screen()
    
    # Display ASCII frame
    for line in frame_data:
        print(line)
    
    # Display subtitle with white background if present
    if subtitle:
        # Move cursor to bottom left area
        terminal_width = os.get_terminal_size().columns if hasattr(os, 'get_terminal_size') else 80
        subtitle_lines = [subtitle[i:i+40] for i in range(0, len(subtitle), 40)]
        
        print("\\n" * 2)  # Add some space
        for line in subtitle_lines:
            # White background, black text - positioned at bottom left
            print(f"\\033[47m\\033[30m {{line.ljust(40)}} \\033[0m")

def play_animation():
    """Play the ASCII animation"""
    print("🎬 ASCII Video Animation Player")
    print(f"📊 FPS: {{FPS}}, Total Frames: {{len(FRAMES)}}")
    print(f"⏱️  Duration: {{len(FRAMES)/FPS:.2f}} seconds")
    print("🎮 Press Ctrl+C to stop\\n")
    
    try:
        start_time = time.time()
        
        for frame_num, (frame_data, subtitle) in enumerate(FRAMES):
            # Calculate when this frame should be displayed
            target_time = start_time + (frame_num * FRAME_DELAY)
            current_time = time.time()
            
            # Wait if we're ahead of schedule
            if current_time < target_time:
                time.sleep(target_time - current_time)
            
            # Display the frame
            display_frame(frame_data, subtitle)
            
        print("\\n\\n🎉 Animation completed!")
        
    except KeyboardInterrupt:
        print("\\n\\n⏹️  Animation stopped by user.")
    except Exception as e:
        print(f"\\n\\n❌ Error during playback: {{e}}")

if __name__ == "__main__":
    play_animation()
'''
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(python_code)
            
        # Make file executable on Unix systems
        if os.name != 'nt':
            os.chmod(output_path, 0o755)

def print_help():
    """Print detailed help information"""
    help_text = """
🎬 Video to ASCII CLI Converter

DESCRIPTION:
    Convert MP4 videos to colorful ASCII animations with subtitle support.
    Generates a standalone Python file that can play the animation.

USAGE:
    python video_to_ascii_cli.py <video_file> <output_file> [options]

ARGUMENTS:
    video_file      Path to the input MP4 video file
    output_file     Path for the output Python animation file

OPTIONS:
    -s, --subtitles FILE    SRT subtitle file (optional)
    -r, --resolution NUM    ASCII resolution 10-500 characters (default: 80)
    -h, --help             Show this help message

EXAMPLES:
    # Basic conversion
    python video_to_ascii_cli.py video.mp4 animation.py
    
    # With custom resolution
    python video_to_ascii_cli.py video.mp4 animation.py --resolution 120
    
    # With subtitles
    python video_to_ascii_cli.py video.mp4 animation.py --subtitles subs.srt
    
    # Full featured
    python video_to_ascii_cli.py video.mp4 animation.py -s subs.srt -r 150

FEATURES:
    ✅ Full RGB color support for each ASCII character
    ✅ Subtitle synchronization with .srt files
    ✅ Adjustable resolution (10-500 characters)
    ✅ Maintains original frame rate
    ✅ No file size limits
    ✅ Generates standalone executable Python file

REQUIREMENTS:
    pip install opencv-python numpy

OUTPUT:
    The generated Python file is completely self-contained and can be
    run independently to play the ASCII animation:
    
    python your_animation.py

CONTROLS:
    Press Ctrl+C to stop the animation during playback.

NOTES:
    - Larger resolutions create more detailed but slower animations
    - Subtitles appear at the bottom left with white background
    - The output file size depends on video length and resolution
    - Terminal with color support recommended for best experience
"""
    print(help_text)

def main():
    """Main CLI function"""
    
    # Print banner
    print("🎬 Video to ASCII CLI Converter v1.0")
    print("=" * 50)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Convert MP4 videos to ASCII animations",
        add_help=False  # We'll handle help ourselves
    )
    
    parser.add_argument('video_file', nargs='?', help='Input MP4 video file')
    parser.add_argument('output_file', nargs='?', help='Output Python animation file')
    parser.add_argument('-s', '--subtitles', help='SRT subtitle file')
    parser.add_argument('-r', '--resolution', type=int, default=80, 
                       help='ASCII resolution (10-500, default: 80)')
    parser.add_argument('-h', '--help', action='store_true', help='Show help')
    
    args = parser.parse_args()
    
    # Handle help
    if args.help or not args.video_file or not args.output_file:
        print_help()
        return
    
    # Validate arguments
    if not os.path.exists(args.video_file):
        print(f"❌ Error: Video file not found: {args.video_file}")
        return
        
    if not args.video_file.lower().endswith('.mp4'):
        print(f"⚠️  Warning: File doesn't have .mp4 extension: {args.video_file}")
        
    if args.resolution < 10 or args.resolution > 500:
        print(f"❌ Error: Resolution must be between 10 and 500 (got: {args.resolution})")
        return
        
    if args.subtitles and not os.path.exists(args.subtitles):
        print(f"❌ Error: Subtitle file not found: {args.subtitles}")
        return
        
    # Check if output file already exists
    if os.path.exists(args.output_file):
        response = input(f"⚠️  Output file exists: {args.output_file}. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("❌ Operation cancelled.")
            return
    
    try:
        # Create converter and run conversion
        converter = VideoToASCIIConverter()
        converter.convert_video(
            args.video_file, 
            args.output_file, 
            args.subtitles, 
            args.resolution
        )
        
    except KeyboardInterrupt:
        print("\n❌ Conversion cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()