import os
import sys
from PIL import Image
import argparse

def get_file_size(filepath):
    """Get file size in bytes"""
    return os.path.getsize(filepath)

def compress_and_resize_image(image_path, max_size=720, quality=85, max_file_size_kb=200, target_size_kb=None, remove_exif=True):
    """
    Compress and resize an image with maximum optimization.
    Maintains original filename and format.
    
    Args:
        image_path: Path to the image file
        max_size: Maximum dimension (width or height) in pixels
        quality: JPEG/WebP compression quality (0-100)
        max_file_size_kb: Maximum file size in KB (will compress if exceeds this)
        target_size_kb: Target file size in KB (will aggressively compress to reach this)
        remove_exif: Remove EXIF metadata to reduce file size
    """
    try:
        # Get original file size
        original_size = get_file_size(image_path)
        original_size_kb = original_size / 1024
        
        print(f"\nProcessing: {image_path}")
        print(f"Original size: {original_size_kb:.2f} KB")
        
        # Check if file is readable
        if not os.access(image_path, os.R_OK):
            print(f"Error: Cannot read file {image_path} - Check permissions")
            return 'error', 0
            
        # Open the image
        img = Image.open(image_path)
        original_format = img.format
        
        # Get current dimensions
        width, height = img.size
        print(f"Dimensions: {width}x{height}")
        
        # Determine if we need to process this image
        needs_resize = width > max_size or height > max_size
        needs_compression = original_size_kb > max_file_size_kb
        
        # If target size is specified, always process if current size exceeds target
        if target_size_kb and original_size_kb > target_size_kb:
            needs_compression = True
            print(f"Target size: {target_size_kb}KB (will compress aggressively)")
        
        if not needs_resize and not needs_compression:
            print(f"Skipped: Dimensions ≤{max_size}px and file size ≤{max_file_size_kb}KB")
            return 'skipped', 0
        
        # Calculate new dimensions if needed
        if needs_resize:
            if width > height:
                new_width = max_size
                new_height = int(height * max_size / width)
            else:
                new_height = max_size
                new_width = int(width * max_size / height)
            
            # Resize with high-quality resampling
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            print(f"Resized from {width}x{height} to {new_width}x{new_height}")
        else:
            print(f"No resize needed (dimensions OK), but will compress due to file size > {max_file_size_kb}KB")
        
        # Convert RGBA to RGB (remove alpha channel) for better compression
        if img.mode in ('RGBA', 'LA', 'P'):
            # Create white background
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
            print("Converted to RGB (removed transparency)")
        elif img.mode != 'RGB' and original_format in ['JPEG', 'JPG']:
            img = img.convert('RGB')
            print(f"Converted {img.mode} to RGB")
        
        # Prepare save parameters based on original format
        save_kwargs = {'optimize': True}
        
        # Determine initial quality for aggressive compression
        current_quality = quality
        if target_size_kb and original_size_kb > target_size_kb:
            # Start with lower quality if we need aggressive compression
            current_quality = min(quality, 75)
            print(f"Using aggressive compression (starting quality: {current_quality})")
        
        # Save with original format and filename
        if original_format in ['JPEG', 'JPG']:
            # For JPEG, we can iteratively compress to target size
            attempt = 0
            max_attempts = 8
            
            while attempt < max_attempts:
                save_kwargs = {
                    'optimize': True,
                    'quality': current_quality,
                    'progressive': True,
                    'subsampling': '4:2:0',
                }
                
                # Remove EXIF data if requested
                if not remove_exif:
                    exif = img.info.get('exif')
                    if exif:
                        save_kwargs['exif'] = exif
                elif attempt == 0:
                    print("Removing EXIF metadata")
                
                img.save(image_path, 'JPEG', **save_kwargs)
                
                # Check if we reached target
                current_size_kb = get_file_size(image_path) / 1024
                
                if target_size_kb is None:
                    # No target, just compress once
                    break
                    
                if current_size_kb <= target_size_kb:
                    print(f"✓ Reached target size after {attempt + 1} attempt(s) with quality {current_quality}")
                    break
                    
                # Not reached target, reduce quality for next attempt
                attempt += 1
                if attempt < max_attempts:
                    # Reduce quality more aggressively as we go
                    quality_reduction = 8 if current_size_kb > target_size_kb * 1.5 else 5
                    current_quality = max(current_quality - quality_reduction, 40)  # Don't go below 40
                    print(f"  Attempt {attempt}: {current_size_kb:.1f}KB > {target_size_kb}KB, reducing quality to {current_quality}")
            
            if attempt >= max_attempts and target_size_kb:
                print(f"⚠ Could not reach target of {target_size_kb}KB (final: {current_size_kb:.1f}KB, quality: {current_quality})")
            
        elif original_format == 'PNG':
            # For PNG with target size, consider converting to JPEG if no transparency
            if target_size_kb and img.mode in ['RGB', 'L']:
                print(f"Note: PNG detected. For aggressive compression (<{target_size_kb}KB), consider JPEG format")
            
            # Save as PNG with max compression
            save_kwargs['compress_level'] = 9
            img.save(image_path, 'PNG', **save_kwargs)
            
        elif original_format == 'WEBP':
            save_kwargs.update({
                'quality': quality,
                'method': 6,  # Maximum compression effort
            })
            img.save(image_path, 'WEBP', **save_kwargs)
            
        else:
            # For other formats, convert to RGB and save in original format if possible
            if img.mode not in ['RGB', 'L']:
                img = img.convert('RGB')
            
            if original_format in ['GIF', 'BMP', 'TIFF']:
                img.save(image_path, original_format, **save_kwargs)
            else:
                # Fallback: save as JPEG with original extension (not ideal but maintains name)
                save_kwargs.update({
                    'quality': quality,
                    'progressive': True,
                })
                img.save(image_path, 'JPEG', **save_kwargs)
        
        # Get new file size and calculate compression
        new_size = get_file_size(image_path)
        new_size_kb = new_size / 1024
        compression_ratio = ((original_size - new_size) / original_size) * 100
        
        print(f"New size: {new_size_kb:.2f} KB")
        print(f"Saved: {(original_size - new_size) / 1024:.2f} KB ({compression_ratio:.1f}% reduction)")
        print(f"Successfully processed: {image_path}")
        
        return 'compressed', compression_ratio
        
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        import traceback
        traceback.print_exc()
        return 'error', 0

def process_directory_recursive(directory_path, max_size=720, quality=85, max_file_size_kb=200, remove_exif=True):
    """
    Process all images in a directory and its subdirectories recursively.
    
    Args:
        directory_path: Path to directory containing images
        max_size: Maximum dimension for resizing
        quality: JPEG/WebP compression quality
        max_file_size_kb: Maximum file size in KB
        remove_exif: Remove EXIF metadata
    """
    # Check if directory exists
    if not os.path.isdir(directory_path):
        print(f"Error: Directory '{directory_path}' not found.")
        return

    # Supported image formats
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.avif', '.heic']
    
    # Statistics
    total_images = 0
    processed_images = 0
    skipped_images = 0
    failed_images = 0
    total_original_size = 0
    total_new_size = 0
    
    print(f"\n{'='*70}")
    print(f"Starting image compression")
    print(f"Directory: {directory_path}")
    print(f"Max dimension: {max_size}px")
    print(f"Max file size: {max_file_size_kb}KB")
    print(f"Quality: {quality}")
    print(f"Remove EXIF: {remove_exif}")
    print(f"Note: Original filenames and formats will be preserved")
    print(f"{'='*70}\n")
    
    # Walk through directory and subdirectories
    for root, dirs, files in os.walk(directory_path):
        for filename in files:
            file_path = os.path.join(root, filename)
            file_ext = os.path.splitext(filename.lower())[1]
            
            # Check if it's an image file
            if os.path.isfile(file_path) and file_ext in image_extensions:
                total_images += 1
                original_size = get_file_size(file_path)
                total_original_size += original_size
                
                try:
                    result, compression = compress_and_resize_image(
                        file_path, max_size, quality, max_file_size_kb, remove_exif
                    )
                    
                    if result == 'compressed':
                        processed_images += 1
                        new_size = get_file_size(file_path)
                        total_new_size += new_size
                    elif result == 'skipped':
                        skipped_images += 1
                        total_new_size += original_size
                    else:
                        failed_images += 1
                        total_new_size += original_size
                        
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
                    failed_images += 1
                    total_new_size += original_size
    
    # Print summary
    print(f"\n{'='*70}")
    print(f"COMPRESSION SUMMARY")
    print(f"{'='*70}")
    print(f"Total images found: {total_images}")
    print(f"Successfully compressed: {processed_images}")
    print(f"Skipped (already optimized): {skipped_images}")
    print(f"Failed: {failed_images}")
    print(f"\nStorage saved:")
    print(f"Original total size: {total_original_size / (1024*1024):.2f} MB")
    print(f"New total size: {total_new_size / (1024*1024):.2f} MB")
    print(f"Total saved: {(total_original_size - total_new_size) / (1024*1024):.2f} MB")
    if total_original_size > 0:
        overall_compression = ((total_original_size - total_new_size) / total_original_size) * 100
        print(f"Overall compression: {overall_compression:.1f}%")
    print(f"{'='*70}\n")

def main():
    try:
        parser = argparse.ArgumentParser(
            description='Compress and resize images while preserving original filenames and formats.',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python script.py --path /path/to/images
  python script.py --path /path/to/images --quality 75 --size 1080 --maxsize 300
  python script.py --path /path/to/images --quality 80 --maxsize 150
  
The script will:
  - Resize images with dimensions > max_size (default 720px)
  - Compress images with file size > max_file_size (default 200KB)
  - Keep original filename and format
  - Remove EXIF metadata by default
            """
        )
        
        parser.add_argument('--quality', type=int, default=85, 
                          help='Compression quality (0-100, default: 85, lower = smaller file)')
        parser.add_argument('--size', type=int, default=720, 
                          help='Maximum dimension in pixels (default: 720)')
        parser.add_argument('--maxsize', type=int, default=200,
                          help='Maximum file size in KB (default: 200, will compress if exceeds)')
        parser.add_argument('--path', type=str, 
                          help='Path to the folder containing images')
        parser.add_argument('--keep-exif', dest='remove_exif', action='store_false',
                          help='Keep EXIF metadata (default: remove to save space)')
        
        args = parser.parse_args()
        
        # Get directory path
        directory = args.path
        if not directory:
            directory = input("Enter the path to the folder containing images: ")
        
        # Validate directory
        if not os.path.isdir(directory):
            print(f"Error: Directory '{directory}' not found.")
            sys.exit(1)
            
        # Process images
        process_directory_recursive(
            directory, 
            args.size, 
            args.quality,
            args.maxsize,
            args.remove_exif
        )
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()