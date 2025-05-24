import os
import sys
from PIL import Image
import argparse

def compress_and_resize_image(image_path, max_size=720, quality=85):
    """
    Compress and resize an image, maintaining aspect ratio so the longest side equals max_size.
    Only compresses images with dimensions greater than max_size.
    
    Args:
        image_path: Path to the image file
        max_size: Maximum dimension (width or height) in pixels
        quality: JPEG compression quality (0-100)
    """
    try:
        # Print file information for debugging
        print(f"Attempting to process: {image_path}")
        
        # Check if file is readable
        if not os.access(image_path, os.R_OK):
            print(f"Error: Cannot read file {image_path} - Check permissions")
            return 'error'
            
        # Open the image
        img = Image.open(image_path)
        
        # Get the original format
        original_format = img.format
        print(f"Image format: {original_format}")
        
        # Get current dimensions
        width, height = img.size
        
        # Check if dimensions exceed max_size
        if width <= max_size and height <= max_size:
            print(f"Skipped: {image_path} (dimensions {width}x{height} do not exceed {max_size}px)")
            return 'skipped'
            
        # Calculate new dimensions, maintaining aspect ratio
        if width > height:
            new_width = max_size
            new_height = int(height * max_size / width)
        else:
            new_height = max_size
            new_width = int(width * max_size / height)
        
        # Resize image
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Save the image with compression, overwriting the original
        if original_format == 'JPEG' or original_format == 'JPG':
            img.save(image_path, 'JPEG', quality=quality, optimize=True)
        elif original_format == 'PNG':
            img.save(image_path, 'PNG', optimize=True)
        else:
            # Convert to JPEG if format not supported
            img = img.convert('RGB')
            image_path = os.path.splitext(image_path)[0] + '.jpg'
            img.save(image_path, 'JPEG', quality=quality, optimize=True)
        
        print(f"Successfully compressed: {image_path} from {width}x{height} to {new_width}x{new_height}")
        return 'compressed'
        
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return 'error'

def process_directory_recursive(directory_path, max_size=720, quality=85):
    """
    Process all images in a directory and its subdirectories recursively.
    Only compresses images with dimensions greater than max_size.
    
    Args:
        directory_path: Path to directory containing images
        max_size: Maximum dimension for resizing
        quality: JPEG compression quality
    """
    # Check if directory exists
    if not os.path.isdir(directory_path):
        print(f"Error: Directory '{directory_path}' not found.")
        return

    # Supported image formats - added more formats including avif
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.avif', '.heic']
    
    # Count for statistics
    total_images = 0
    processed_images = 0
    skipped_images = 0
    failed_images = 0
    
    print(f"\nStarting image compression in: {directory_path} and all subdirectories")
    print(f"Only compressing images with dimensions greater than {max_size}px\n")
    print(f"Looking for image files with extensions: {', '.join(image_extensions)}")
    
    # Walk through directory and subdirectories
    for root, dirs, files in os.walk(directory_path):
        # Print current directory being processed for debugging
        print(f"Scanning directory: {root}")
        
        # Process each file in the current directory
        for filename in files:
            file_path = os.path.join(root, filename)
            file_ext = os.path.splitext(filename.lower())[1]
            
            # Check if it's a file and has an image extension
            if os.path.isfile(file_path) and file_ext in image_extensions:
                print(f"Found image: {file_path}")
                total_images += 1
                try:
                    result = compress_and_resize_image(file_path, max_size, quality)
                    
                    if result == 'compressed':
                        processed_images += 1
                    elif result == 'skipped':
                        skipped_images += 1
                    else:
                        failed_images += 1
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
                    failed_images += 1
    
    # Print summary
    print(f"\nProcessing complete!")
    print(f"Total images found: {total_images}")
    print(f"Successfully compressed: {processed_images}")
    print(f"Skipped (under {max_size}px): {skipped_images}")
    print(f"Failed: {failed_images}")

def main():
    try:
        parser = argparse.ArgumentParser(description='Compress and resize images in a directory and subdirectories to specified max dimension.')
        parser.add_argument('--quality', type=int, default=85, help='JPEG compression quality (0-100, default: 85)')
        parser.add_argument('--size', type=int, default=720, help='Maximum dimension in pixels (default: 720)')
        parser.add_argument('--path', type=str, help='Path to the folder containing images (optional)')
        
        args = parser.parse_args()
        
        # Either use command line argument or ask for directory input at runtime
        directory = args.path
        if not directory:
            directory = input("Enter the path to the folder containing images: ")
        
        # Validate directory exists
        if not os.path.isdir(directory):
            print(f"Error: Directory '{directory}' not found.")
            sys.exit(1)
            
        # Print additional debugging info
        print(f"Processing directory: {directory}")
        print(f"Directory exists: {os.path.exists(directory)}")
        print(f"Is directory: {os.path.isdir(directory)}")
        print(f"Directory contents: {os.listdir(directory)}")
            
        process_directory_recursive(directory, args.size, args.quality)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"An error occurred: {e}")
        # Print full traceback for debugging
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
