import os
import sys
import subprocess
import pathlib
import logging
import djjtb.utils as djj

os.system('clear')

def clean_path(path_str):
    return path_str.strip().strip('\'"')

def return_to_djjtb():
    """Switch back to DJJTB tab (Command+1)"""
    subprocess.run([
        "osascript", "-e",
        'tell application "Terminal" to tell application "System Events" to keystroke "1" using command down'
    ])

def is_valid_gif(filename):
    return filename.lower().endswith('.gif')

def is_valid_video(filename):
    return filename.lower().endswith(('.mp4', '.mov', '.webm', '.mkv', '.avi'))

def get_conversion_mode():
    """Get conversion mode from user"""
    return djj.prompt_choice(
        "Conversion mode:\n1. GIF to Video\n2. Video to GIF\n",
        ['1', '2'],
        default='1'
    )

def get_gif_quality():
    """Get GIF quality settings"""
    quality = djj.prompt_choice(
        "GIF Quality:\n1. High (15fps, 720p)\n2. Medium (10fps, 480p)\n3. Low (8fps, 360p)\n",
        ['1', '2', '3'],
        default='2'
    )
    
    quality_settings = {
        '1': {'fps': 15, 'scale': '720:-1'},
        '2': {'fps': 10, 'scale': '480:-1'},
        '3': {'fps': 8, 'scale': '360:-1'}
    }
    
    return quality_settings[quality]

def get_video_codec():
    """Get video codec preference"""
    codec = djj.prompt_choice(
        "Video codec:\n1. H.264 (MP4)\n2. WebM\n",
        ['1', '2'],
        default='1'
    )
    
    codec_settings = {
        '1': {'codec': 'libx264', 'ext': 'mp4'},
        '2': {'codec': 'libvpx', 'ext': 'webm'}
    }
    
    return codec_settings[codec]

def collect_media_from_folder(input_path, conversion_mode, subfolders=False):
    """Collect media files from folder based on conversion mode"""
    input_path_obj = pathlib.Path(input_path)
    
    if conversion_mode == '1':  # GIF to Video
        extensions = ('.gif',)
    else:  # Video to GIF
        extensions = ('.mp4', '.mkv', '.webm', '.mov', '.avi')
    
    media_files = []
    if input_path_obj.is_dir():
        if subfolders:
            for root, _, files in os.walk(input_path):
                media_files.extend(pathlib.Path(root) / f for f in files if pathlib.Path(f).suffix.lower() in extensions)
        else:
            media_files = [f for f in input_path_obj.glob('*') if f.suffix.lower() in extensions and f.is_file()]
    
    return sorted([str(v) for v in media_files], key=str.lower)

def collect_media_from_paths(file_paths, conversion_mode):
    """Collect media files from space-separated file paths"""
    media_files = []
    paths = file_paths.strip().split()
    
    for path in paths:
        path = clean_path(path)
        path_obj = pathlib.Path(path)
        
        if path_obj.is_file():
            if conversion_mode == '1' and is_valid_gif(path_obj.name):
                media_files.append(str(path_obj))
            elif conversion_mode == '2' and is_valid_video(path_obj.name):
                media_files.append(str(path_obj))
            else:
                print(f"⚠️ Skipping incompatible file: {path}")
        elif path_obj.is_dir():
            print(f"⚠️ Skipping directory in file list: {path}")
    
    return sorted(media_files, key=str.lower)

def get_output_directory(media_files, is_folder_mode=True, first_folder=None, conversion_mode='1'):
    """Determine output directory based on input mode"""
    subfolder_name = "GIF_to_Video" if conversion_mode == '1' else "Video_to_GIF"
    
    if is_folder_mode and first_folder:
        return os.path.join(first_folder, "Output", subfolder_name)
    elif media_files:
        first_media_dir = os.path.dirname(media_files[0])
        return os.path.join(first_media_dir, "Output", subfolder_name)
    else:
        return os.path.join(os.getcwd(), "Output", subfolder_name)

def convert_gif_to_video(gif_path, output_path, codec_settings):
    """Convert GIF to video - simple method"""
    base_name = os.path.splitext(os.path.basename(gif_path))[0]
    output_file = os.path.join(output_path, f"{base_name}.{codec_settings['ext']}")
    
    cmd = [
        "ffmpeg", "-y",
        "-i", gif_path,
        "-c:v", codec_settings['codec'],
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output_file
    ]
    
    return cmd, output_file

def convert_video_to_gif(video_path, output_path, gif_settings):
    """Convert video to GIF - simple direct method"""
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    output_file = os.path.join(output_path, f"{base_name}.gif")
    
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", f"fps={gif_settings['fps']},scale={gif_settings['scale']}",
        output_file
    ]
    
    return cmd, output_file

def process_conversions(media_files, output_dir, conversion_mode, settings):
    """Process all conversions"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Setup logging
    logger = djj.setup_logging(output_dir, "gif_video_converter")
    
    conversion_type = "GIF to Video" if conversion_mode == '1' else "Video to GIF"
    print(f"📄 Found {len(media_files)} file(s). Starting {conversion_type} conversion...")
    
    success_count = 0
    error_count = 0
    
    for i, media_file in enumerate(media_files, 1):
        print(f"\n🔄 Processing {i}/{len(media_files)}: {os.path.basename(media_file)}")
        
        try:
            if conversion_mode == '1':  # GIF to Video
                cmd, output_file = convert_gif_to_video(media_file, output_dir, settings)
            else:  # Video to GIF
                cmd, output_file = convert_video_to_gif(media_file, output_dir, settings)
            
            # Run conversion
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            # Check if output file was created and has content
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                print(f"✅ Converted to: {os.path.basename(output_file)}")
                logger.info(f"{conversion_type}: {media_file} -> {output_file}")
                success_count += 1
            else:
                print(f"❌ Output file is empty or missing: {os.path.basename(output_file)}")
                logger.error(f"Empty output file: {output_file}")
                error_count += 1
                
        except subprocess.CalledProcessError as e:
            error_msg = f"FFmpeg error for {os.path.basename(media_file)}: {e.stderr if e.stderr else 'Unknown error'}"
            print(f"❌ {error_msg}")
            logger.error(error_msg)
            error_count += 1
        except Exception as e:
            error_msg = f"Unexpected error for {os.path.basename(media_file)}: {str(e)}"
            print(f"❌ {error_msg}")
            logger.error(error_msg)
            error_count += 1
    
    return success_count, error_count, output_dir

def main():
    while True:
        print()
        print()
        print("\033[92m==================================================\033[0m")
        print("\033[1;33mGIF ⇔ Video Converter\033[0m")
        print("Convert between GIF and Video formats")
        print("\033[92m==================================================\033[0m")
        print()
        
        # Get conversion mode
        conversion_mode = get_conversion_mode()
        print()
        
        # Get input mode
        input_mode = djj.prompt_choice(
            "Input mode:\n1. Folder path\n2. Space-separated file paths\n",
            ['1', '2'],
            default='1'
        )
        print()
        
        media_files = []
        output_dir = None
        
        if input_mode == '1':
            # Folder mode
            src_dir = input("📁 \033[33mEnter folder path: \n -> \033[0m").strip()
            src_dir = clean_path(src_dir)
            
            if not os.path.isdir(src_dir):
                print(f"❌ \033[33mThe path\033[0m '{src_dir}' \033[33mis not a valid directory\033[0m.")
                continue
            
            print()
            include_sub = djj.prompt_choice(
                "\033[33mInclude subfolders? \033[0m\n1. Yes, 2. No ",
                ['1', '2'],
                default='2'
            ) == '1'
            print()
            
            media_files = collect_media_from_folder(src_dir, conversion_mode, include_sub)
            output_dir = get_output_directory(media_files, is_folder_mode=True, first_folder=src_dir, conversion_mode=conversion_mode)
            
        else:
            # File paths mode
            file_type = "GIF files" if conversion_mode == '1' else "Video files"
            file_paths = input(f"📁 \033[33mEnter {file_type} paths (max ~10 files recommended): \n -> \033[0m").strip()
            
            if not file_paths:
                print("❌ No file paths provided.")
                continue
            
            media_files = collect_media_from_paths(file_paths, conversion_mode)
            output_dir = get_output_directory(media_files, is_folder_mode=False, conversion_mode=conversion_mode)
            print()
        
        if not media_files:
            file_type = "GIF" if conversion_mode == '1' else "video"
            print(f"❌ \033[33mNo valid {file_type} files found.\033[0m")
            continue
        
        # Get conversion settings
        print()
        if conversion_mode == '1':  # GIF to Video
            settings = get_video_codec()
        else:  # Video to GIF
            settings = get_gif_quality()
        print()
        
        success_count, error_count, final_output_dir = process_conversions(media_files, output_dir, conversion_mode, settings)
        
        conversion_type = "GIF to Video" if conversion_mode == '1' else "Video to GIF"
        print(f"\033[33m\n🏁 Done!\033[0m {success_count} \033[33mfile(s) converted ({conversion_type}), \033[0m{error_count} \033[33merror(s).\033[0m")
        print(f"📁\033[33m Output folder:\033[0m {final_output_dir}")
        
        djj.prompt_open_folder(final_output_dir)
        
        action = djj.what_next()
        if action == 'exit':
            break

if __name__ == "__main__":
    main()