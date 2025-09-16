import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import numpy as np
import os
import threading
import time
from datetime import datetime, timedelta
import re

class VideoToASCIIConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Video to ASCII Converter")
        self.root.geometry("800x600")
        
        # ASCII characters from darkest to lightest
        self.ascii_chars = "@%#*+=-:. "
        
        # Variables
        self.video_path = tk.StringVar()
        self.srt_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.resolution = tk.IntVar(value=80)
        self.is_converting = False
        self.progress_var = tk.DoubleVar()
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Video file selection
        ttk.Label(main_frame, text="Select MP4 Video:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.video_path, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_video).grid(row=0, column=2)
        
        # SRT file selection
        ttk.Label(main_frame, text="Select SRT Subtitle (Optional):").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.srt_path, width=50).grid(row=1, column=1, padx=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_srt).grid(row=1, column=2)
        
        # Output path
        ttk.Label(main_frame, text="Output Python File:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.output_path, width=50).grid(row=2, column=1, padx=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_output).grid(row=2, column=2)
        
        # Resolution control
        ttk.Label(main_frame, text="ASCII Resolution (0-500):").grid(row=3, column=0, sticky=tk.W, pady=5)
        resolution_frame = ttk.Frame(main_frame)
        resolution_frame.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Scale(resolution_frame, from_=10, to=500, variable=self.resolution, orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(resolution_frame, textvariable=self.resolution).pack(side=tk.RIGHT)
        
        # Convert button
        self.convert_btn = ttk.Button(main_frame, text="Convert to ASCII", command=self.start_conversion)
        self.convert_btn.grid(row=4, column=0, columnspan=3, pady=20)
        
        # Progress bar
        ttk.Label(main_frame, text="Progress:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=5, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=5)
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Ready to convert")
        self.status_label.grid(row=6, column=0, columnspan=3, pady=10)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
    def browse_video(self):
        filename = filedialog.askopenfilename(
            title="Select MP4 Video",
            filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")]
        )
        if filename:
            self.video_path.set(filename)
            
    def browse_srt(self):
        filename = filedialog.askopenfilename(
            title="Select SRT Subtitle",
            filetypes=[("SRT files", "*.srt"), ("All files", "*.*")]
        )
        if filename:
            self.srt_path.set(filename)
            
    def browse_output(self):
        filename = filedialog.asksaveasfilename(
            title="Save ASCII Animation",
            defaultextension=".py",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )
        if filename:
            self.output_path.set(filename)
            
    def parse_srt(self, srt_path):
        """Parse SRT subtitle file"""
        subtitles = []
        if not os.path.exists(srt_path):
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
        
    def start_conversion(self):
        if self.is_converting:
            return
            
        if not self.video_path.get():
            messagebox.showerror("Error", "Please select a video file")
            return
            
        if not self.output_path.get():
            messagebox.showerror("Error", "Please specify output file path")
            return
            
        self.is_converting = True
        self.convert_btn.config(state='disabled')
        
        # Start conversion in separate thread
        thread = threading.Thread(target=self.convert_video)
        thread.daemon = True
        thread.start()
        
    def convert_video(self):
        try:
            self.status_label.config(text="Loading video...")
            
            # Open video
            cap = cv2.VideoCapture(self.video_path.get())
            if not cap.isOpened():
                raise Exception("Could not open video file")
                
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Parse subtitles if provided
            subtitles = []
            if self.srt_path.get():
                subtitles = self.parse_srt(self.srt_path.get())
                
            # Convert frames
            ascii_frames = []
            frame_count = 0
            
            self.status_label.config(text="Converting frames to ASCII...")
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                    
                # Convert frame to ASCII
                ascii_frame = self.frame_to_ascii(frame, self.resolution.get())
                
                # Add subtitle if applicable
                current_time = frame_count / fps
                subtitle_text = ""
                for start_time, end_time, text in subtitles:
                    if start_time <= current_time <= end_time:
                        subtitle_text = text
                        break
                        
                ascii_frames.append((ascii_frame, subtitle_text))
                frame_count += 1
                
                # Update progress
                progress = (frame_count / total_frames) * 80  # 80% for conversion
                self.progress_var.set(progress)
                
            cap.release()
            
            # Generate Python file
            self.status_label.config(text="Generating Python file...")
            self.generate_python_file(ascii_frames, fps)
            
            self.progress_var.set(100)
            self.status_label.config(text="Conversion completed!")
            messagebox.showinfo("Success", f"ASCII animation saved to {self.output_path.get()}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Conversion failed: {str(e)}")
            self.status_label.config(text="Conversion failed")
            
        finally:
            self.is_converting = False
            self.convert_btn.config(state='normal')
            
    def generate_python_file(self, ascii_frames, fps):
        """Generate standalone Python file with ASCII animation"""
        
        python_code = f'''#!/usr/bin/env python3
"""
ASCII Video Animation
Generated by Video to ASCII Converter
Original FPS: {fps}
Total Frames: {len(ascii_frames)}
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
        
        # Add frame data
        for i, (frame, subtitle) in enumerate(ascii_frames):
            frame_str = repr(frame)
            subtitle_str = repr(subtitle)
            python_code += f"    ({frame_str}, {subtitle_str}),\n"
            
            # Update progress
            progress = 80 + (i / len(ascii_frames)) * 20  # Remaining 20%
            self.progress_var.set(progress)
            
        python_code += ''']

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
            print(f"\\033[47m\\033[30m {line.ljust(40)} \\033[0m")

def play_animation():
    """Play the ASCII animation"""
    print("Starting ASCII Video Animation...")
    print(f"FPS: {FPS}, Total Frames: {len(FRAMES)}")
    print("Press Ctrl+C to stop\\n")
    
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
            
        print("\\n\\nAnimation completed!")
        
    except KeyboardInterrupt:
        print("\\n\\nAnimation stopped by user.")
    except Exception as e:
        print(f"\\n\\nError during playback: {e}")

if __name__ == "__main__":
    play_animation()
'''
        
        # Write to file
        with open(self.output_path.get(), 'w', encoding='utf-8') as f:
            f.write(python_code)

def main():
    root = tk.Tk()
    app = VideoToASCIIConverter(root)
    root.mainloop()

if __name__ == "__main__":
    main()